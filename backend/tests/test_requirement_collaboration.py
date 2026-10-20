import json

import httpx
import pytest
from test_workflow import approve, command, create

from app.agents.requirement_provider import CriterionChoice, IndependentReview, perform
from app.services.requirement_collaboration import WORKFLOW


def source(client):
    m = approve(client, create(client))
    return approve(client, command(client, m, "advance"))


def start(client, m=None, **kwargs):
    m = command(
        client,
        m or source(client),
        "requirement-collaboration",
        requirement_id="req-latency",
        **kwargs,
    )
    ident = next(e["id"] for e in m["entities"].values() if e["data"].get("workflow") == WORKFLOW)
    return m, ident


def task(client, m, ident, action="step", **kwargs):
    return command(client, m, f"requirement-collaboration/{ident}/{action}", **kwargs)


def ready(client, m, ident):
    m = task(client, m, ident)
    assert m["entities"][ident]["data"]["status"] == "awaiting_answers"
    m = task(
        client,
        m,
        ident,
        "answers",
        answers=["Image quality is outside this latency check"]
        * len(m["entities"][ident]["data"]["pending_questions"]),
    )
    m = task(client, m, ident)
    return task(client, m, ident)


def test_simulation_review_submission_and_approval(client):
    m, ident = start(client)
    original = m["entities"]["req-latency"]
    m = ready(client, m, ident)
    assert m["entities"][ident]["data"]["status"] == "review_ready"
    assert m["entities"]["req-latency"] == original
    assert not any(p["status"] == "submitted" for p in m["proposals"].values())
    m = task(client, m, ident, "submit")
    assert m["entities"]["req-latency"] == original
    proposal = next(p for p in m["proposals"].values() if p["status"] == "submitted")
    assert ident in proposal["evidence_references"]
    m = approve(client, m)
    scope = m["entities"]["req-latency"]["data"]["formalization"]
    assert scope["coverage"] == "partial"
    assert scope["criterion"]["threshold"] == {"value": 30, "unit": "minute"}
    run = m["entities"][ident]["data"]
    assert [a["agent"] for a in run["budget"]["attempts"]] == ["mission", "formalize", "review"]
    assert all(a["accounted_tokens"] == 0 for a in run["budget"]["attempts"])
    assert [e["sequence"] for e in run["events"]] == list(range(1, len(run["events"]) + 1))


def test_source_notes_cannot_be_skipped(client):
    m = source(client)
    m = command(client, m, "requirements/req-latency/clarify", question="Which image quality?")
    m, ident = start(client, m)
    m = ready(client, m, ident)
    m = task(client, m, ident, "submit")
    proposed = next(p for p in m["proposals"].values() if p["status"] == "submitted")
    assert (
        "Which image quality?"
        not in proposed["operations"][0]["entity"]["data"]["formalization"]["open_questions"]
    )


def test_no_criterion_and_round_bounds(client):
    m = source(client)
    m = command(client, m, "requirement-collaboration", requirement_id="req-cost")
    ident = next(e["id"] for e in m["entities"].values() if e["data"].get("workflow") == WORKFLOW)
    m = ready(client, m, ident)
    assert m["entities"][ident]["data"]["status"] == "awaiting_answers"
    for _ in range(2):
        m = task(client, m, ident, "answers", answers=["No supported cost metric available"])
        m = task(client, m, ident)
        m = task(client, m, ident)
    response = client.post(
        f"/api/missions/{m['id']}/requirement-collaboration/{ident}/answers",
        json=dict(revision=m["revision"], answers=["Try once more"]),
    )
    assert response.status_code == 409
    assert m["entities"][ident]["data"]["round"] == 3
    m = task(client, m, ident, "cancel")
    assert m["entities"][ident]["data"]["status"] == "cancelled"


def test_unsourced_criterion_is_failed_and_explicit_retry(client, monkeypatch):
    m, ident = start(client)
    m = task(client, m, ident)
    m = task(client, m, ident, "answers", answers=["Quality needs separate assessment"])
    monkeypatch.setattr(
        "app.services.requirement_collaboration.perform",
        lambda *args: (
            CriterionChoice(
                criterion_id="invented", basis="Invent a threshold", limitations=["Unsupported"]
            ),
            {},
        ),
    )
    m = task(client, m, ident)
    assert m["entities"][ident]["data"]["status"] == "failed"
    monkeypatch.setattr("app.services.requirement_collaboration.perform", perform)
    m = task(client, m, ident, "retry")
    m = task(client, m, ident)
    assert m["entities"][ident]["data"]["status"] == "ready"
    assert len(m["entities"][ident]["data"]["budget"]["attempts"]) == 3


