from datetime import timedelta

import pytest
from test_collaboration import start
from test_collaboration_execution import claim
from test_workflow import approve

from app.persistence.store import Store
from app.services import execution_recovery as leases
from app.services.collaboration import Collaboration, Recovery, get_run


class ProcessLost(BaseException):
    """Bypass the normal task error handler, like an abrupt worker exit."""


def crash(service, model, run_id, monkeypatch):
    def lost(*args):
        raise ProcessLost()

    with monkeypatch.context() as patch:
        patch.setattr(service, "perform", lost)
        with pytest.raises(ProcessLost):
            service.step(model.id, run_id, model.revision)
    return service.store.get(model.id)


def expire(monkeypatch):
    later = leases.utc_now() + timedelta(seconds=leases.LEASE_SECONDS + 1)
    monkeypatch.setattr(leases, "utc_now", lambda: later)


def interrupted(client, monkeypatch):
    source, model, run_id = start(client)
    service = Collaboration(client.app.state.store)
    saved = crash(service, service.store.get(model["id"]), run_id, monkeypatch)
    expire(monkeypatch)
    return source, service, saved, run_id


def test_reopened_store_recovers_only_unfinished_tasks_and_preserves_history(client, monkeypatch):
    source, model, run_id = start(client)
    service = Collaboration(client.app.state.store)
    saved = service.store.get(model["id"])
    for _ in range(2):
        saved = service.step(saved.id, run_id, saved.revision)
    checkpoint = get_run(saved, run_id).model_copy(deep=True)
    saved = crash(service, saved, run_id, monkeypatch)
    assert not service.recovery(saved.id, run_id)["available"]
    expire(monkeypatch)
    # A fresh service and database connection have no in-memory execution state.
    reopened = Store(service.store.engine.url.render_as_string(hide_password=False))
    try:
        service = Collaboration(reopened)
        assert service.recovery(saved.id, run_id)["available"]
        recovered = service.recover(saved.id, run_id, Recovery(revision=saved.revision))
        data = get_run(recovered, run_id).data
        assert data["stage"] == "bus" and data["completed"] == checkpoint.data["completed"]
        assert data["payload"] == checkpoint.data["payload"]
        assert data["evaluate_payload"] == checkpoint.data["evaluate_payload"]
        assert data["events"][: len(checkpoint.data["events"])] == checkpoint.data["events"]
        assert data["attempts"] == 3  # Recovery never resets the attempt budget.
        assert service.store.revision(saved.id, saved.revision) == saved
        stages = []
        original = service.perform

        def perform(m, run):
            stages.append(run.data["stage"])
            return original(m, run)

        monkeypatch.setattr(service, "perform", perform)
        recovered = service.begin_execution(saved.id, run_id, recovered.revision)
        service.execute_remaining(
            saved.id, run_id, get_run(recovered, run_id).data["execution"]["id"]
        )
        final = service.store.get(saved.id).model_dump(mode="json")
        assert stages == ["bus", "evaluate_bus", "systems"]
        assert final["entities"][run_id]["data"]["status"] == "awaiting_approval"
        assert (
            final["entities"]["selective-data-inputs"]
            == source["entities"]["selective-data-inputs"]
        )
        assert approve(client, final)["entities"][run_id]["data"]["status"] == "accepted"
    finally:
        reopened.engine.dispose()


def test_expired_claim_between_tasks_requires_recovery_and_fences_old_worker(client, monkeypatch):
    _, model, run_id = start(client)
    service, saved, token = claim(client, model, run_id)
    saved = service.step(saved.id, run_id, saved.revision, token)
    expire(monkeypatch)
    service.execute_remaining(saved.id, run_id, token)
    assert service.store.get(saved.id) == saved
    with pytest.raises(ValueError, match="lease expired"):
        service.step(saved.id, run_id, saved.revision, token)
    details = service.recovery(saved.id, run_id)
    assert details["available"] and not details["requires_confirmation"]
    recovered = service.recover(saved.id, run_id, Recovery(revision=saved.revision))
    assert get_run(recovered, run_id).data["execution"]["status"] == "stopped"
    service.execute_remaining(saved.id, run_id, token)
    assert service.store.get(saved.id) == recovered
    with pytest.raises(ValueError, match="Stale revision"):
        service.recover(saved.id, run_id, Recovery(revision=saved.revision))


