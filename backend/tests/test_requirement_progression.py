import pytest
from test_requirement_collaboration import start, task
from test_workflow import command

from app.agents.requirement_provider import MissionQuestions, perform
from app.services.requirement_collaboration import RequirementCollaboration, Retry


def claim(client, model, ident):
    service = RequirementCollaboration(client.app.state.store)
    saved = service.begin_execution(model["id"], ident, model["revision"])
    return service, saved, saved.entities[ident].data["execution"]["id"]


def current(client, model):
    return client.app.state.store.get(model["id"]).model_dump(mode="json")


def test_run_stops_at_questions_then_review_without_submission(client):
    m, ident = start(client)
    original = m["entities"]["req-latency"]
    r = client.post(
        f"/api/missions/{m['id']}/requirement-collaboration/{ident}/run",
        json={"revision": m["revision"]},
    )
    assert r.status_code == 202, r.text
    m = current(client, m)
    d = m["entities"][ident]["data"]
    assert d["status"] == "awaiting_answers" and d["attempts"] == 1
    assert d["execution"]["status"] == "stopped"
    m = task(client, m, ident, "answers", answers=["Quality remains outside this deadline"])
    service, saved, execution = claim(client, m, ident)
    service.execute_remaining(m["id"], ident, execution)
    m = current(client, m)
    d = m["entities"][ident]["data"]
    assert d["status"] == "review_ready" and d["attempts"] == 3
    assert m["entities"]["req-latency"] == original
    assert not any(p["status"] == "submitted" for p in m["proposals"].values())
    assert [a["agent"] for a in d["budget"]["attempts"]] == ["mission", "formalize", "review"]
    m = task(client, m, ident, "submit")
    assert m["entities"][ident]["data"]["status"] == "submitted"


def test_claim_excludes_duplicate_run_and_manual_task(client):
    m, ident = start(client)
    service, saved, execution = claim(client, m, ident)
    for method in [service.begin_execution, service.step]:
        with pytest.raises(ValueError, match="owns this run"):
            method(m["id"], ident, saved.revision)
    assert len(saved.entities[ident].data["budget"]["attempts"]) == 0
    service.execute_remaining(m["id"], ident, "wrong-id")
    assert current(client, m)["revision"] == saved.revision


@pytest.mark.parametrize("action", ["pause_resume", "cancel", "edit"])
def test_inflight_changes_fence_worker_and_next_task(client, monkeypatch, action):
    m, ident = start(client)
    service, saved, execution = claim(client, m, ident)
    calls = []

    def interrupted(stage, context, mode):
        calls.append(stage)
        latest = current(client, m)
        if action == "pause_resume":
            latest = command(client, latest, "pause")
            command(client, latest, "pause")
        elif action == "cancel":
            task(client, latest, ident, "cancel")
        else:
            store = client.app.state.store
            old = store.get(m["id"])
            updated = old.model_copy(deep=True)
            updated.entities["req-latency"].title += " revised"
            store.save(updated, "human", "Concurrent source edit", old)
        return MissionQuestions(summary="Ready to proceed", questions=[]), {}

    monkeypatch.setattr("app.services.requirement_collaboration.perform", interrupted)
    service.execute_remaining(m["id"], ident, execution)
    d = current(client, m)["entities"][ident]["data"]
    assert calls == ["mission"]
    assert "mission" not in d
    assert d["execution"]["status"] == "stopped"
    assert d["status"] == ("cancelled" if action == "cancel" else "working")


@pytest.mark.parametrize("status", ["ready", "awaiting_answers", "review_ready"])
def test_expired_idle_claim_recovery_keeps_checkpoint_without_call_ack(client, status):
    m, ident = start(client)
    service, saved, execution = claim(client, m, ident)
    store = client.app.state.store
    updated = saved.model_copy(deep=True)
    d = updated.entities[ident].data
    d["execution"]["lease_expires_at"] = "2000-01-01T00:00:00+00:00"
    d.update(status=status, mode="live")
    saved = store.save(updated, "orchestrator", "Simulated interrupted checkpoint", saved)
    recovered = service.retry(m["id"], ident, Retry(revision=saved.revision))
    assert recovered.entities[ident].data["status"] == status
    assert recovered.entities[ident].data["execution"]["status"] == "stopped"
    service.execute_remaining(m["id"], ident, execution)
    assert current(client, m)["revision"] == recovered.revision
    assert not recovered.entities[ident].data["budget"]["attempts"]


