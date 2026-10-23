import copy
import json

import httpx
import pytest
from test_requirement_collaboration import live_env, ready, source, start, task
from test_workflow import approve, command, to_trade

from app.domain.decomposition import validate_plan
from app.domain.models import Model, Proposal
from app.domain.protocol import validate
from app.services.requirement_checks import evaluate


def pending(client, model=None):
    m, ident = start(client, model, study="decomposition")
    m = ready(client, m, ident)
    m = task(client, m, ident, "submit")
    p = next(p for p in m["proposals"].values() if p["status"] == "submitted")
    return m, ident, p


def test_children_added_only_on_approval_parent_unchanged_and_checks_partial(client):
    initial = to_trade(client)
    original = initial["entities"]["req-latency"]
    m, ident, p = pending(client, initial)
    assert m["entities"]["req-latency"] == original
    assert all(op["entity"]["id"] not in m["entities"] for op in p["operations"])
    m = approve(client, m)
    assert m["phase"] == "Recalculation required"
    assert m["entities"]["req-latency"] == original
    children = [m["entities"][op["entity"]["id"]] for op in p["operations"]]
    assert len(children) == 2
    assert all(c["data"]["priority"] == original["data"]["priority"] for c in children)
    assert all(c["data"]["formalization"]["coverage"] == "partial" for c in children)
    assert all(dict(type="derives_from", target="req-latency") in c["relations"] for c in children)
    m = command(client, m, "advance")
    typed = Model.model_validate(m)
    for child in children:
        assert evaluate(typed, typed.entities[child["id"]], "selective").data["status"] != "pass"
    assert (
        client.post(
            f"/api/missions/{m['id']}/requirement-collaboration",
            json=dict(revision=m["revision"], requirement_id="req-latency", study="decomposition"),
        ).status_code
        == 409
    )


def test_reject_and_challenge_do_not_create_children(client):
    m, ident, p = pending(client)
    m = command(
        client,
        m,
        "proposals/" + p["id"] + "/decision",
        action="challenge",
        reason="Scope remains incomplete",
    )
    assert all(op["entity"]["id"] not in m["entities"] for op in p["operations"])
    m = command(
        client,
        m,
        "proposals/" + p["id"] + "/decision",
        action="reject",
        reason="Revise separate obligations",
    )
    assert all(op["entity"]["id"] not in m["entities"] for op in p["operations"])


@pytest.mark.parametrize("tamper", ["title", "priority", "criterion", "parent", "count", "type"])
def test_acceptance_revalidates_reviewed_children(client, tamper):
    m, ident, raw = pending(client)
    p = Proposal.model_validate(raw)
    p.target_revision = m["revision"]
    e = p.operations[0].entity
    if tamper == "title":
        e.title = "Invented target of 10 metres"
    if tamper == "priority":
        e.data["priority"] = "Could"
    if tamper == "criterion":
        e.data["criterion"] = dict(
            metric="mass.total", operator="<=", threshold=dict(value=10, unit="kg")
        )
    if tamper == "parent":
        e.relations[0].target = "req-cost"
    if tamper == "count":
        p.operations.pop()
    if tamper == "type":
        p.proposal_type = "design change"
    with pytest.raises(ValueError):
        validate(Model.model_validate(m), p)


def test_fabricated_quote_unknown_criterion_duplicate_children_rejected(client):
    m, ident = start(client, study="decomposition")
    m = ready(client, m, ident)
    d = m["entities"][ident]["data"]
    for mutation in ["quote", "criterion", "duplicate"]:
        raw = copy.deepcopy(d["proposal"])
        if mutation == "quote":
            raw["children"][0]["source_quote"] = "Invented 10 m resolution"
        if mutation == "criterion":
            raw["children"][0]["criterion_id"] = "invented"
        if mutation == "duplicate":
            raw["children"][1] = raw["children"][0]
        with pytest.raises(ValueError):
            validate_plan(d, raw)