def test_live_unknown_outcome_requires_explicit_confirmation_without_calling_provider(
    client, monkeypatch
):
    _, service, saved, run_id = interrupted(client, monkeypatch)
    live = saved.model_copy(deep=True)
    get_run(live, run_id).data.update(mode="live", provider_model="test-model")
    saved = service.store.save(live, "test", "Simulate interrupted live task", saved)
    monkeypatch.setenv("LLM_MODEL", "test-model")
    root = f"/api/missions/{saved.id}/collaboration/{run_id}"
    before = service.store.history(saved.id)
    for _ in range(2):
        details = client.get(root + "/recovery").json()
        assert details["available"] and details["requires_confirmation"]
    assert service.store.history(saved.id) == before
    body = {"revision": saved.revision}
    assert client.post(root + "/recover", json=body).status_code == 409
    assert (
        client.post(root + "/recover", json={**body, "retry_uncertain": "true"}).status_code == 422
    )
    assert service.store.get(saved.id) == saved

    def forbidden(*args):
        pytest.fail("Recovery must not call a model or execute a task")

    monkeypatch.setattr(Collaboration, "perform", forbidden)
    response = client.post(root + "/recover", json={**body, "retry_uncertain": True})
    assert response.status_code == 200
    data = response.json()["entities"][run_id]["data"]
    assert data["status"] == "ready" and data["attempt"] != get_run(saved, run_id).data["attempt"]
    assert data["events"][-1]["evidence"]["retry_confirmed"]
    assert not service.recovery(saved.id, run_id)["available"]


@pytest.mark.parametrize("recover_during_call", [False, True])
def test_late_response_cannot_publish_results_or_overwrite_recovery(
    client, monkeypatch, recover_during_call
):
    _, model, run_id = start(client)
    service = Collaboration(client.app.state.store)
    original = service.perform

    def late(m, run):
        result = original(m, run)
        expire(monkeypatch)
        if recover_during_call:
            service.recover(m.id, run_id, Recovery(revision=m.revision))
        return result

    monkeypatch.setattr(service, "perform", late)
    final = service.step(model["id"], run_id, model["revision"])
    data = get_run(final, run_id).data
    assert data["status"] == ("ready" if recover_during_call else "interrupted")
    assert data["completed"] == [] and "payload" not in data
    assert not any(p.status == "submitted" for p in final.proposals.values())
    assert service.recovery(final.id, run_id)["available"] is not recover_during_call
    if not recover_during_call:
        final = service.cancel(final.id, run_id, final.revision)
        assert get_run(final, run_id).data["status"] == "cancelled"


@pytest.mark.parametrize(
    "change,reason",
    [
        ("paused", "Resume"),
        ("archived", "Restore"),
        ("baseline", "Restore"),
        ("source", "Design inputs changed"),
        ("attempts", "attempt limit"),
        ("completed", "inconsistent"),
        ("evidence", "evidence is missing"),
        ("provider", "Provider model changed"),
        ("pending", "Resolve pending"),
    ],
)
def test_recovery_guards_preserve_checkpoint(client, monkeypatch, change, reason):
    _, service, saved, run_id = interrupted(client, monkeypatch)
    updated = saved.model_copy(deep=True)
    data = get_run(updated, run_id).data
    if change in ["paused", "archived"]:
        setattr(updated, change, True)
    elif change == "baseline":
        updated.baseline = "frozen-baseline"
    elif change == "source":
        updated.entities["selective-data-inputs"].title = "Changed source"
    elif change == "attempts":
        data["attempts"] = 10
    elif change == "completed":
        data["completed"] = ["bus"]
    elif change == "evidence":
        data.update(stage="bus", completed=["payload", "evaluate_payload"])
    elif change == "provider":
        data.update(mode="live", provider_model="old-model")
        monkeypatch.setenv("LLM_MODEL", "different-model")
    else:
        next(iter(updated.proposals.values())).status = "challenged"
    saved = service.store.save(updated, "test", "Recovery guard fixture", saved)
    details = service.recovery(saved.id, run_id)
    assert not details["available"] and reason in details["reason"]
    with pytest.raises(ValueError):
        service.recover(saved.id, run_id, Recovery(revision=saved.revision, retry_uncertain=True))
    assert service.store.get(saved.id) == saved


def test_active_lease_and_legacy_checkpoint_wait_for_expiry(client, monkeypatch):
    _, model, run_id = start(client)
    service = Collaboration(client.app.state.store)
    saved = crash(service, service.store.get(model["id"]), run_id, monkeypatch)
    with pytest.raises(ValueError, match="still active"):
        service.recover(saved.id, run_id, Recovery(revision=saved.revision))
    legacy = saved.model_copy(deep=True)
    get_run(legacy, run_id).data.pop("task_lease")
    saved = service.store.save(legacy, "test", "Legacy checkpoint", saved)
    assert not service.recovery(saved.id, run_id)["available"]
    expire(monkeypatch)
    assert service.recovery(saved.id, run_id)["available"]
    invalid = saved.model_copy(deep=True)
    get_run(invalid, run_id).data["events"][-1]["timestamp"] = "unknown"
    saved = service.store.save(invalid, "test", "Missing legacy time", saved)
    assert not service.recovery(saved.id, run_id)["available"]


def test_recovery_is_mission_scoped(client, monkeypatch):
    _, service, saved, run_id = interrupted(client, monkeypatch)
    _, other, _ = start(client)
    root = f"/api/missions/{other['id']}/collaboration/{run_id}"
    assert client.get(root + "/recovery").status_code == 409
    assert client.post(root + "/recover", json={"revision": other["revision"]}).status_code == 409
    assert service.store.get(saved.id) == saved