@pytest.mark.parametrize("change", ["cancel", "pause", "requirement"])
def test_late_results_fenced(client, monkeypatch, change):
    m, ident = start(client)
    store = client.app.state.store

    def concurrent(stage, context, mode):
        latest = store.get(m["id"])
        if change == "cancel":
            task(client, latest.model_dump(mode="json"), ident, "cancel")
        elif change == "pause":
            command(client, latest.model_dump(mode="json"), "pause")
        else:
            updated = latest.model_copy(deep=True)
            updated.entities["req-latency"].title += " revised"
            store.save(updated, "human", "Concurrent change", latest)
        return perform(stage, context, mode)

    monkeypatch.setattr("app.services.requirement_collaboration.perform", concurrent)
    m = task(client, m, ident)
    assert "mission" not in m["entities"][ident]["data"]
    assert m["entities"][ident]["data"]["status"] == (
        "cancelled" if change == "cancel" else "working"
    )


def live_env(monkeypatch):
    for k, v in dict(
        LLM_PROVIDER="openai-compatible",
        LLM_MODEL="test",
        LLM_BASE_URL="https://example.invalid/v1",
        LLM_API_KEY="test-only",
        LLM_MAX_PRICE_PER_MILLION="1",
        MAX_RUN_COST_EUR="1",
    ).items():
        monkeypatch.setenv(k, v)


def test_three_separate_live_calls_with_source_context(client, monkeypatch):
    initial = source(client)
    live_env(monkeypatch)
    real_client = httpx.Client
    received = []
    outputs = [
        dict(summary="Clarify applicability", questions=["What quality applies?"]),
        dict(
            criterion_id="literal-deadline",
            basis="Requirement explicitly states 30 minutes; quality is outside scope",
            limitations=["Image quality remains outside this check"],
        ),
        dict(
            recommendation="submit",
            rationale="Sourced deadline is suitable for partial human review",
            findings=["Quality remains unverified"],
            questions=[],
        ),
    ]

    def respond(request):
        body = json.loads(request.content)
        context = json.loads(body["messages"][1]["content"])
        received.append((body["messages"][0]["content"], context))
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": json.dumps(outputs[len(received) - 1])}}],
                "usage": {"total_tokens": 100},
            },
        )

    monkeypatch.setattr(
        "app.agents.design_provider.httpx.Client",
        lambda **kw: real_client(transport=httpx.MockTransport(respond), **kw),
    )
    m, ident = start(client, initial, mode="live")
    m = ready(client, m, ident)
    assert len(received) == 3
    assert "Mission clarification agent" in received[0][0]
    assert "Systems formalization agent" in received[1][0]
    assert "independent requirement reviewer" in received[2][0]
    assert received[1][1]["answers"][0]["answer"] == "Image quality is outside this latency check"
    assert received[2][1]["proposal"]["criterion_id"] == "literal-deadline"
    assert m["entities"][ident]["data"]["status"] == "review_ready"
    assert (
        sum(a["accounted_tokens"] for a in m["entities"][ident]["data"]["budget"]["attempts"])
        == 300
    )


def test_budget_prevents_call_and_unknown_retry_keeps_reservation(client, monkeypatch):
    initial = source(client)
    live_env(monkeypatch)
    m, ident = start(
        client, initial, mode="live", limits=dict(tokens=1, cost_eur=1, elapsed_seconds=3600)
    )
    r = client.post(
        f"/api/missions/{m['id']}/requirement-collaboration/{ident}/step",
        json=dict(revision=m["revision"]),
    )
    assert r.status_code == 409 and "Token budget" in r.text
    m = task(client, m, ident, "cancel")
    m = command(client, m, "requirement-collaboration", requirement_id="req-latency", mode="live")
    ident = next(
        e["id"]
        for e in m["entities"].values()
        if e["data"].get("workflow") == WORKFLOW and e["data"]["status"] == "ready"
    )

    def fail(*args):
        raise ValueError("private provider error")

    monkeypatch.setattr("app.services.requirement_collaboration.perform", fail)
    m = task(client, m, ident)
    assert m["entities"][ident]["data"]["status"] == "failed"
    assert "private provider error" not in json.dumps(m)
    r = client.post(
        f"/api/missions/{m['id']}/requirement-collaboration/{ident}/retry",
        json=dict(revision=m["revision"]),
    )
    assert r.status_code == 409
    m = task(client, m, ident, "retry", acknowledge_unknown=True)
    assert m["entities"][ident]["data"]["budget"]["attempts"][0]["accounted_tokens"] == 29120