def test_live_decomposition_uses_owner_quotes_and_separate_review(client, monkeypatch):
    initial = source(client)
    live_env(monkeypatch)
    real = httpx.Client
    contexts = []
    outputs = [
        dict(summary="Clarify image quality", questions=["What quality obligation applies?"]),
        dict(
            basis="Separate time from owner-stated quality obligation",
            children=[
                dict(
                    source_ref="parent",
                    source_quote="within 30 minutes of acquisition",
                    criterion_id="literal-deadline",
                    rationale="Explicit parent deadline",
                    unresolved=["Operating conditions still need review"],
                ),
                dict(
                    source_ref="answer-0",
                    source_quote="Image quality is outside this latency check",
                    criterion_id=None,
                    rationale="Owner states quality is separate",
                    unresolved=["No measurable quality target provided"],
                ),
            ],
            limitations=["Parent completeness not established"],
        ),
        dict(
            recommendation="submit",
            rationale="Source-bound partial decomposition for owner review",
            findings=["Quality remains unresolved"],
            questions=[],
        ),
    ]

    def respond(request):
        body = json.loads(request.content)
        contexts.append(json.loads(body["messages"][1]["content"]))
        return httpx.Response(
            200,
            json=dict(
                choices=[dict(message=dict(content=json.dumps(outputs[len(contexts) - 1])))],
                usage=dict(total_tokens=100),
            ),
        )

    monkeypatch.setattr(
        "app.agents.design_provider.httpx.Client",
        lambda **kw: real(transport=httpx.MockTransport(respond), **kw),
    )
    m, ident = start(client, initial, study="decomposition", mode="live")
    m = ready(client, m, ident)
    assert len(contexts) == 3 and len(contexts[2]["proposal"]["children"]) == 2
    assert contexts[1]["sources"]["answer-0"] == "Image quality is outside this latency check"
    m = task(client, m, ident, "submit")
    assert (
        sum(a["accounted_tokens"] for a in m["entities"][ident]["data"]["budget"]["attempts"])
        == 300
    )


def test_decomposition_automatic_progression_and_simulation_scope(client):
    m, ident = start(client, study="decomposition")
    for phase in range(2):
        r = client.post(
            f"/api/missions/{m['id']}/requirement-collaboration/{ident}/run",
            json=dict(revision=m["revision"]),
        )
        assert r.status_code == 202, r.text
        m = client.app.state.store.get(m["id"]).model_dump(mode="json")
        if phase == 0:
            m = task(
                client, m, ident, "answers", answers=["Quality and workload remain unresolved"]
            )
    assert m["entities"][ident]["data"]["status"] == "review_ready"
    assert not any(p["status"] == "submitted" for p in m["proposals"].values())
    m = task(client, m, ident, "cancel")
    r = client.post(
        f"/api/missions/{m['id']}/requirement-collaboration",
        json=dict(revision=m["revision"], requirement_id="req-cost", study="decomposition"),
    )
    assert r.status_code == 409 and "Simulation decomposition" in r.text


def test_parent_change_and_missing_review_block_acceptance(client):
    m, ident, raw = pending(client)
    p = Proposal.model_validate(raw)
    p.target_revision = m["revision"]
    changed = Model.model_validate(m)
    changed.entities["req-latency"].title += " revised scope"
    with pytest.raises(ValueError, match="Parent changed"):
        validate(changed, p)
    changed = Model.model_validate(m)
    changed.entities[ident].data["review"]["recommendation"] = "clarify"
    with pytest.raises(ValueError, match="independent review"):
        validate(changed, p)


def test_historical_revision_preserves_parent_and_excludes_later_children(client):
    m, ident, p = pending(client)
    revision = m["revision"]
    m = approve(client, m)
    prior = client.get(f"/api/missions/{m['id']}/revisions/{revision}").json()
    assert all(op["entity"]["id"] not in prior["entities"] for op in p["operations"])
    assert prior["entities"]["req-latency"] == m["entities"]["req-latency"]