def test_three_tasks_bound_and_failure_never_retries(client, monkeypatch):
    m, ident = start(client)
    service, saved, execution = claim(client, m, ident)
    calls = []

    def provider(stage, context, mode):
        calls.append(stage)
        if stage == "mission":
            return MissionQuestions(summary="No further questions", questions=[]), {}
        return perform(stage, context, mode)

    monkeypatch.setattr("app.services.requirement_collaboration.perform", provider)
    service.execute_remaining(m["id"], ident, execution)
    assert calls == ["mission", "formalize", "review"]
    assert current(client, m)["entities"][ident]["data"]["status"] == "review_ready"


def test_failure_stops_and_budget_preflight_does_not_claim(client, monkeypatch):
    m, ident = start(client)
    service, saved, execution = claim(client, m, ident)

    def fail(*args):
        raise ValueError("provider failed")

    monkeypatch.setattr("app.services.requirement_collaboration.perform", fail)
    service.execute_remaining(m["id"], ident, execution)
    d = current(client, m)["entities"][ident]["data"]
    assert d["status"] == "failed" and d["attempts"] == 1
    assert d["execution"]["status"] == "stopped"
    store = client.app.state.store
    old = store.get(m["id"])
    updated = old.model_copy(deep=True)
    updated.entities[ident].data.update(status="ready")
    updated.entities[ident].data["budget"]["deadline"] = "2000-01-01T00:00:00+00:00"
    saved = store.save(updated, "human", "Exhausted elapsed budget", old)
    with pytest.raises(ValueError, match="Elapsed-time budget"):
        service.begin_execution(m["id"], ident, saved.revision)
    assert current(client, m)["revision"] == saved.revision


def test_pending_proposal_during_call_stays_approvable(client, monkeypatch):
    from test_workflow import approve

    from app.services.formalization import Formalizer, Submit

    m, ident = start(client)
    service, saved, execution = claim(client, m, ident)
    store = client.app.state.store

    def concurrent(stage, context, mode):
        latest = store.get(m["id"])
        Formalizer(store).propose(
            m["id"],
            "req-launch",
            Submit(revision=latest.revision, criterion=None, basis="Geometry remains unresolved"),
        )
        return MissionQuestions(summary="No new questions", questions=[]), {}

    monkeypatch.setattr("app.services.requirement_collaboration.perform", concurrent)
    service.execute_remaining(m["id"], ident, execution)
    latest = current(client, m)
    assert latest["entities"][ident]["data"]["execution"]["status"] == "stopped"
    assert "mission" not in latest["entities"][ident]["data"]
    approved = approve(client, latest)
    assert approved["entities"]["req-launch"]["data"]["formalization"]["coverage"] == "partial"


def test_expired_working_execution_requires_unknown_charge_ack(client):
    m, ident = start(client)
    service, saved, execution = claim(client, m, ident)
    store = client.app.state.store
    updated = saved.model_copy(deep=True)
    d = updated.entities[ident].data
    d.update(status="working", mode="live", task_lease="2000-01-01T00:00:00+00:00")
    d["execution"]["lease_expires_at"] = "2000-01-01T00:00:00+00:00"
    saved = store.save(updated, "orchestrator", "Interrupted live task", saved)
    with pytest.raises(ValueError, match="may have incurred a charge"):
        service.retry(m["id"], ident, Retry(revision=saved.revision))
    recovered = service.retry(
        m["id"], ident, Retry(revision=saved.revision, acknowledge_unknown=True)
    )
    assert recovered.entities[ident].data["status"] == "ready"
    assert recovered.entities[ident].data["execution"]["status"] == "stopped"