def test_independent_review_blocks_submission(client, monkeypatch):
    m, ident = start(client)
    m = task(client, m, ident)
    m = task(client, m, ident, "answers", answers=["Quality is unresolved"])
    m = task(client, m, ident)
    monkeypatch.setattr(
        "app.services.requirement_collaboration.perform",
        lambda *args: (
            IndependentReview(
                recommendation="revise",
                rationale="Applicability is missing",
                findings=["Workload not defined"],
                questions=["Which workload?"],
            ),
            {},
        ),
    )
    m = task(client, m, ident)
    r = client.post(
        f"/api/missions/{m['id']}/requirement-collaboration/{ident}/submit",
        json=dict(revision=m["revision"]),
    )
    assert r.status_code == 409
    assert m["entities"][ident]["data"]["pending_questions"] == ["Which workload?"]


def test_expired_checkpoint_recovery_preserves_reservation(client, monkeypatch):
    initial = source(client)
    live_env(monkeypatch)
    m, ident = start(client, initial, mode="live")
    store = client.app.state.store
    old = store.get(m["id"])
    updated = old.model_copy(deep=True)
    d = updated.entities[ident].data
    d.update(
        status="working", attempt="old-call", task_lease="2000-01-01T00:00:00+00:00", attempts=1
    )
    from app.services.run_budget import reserve

    reserve(d, "old-call")
    m = store.save(updated, "orchestrator", "Interrupted test checkpoint", old).model_dump(
        mode="json"
    )
    m = task(client, m, ident, "retry", acknowledge_unknown=True)
    d = m["entities"][ident]["data"]
    assert d["status"] == "ready" and d["attempt"] is None
    assert d["budget"]["attempts"][0]["accounted_tokens"] == 29120
    assert d["budget"]["attempts"][0]["status"] == "unknown"


def test_source_note_replies_and_new_note_detection(client):
    m = source(client)
    m = command(client, m, "requirements/req-latency/clarify", question="Which workload?")
    note = next(
        e
        for e in m["entities"].values()
        if e["data"].get("workflow") == "requirement-formalization"
    )
    m = command(
        client,
        m,
        "requirements/req-latency/clarify",
        question="Which workload?",
        answer="Reference workload only",
        reply_to=note["id"],
    )
    m, ident = start(client, m)
    m = ready(client, m, ident)
    m = command(client, m, "requirements/req-latency/clarify", question="New obligation?")
    r = client.post(
        f"/api/missions/{m['id']}/requirement-collaboration/{ident}/submit",
        json=dict(revision=m["revision"]),
    )
    assert r.status_code == 409 and "history changed" in r.text


def test_owner_criterion_is_explicit_and_model_cannot_replace_it(client):
    m = source(client)
    m = command(client, m, "requirement-collaboration", requirement_id="req-launch")
    ident = next(e["id"] for e in m["entities"].values() if e["data"].get("workflow") == WORKFLOW)
    m = task(client, m, ident)
    rule = dict(metric="mass.total", operator="<=", threshold=dict(value=20, unit="kg"))
    m = task(
        client,
        m,
        ident,
        "answers",
        answers=["Mass is a partial constraint; geometric envelope remains unresolved"],
        criterion=rule,
    )
    m = task(client, m, ident)
    m = task(client, m, ident)
    m = task(client, m, ident, "submit")
    proposal = next(p for p in m["proposals"].values() if p["status"] == "submitted")
    assert proposal["operations"][0]["entity"]["data"]["criterion"] == rule
    assert proposal["operations"][0]["entity"]["data"]["formalization"]["coverage"] == "partial"


def test_existing_scope_questions_pause_even_if_agent_omits_them(client, monkeypatch):
    from app.agents.requirement_provider import MissionQuestions

    m = source(client)
    m = command(
        client,
        m,
        "requirements/req-latency/formalize",
        criterion=None,
        coverage="partial",
        basis="Need explicit applicability",
        open_questions=["Which processing delay applies?"],
    )
    m = approve(client, m)
    m, ident = start(client, m)
    monkeypatch.setattr(
        "app.services.requirement_collaboration.perform",
        lambda *args: (MissionQuestions(summary="No additional questions", questions=[]), {}),
    )
    m = task(client, m, ident)
    assert m["entities"][ident]["data"]["status"] == "awaiting_answers"
    assert m["entities"][ident]["data"]["pending_questions"] == ["Which processing delay applies?"]
