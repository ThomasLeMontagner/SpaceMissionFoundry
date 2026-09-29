import json

import httpx
import pytest
from test_workflow import approve, command, to_ready, to_trade

from app.agents.design_provider import DutyProposal, propose
from app.services.collaboration import get_run


def start(client):
    source = to_trade(client)
    model = command(
        client,
        source,
        "collaboration",
        candidate="selective",
        goal="Increase useful observation time",
    )
    run_id = next(
        k for k, e in model["entities"].items() if e["data"].get("workflow") == "duty-collaboration"
    )
    return source, model, run_id


def test_negotiation_requires_approval_and_preserves_source(client):
    source, model, run_id = start(client)
    original = source["entities"]["selective-data-inputs"]
    for _ in range(5):
        model = command(client, model, f"collaboration/{run_id}/step")
        assert model["entities"]["selective-data-inputs"] == original
    run = model["entities"][run_id]["data"]
    assert run["status"] == "awaiting_approval"
    assert not run["evaluate_payload"]["link"]["outputs"]["compliant"]
    assert run["evaluate_bus"]["link"]["outputs"]["compliant"]
    assert len(run["completed"]) == 5
    assert len({e["id"] for e in run["events"]}) == len(run["events"])
    assert all(e["source_revision"] == source["revision"] for e in run["events"])
    accepted = approve(client, model)
    assert accepted["entities"][run_id]["data"]["status"] == "accepted"
    assert (
        accepted["entities"]["selective-data-inputs"]["data"]["inputs"]["duty"]["value"]
        == run["bus"]["duty"]
    )
    historical = client.get(f"/api/missions/{source['id']}/revisions/{source['revision']}").json()
    assert historical == source
    assert client.get(f"/api/missions/{model['id']}").json() == accepted


def test_failure_retry_pause_and_cancel(client, monkeypatch):
    _, model, run_id = start(client)

    def fail(*args):
        raise ValueError("secret provider response")

    monkeypatch.setattr("app.services.collaboration.propose", fail)
    model = command(client, model, f"collaboration/{run_id}/step")
    assert model["entities"][run_id]["data"]["status"] == "failed"
    assert "secret provider" not in json.dumps(model)
    model = command(client, model, "pause")
    assert (
        client.post(
            f"/api/missions/{model['id']}/collaboration/{run_id}/step",
            json={"revision": model["revision"]},
        ).status_code
        == 409
    )
    model = command(client, model, "pause")
    monkeypatch.setattr("app.services.collaboration.propose", propose)
    model = command(client, model, f"collaboration/{run_id}/step")
    assert model["entities"][run_id]["data"]["stage"] == "evaluate_payload"
    model = command(client, model, f"collaboration/{run_id}/cancel")
    assert model["entities"][run_id]["data"]["status"] == "cancelled"


@pytest.mark.parametrize("change", ["cancel", "edit"])
def test_inflight_results_cannot_overwrite_cancellation_or_changed_source(
    client, monkeypatch, change
):
    source, model, run_id = start(client)

    def concurrent(*args):
        store = client.app.state.store
        current = store.get(model["id"])
        assert get_run(current, run_id).data["status"] == "working"
        if change == "cancel":
            command(client, current.model_dump(mode="json"), f"collaboration/{run_id}/cancel")
        else:
            updated = current.model_copy(deep=True)
            updated.entities["selective-data-inputs"].data["inputs"]["duty"]["value"] = 0.04
            store.save(updated, "human", "Concurrent source change", current)
        return DutyProposal(duty=0.1, rationale="Test response"), {}

    monkeypatch.setattr("app.services.collaboration.propose", concurrent)
    result = command(client, model, f"collaboration/{run_id}/step")
    run = result["entities"][run_id]["data"]
    assert run["status"] == ("cancelled" if change == "cancel" else "stale")
    assert "payload" not in run
    assert result["proposals"] == source["proposals"]


@pytest.mark.parametrize(
    "answer,valid",
    [
        ({"duty": 0.037, "rationale": "Model chosen value"}, True),
        ({"duty": 2, "rationale": "Bad range"}, False),
        ({"duty": 0.03, "rationale": "Invented result", "compliant": True}, False),
    ],
)
def test_live_provider_contract_without_network(monkeypatch, answer, valid):
    for key, value in {
        "LLM_PROVIDER": "openai-compatible",
        "LLM_MODEL": "test-model",
        "LLM_BASE_URL": "https://example.invalid/v1",
        "LLM_API_KEY": "test-only",
        "LLM_MAX_PRICE_PER_MILLION": "1",
        "MAX_RUN_COST_EUR": "1",
    }.items():
        monkeypatch.setenv(key, value)
    real_client = httpx.Client

    def respond(request):
        body = json.loads(request.content)
        assert body["model"] == "test-model"
        assert body["response_format"] == {"type": "json_object"}
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": json.dumps(answer)}}],
                "usage": {"total_tokens": 42},
            },
        )

    monkeypatch.setattr(
        "app.agents.design_provider.httpx.Client",
        lambda **kw: real_client(transport=httpx.MockTransport(respond), **kw),
    )
    if valid:
        result, usage = propose("payload", {"goal": "Test mission"}, "live")
        assert result.duty == 0.037
        assert usage["tokens"] == 42 and usage["cost"] is None
    else:
        with pytest.raises(ValueError, match="failed validation"):
            propose("payload", {}, "live")


def test_active_run_blocks_baseline_and_cross_mission_commands(client):
    model = to_ready(client)
    model = command(
        client, model, "collaboration", candidate="selective", goal="Review duty allocation"
    )
    run_id = next(
        k for k, e in model["entities"].items() if e["data"].get("workflow") == "duty-collaboration"
    )
    root = f"/api/missions/{model['id']}"
    response = client.post(
        root + "/baseline",
        json={"revision": model["revision"], "name": "Premature", "confirm": True},
    )
    assert response.status_code == 409
    other = to_trade(client)
    assert (
        client.post(
            f"/api/missions/{other['id']}/collaboration/{run_id}/step",
            json={"revision": other["revision"]},
        ).status_code
        == 409
    )
    model = command(client, model, f"collaboration/{run_id}/cancel")
    model = command(client, model, "baseline", name="Completed review", confirm=True)
    assert model["baseline"]


def test_model_values_drive_tool_evidence_and_rejection_preserves_inputs(client, monkeypatch):
    _, model, run_id = start(client)
    original = model["entities"]["selective-data-inputs"]

    def generated(role, context, mode):
        if role == "bus":
            assert context["payload_proposal"]["duty"] == 0.09
            assert not context["evaluation"]["link"]["outputs"]["compliant"]
        return DutyProposal(
            duty=0.09 if role == "payload" else 0.025, rationale="Model fixture chosen value"
        ), {"tokens": 70, "cost": None}

    monkeypatch.setattr("app.services.collaboration.propose", generated)
    for _ in range(5):
        model = command(client, model, f"collaboration/{run_id}/step")
    run = model["entities"][run_id]["data"]
    assert run["evaluate_bus"]["data"]["inputs"]["duty"]["value"] == 0.025
    model = command(
        client,
        model,
        f"proposals/{run['proposal_id']}/decision",
        action="reject",
        reason="Science needs a different duty allocation",
    )
    assert model["entities"]["selective-data-inputs"] == original
    assert model["entities"][run_id]["data"]["status"] == "rejected"
