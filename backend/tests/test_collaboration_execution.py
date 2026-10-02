import pytest
from test_collaboration import start
from test_workflow import approve, command

from app.agents.design_provider import propose
from app.services.collaboration import Collaboration, get_run


def claim(client, model, run_id):
    service = Collaboration(client.app.state.store)
    claimed = service.begin_execution(model["id"], run_id, model["revision"])
    token = get_run(claimed, run_id).data["execution"]["id"]
    return service, claimed, token


def test_background_endpoint_completes_round_without_acceptance(client):
    source, model, run_id = start(client)
    response = client.post(
        f"/api/missions/{model['id']}/collaboration/{run_id}/run",
        json={"revision": model["revision"]},
    )
    assert response.status_code == 202
    assert response.json()["entities"][run_id]["data"]["execution"]["status"] == "running"
    # TestClient waits for BackgroundTasks; HTTP callers receive the initial snapshot.
    finished = client.get(f"/api/missions/{model['id']}").json()
    run = finished["entities"][run_id]["data"]
    assert run["status"] == "awaiting_approval"
    assert run["execution"]["status"] == "stopped"
    assert len(run["completed"]) == 5
    assert (
        finished["entities"]["selective-data-inputs"] == source["entities"]["selective-data-inputs"]
    )
    assert approve(client, finished)["entities"][run_id]["data"]["status"] == "accepted"


def test_claim_prevents_duplicate_start_and_manual_steps(client):
    _, model, run_id = start(client)
    service, claimed, token = claim(client, model, run_id)
    with pytest.raises(ValueError, match="already claimed"):
        service.begin_execution(model["id"], run_id, claimed.revision)
    with pytest.raises(ValueError, match="owns this run"):
        service.step(model["id"], run_id, claimed.revision)
    service.execute_remaining(model["id"], run_id, "wrong-token")
    assert client.app.state.store.get(model["id"]).revision == claimed.revision
    service.cancel(model["id"], run_id, claimed.revision)
    service.execute_remaining(model["id"], run_id, token)
    run = get_run(client.app.state.store.get(model["id"]), run_id)
    assert run.data["status"] == "cancelled" and run.data["attempts"] == 0


def test_concurrent_human_proposal_stops_execution_and_remains_approvable(client, monkeypatch):
    _, model, run_id = start(client)
    service, _, token = claim(client, model, run_id)
    calls = []

    def provider(*args):
        calls.append(args[0])
        current = client.app.state.store.get(model["id"]).model_dump(mode="json")
        inputs = current["entities"]["selective-data-inputs"]["data"]["inputs"]
        inputs["duty"] = {"value": 0.025, "unit": "dimensionless"}
        command(
            client,
            current,
            "objects/selective-data-inputs/edit",
            changes={"inputs": inputs},
            reason="Human proposes a competing duty allocation",
        )
        return propose(*args)

    monkeypatch.setattr("app.services.collaboration.propose", provider)
    service.execute_remaining(model["id"], run_id, token)
    final = client.app.state.store.get(model["id"]).model_dump(mode="json")
    assert calls == ["payload"]
    assert final["entities"][run_id]["data"]["execution"]["status"] == "stopped"
    accepted = approve(client, final)
    assert accepted["entities"]["selective-data-inputs"]["data"]["inputs"]["duty"]["value"] == 0.025


@pytest.mark.parametrize("action", ["pause", "cancel", "fail"])
def test_inflight_interruptions_stop_future_calls_without_retry(client, monkeypatch, action):
    _, model, run_id = start(client)
    service, _, token = claim(client, model, run_id)
    calls = []

    def provider(*args):
        calls.append(args[0])
        current = client.app.state.store.get(model["id"]).model_dump(mode="json")
        if action == "pause":
            paused = command(client, current, "pause")
            command(client, paused, "pause")  # Quick resume must not undo the stop request.
        elif action == "cancel":
            command(client, current, f"collaboration/{run_id}/cancel")
        else:
            raise ValueError("secret failure detail")
        return propose(*args)

    monkeypatch.setattr("app.services.collaboration.propose", provider)
    service.execute_remaining(model["id"], run_id, token)
    final = client.app.state.store.get(model["id"])
    run = get_run(final, run_id)
    assert calls == ["payload"]
    assert run.data["execution"]["status"] == "stopped"
    assert run.data["status"] == {"pause": "ready", "cancel": "cancelled", "fail": "failed"}[action]
    assert "secret failure detail" not in final.model_dump_json()
    if action == "pause":
        assert run.data["stage"] == "evaluate_payload" and not final.paused
    else:
        assert "payload" not in run.data
