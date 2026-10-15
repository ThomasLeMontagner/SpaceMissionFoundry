import json
from copy import deepcopy

import httpx
import pytest
from test_execution_recovery import crash, expire
from test_workflow import approve, command, to_trade

from app.engineering_tools.calculations import q
from app.services import data_alternatives as alternatives
from app.services.collaboration import Collaboration, Recovery, get_run

BOUNDS = dict(
    duty_min=0.01,
    duty_max=0.2,
    compression_min=1,
    compression_max=8,
    storage_min_gbit=1,
    storage_max_gbit=64,
)


def start(client, bounds=None):
    source = to_trade(client)
    model = command(
        client,
        source,
        "collaboration",
        candidate="selective",
        goal="Compare data-system designs",
        study="data-system",
        bounds=bounds or BOUNDS,
    )
    run_id = next(
        k for k, e in model["entities"].items() if e["data"].get("workflow") == "duty-collaboration"
    )
    return source, model, run_id


def test_alternatives_reach_review_and_only_approval_changes_three_inputs(client):
    source, model, run_id = start(client)
    for _ in range(5):
        model = command(client, model, f"collaboration/{run_id}/step")
        assert (
            model["entities"]["selective-data-inputs"]
            == source["entities"]["selective-data-inputs"]
        )
    data = model["entities"][run_id]["data"]
    assert data["status"] == "awaiting_approval"
    assert len(data["payload"]["alternatives"]) == len(data["bus"]["alternatives"]) == 3
    chosen = next(a for a in data["bus"]["alternatives"] if a["id"] == data["selected_alternative"])
    calculated = next(r for r in data["evaluate_bus"]["alternatives"] if r["id"] == chosen["id"])
    assert calculated["eligible"]
    assert q(calculated["data"]["inputs"]["storage"], "Gbit") == chosen["storage_gbit"]
    assert calculated["data"]["inputs"]["compression"]["value"] == chosen["compression"]
    accepted = approve(client, model)
    values = accepted["entities"]["selective-data-inputs"]["data"]["inputs"]
    assert q(values["storage"], "Gbit") == chosen["storage_gbit"]
    assert q(values["compression"], "") == chosen["compression"]
    assert q(values["duty"], "") == chosen["duty"]
    assert values["rate"] == source["entities"]["selective-data-inputs"]["data"]["inputs"]["rate"]
    assert accepted["phase"] == "Recalculation required"
    assert (
        client.get(f"/api/missions/{model['id']}/revisions/{source['revision']}").json() == source
    )


def test_failed_alternatives_block_submission_and_clarification_preserves_history_and_budget(
    client,
):
    _, model, run_id = start(
        client,
        {
            **BOUNDS,
            "duty_min": 0.9,
            "duty_max": 1,
            "compression_max": 1,
            "storage_min_gbit": 0.001,
            "storage_max_gbit": 0.002,
        },
    )
    for _ in range(5):
        model = command(client, model, f"collaboration/{run_id}/step")
    data = model["entities"][run_id]["data"]
    assert data["status"] == "blocked" and data["proposal_id"] is None
    assert not any(r["eligible"] for r in data["evaluate_bus"]["alternatives"])
    revised = command(
        client, model, f"collaboration/{run_id}/clarify", feedback="Reconsider the trade-offs"
    )
    new = revised["entities"][run_id]["data"]
    assert new["round_history"][0]["bus"] == data["bus"]
    assert new["budget"] == data["budget"] and new["bounds"] == data["bounds"]
    assert "bus" not in new and "selected_alternative" not in new


def test_challenged_selection_is_superseded_and_minimum_cannot_exceed_bounds(client):
    _, model, run_id = start(client)
    for _ in range(5):
        model = command(client, model, f"collaboration/{run_id}/step")
    data = model["entities"][run_id]["data"]
    model = command(
        client,
        model,
        f"proposals/{data['proposal_id']}/decision",
        action="challenge",
        reason="Review image quality assumptions",
    )
    root = f"/api/missions/{model['id']}/collaboration/{run_id}/clarify"
    assert (
        client.post(
            root, json=dict(revision=model["revision"], feedback="Raise duty", minimum_duty=0.5)
        ).status_code
        == 409
    )
    revised = command(
        client,
        model,
        f"collaboration/{run_id}/clarify",
        feedback="Prefer less compression",
        minimum_duty=0.01,
    )
    new = revised["entities"][run_id]["data"]
    assert revised["proposals"][data["proposal_id"]]["status"] == "superseded"
    assert new["round_history"][0]["selected_alternative"] == data["selected_alternative"]
    assert new["budget"] == data["budget"]


def test_recovery_preserves_completed_alternative_calculations(client, monkeypatch):
    _, model, run_id = start(client)
    service = Collaboration(client.app.state.store)
    saved = service.store.get(model["id"])
    for _ in range(2):
        saved = service.step(saved.id, run_id, saved.revision)
    evidence = deepcopy(get_run(saved, run_id).data["evaluate_payload"])
    saved = crash(service, saved, run_id, monkeypatch)
    expire(monkeypatch)
    saved = service.recover(saved.id, run_id, Recovery(revision=saved.revision))
    for _ in range(3):
        saved = service.step(saved.id, run_id, saved.revision)
    assert get_run(saved, run_id).data["status"] == "awaiting_approval"
    assert get_run(saved, run_id).data["evaluate_payload"] == evidence


@pytest.mark.parametrize("change", ["cancel", "source", "pause"])
def test_inflight_review_cannot_bypass_interruption(client, monkeypatch, change):
    _, model, run_id = start(client)
    service = Collaboration(client.app.state.store)
    saved = service.store.get(model["id"])
    for _ in range(4):
        saved = service.step(saved.id, run_id, saved.revision)
    original = alternatives.perform

    def interrupt(data, brief):
        result = original(data, brief)
        current = service.store.get(saved.id)
        if change == "cancel":
            service.cancel(current.id, run_id, current.revision)
        else:
            updated = current.model_copy(deep=True)
            if change == "pause":
                updated.paused = True
            else:
                updated.entities["selective-data-inputs"].title = "Changed engineering source"
            service.store.save(updated, "human", "Concurrent test change", current)
        return result

    monkeypatch.setattr(alternatives, "perform", interrupt)
    final = service.step(saved.id, run_id, saved.revision)
    data = get_run(final, run_id).data
    assert data["proposal_id"] is None
    assert data["status"] == {"cancel": "cancelled", "source": "stale", "pause": "ready"}[change]


def options():
    return dict(
        rationale="Trade science duty against resource use",
        alternatives=[
            dict(
                id="A",
                duty=0.2,
                compression=1.0,
                storage_gbit=1.0,
                rationale="High observation, likely resource conflict",
            ),
            dict(
                id="B",
                duty=0.01,
                compression=8.0,
                storage_gbit=32.0,
                rationale="Low duty, quality remains unverified",
            ),
            dict(
                id="C",
                duty=0.02,
                compression=8.0,
                storage_gbit=64.0,
                rationale="More storage and observation",
            ),
        ],
    )


@pytest.mark.parametrize("invalid_selection", [False, True])
def test_live_http_alternatives_and_separate_review_have_strict_selection_and_usage(
    client, monkeypatch, invalid_selection
):
    source = to_trade(client)
    for key, value in dict(
        LLM_PROVIDER="openai-compatible",
        LLM_MODEL="test-model",
        LLM_BASE_URL="https://example.invalid",
        LLM_API_KEY="test-key",
        LLM_MAX_PRICE_PER_MILLION="1",
        MAX_RUN_COST_EUR="1",
    ).items():
        monkeypatch.setenv(key, value)
    model = command(
        client,
        source,
        "collaboration",
        candidate="selective",
        goal="Compare configurations",
        study="data-system",
        bounds=BOUNDS,
        mode="live",
    )
    run_id = next(
        k for k, e in model["entities"].items() if e["data"].get("workflow") == "duty-collaboration"
    )
    calls = []
    real_client = httpx.Client

    def respond(request):
        content = json.loads(request.content)
        calls.append(content)
        payload = options()
        if len(calls) == 3:
            context = json.loads(content["messages"][1]["content"])
            assert "B" in context["eligible_ids"] and "A" not in context["eligible_ids"]
            assert len(context["data_analysis"]) == 3
            payload = dict(
                recommendation="submit",
                selected_id="A" if invalid_selection else "B",
                rationale="Mock separate Systems assessment",
                findings=[
                    dict(
                        severity="advisory",
                        summary="Image quality is unverified",
                        evidence=["bus_proposal"],
                    )
                ],
                follow_up="",
            )
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": json.dumps(payload)}}],
                "usage": {"total_tokens": 60},
            },
        )

    monkeypatch.setattr(
        "app.agents.design_provider.httpx.Client",
        lambda **kw: real_client(transport=httpx.MockTransport(respond), **kw),
    )
    for _ in range(5):
        model = command(client, model, f"collaboration/{run_id}/step")
    data = model["entities"][run_id]["data"]
    assert len(calls) == 3
    assert data["status"] == ("failed" if invalid_selection else "awaiting_approval")
    assert sum(entry["accounted_tokens"] for entry in data["budget"]["attempts"]) == 180
    assert model["entities"]["selective-data-inputs"] == source["entities"]["selective-data-inputs"]


@pytest.mark.parametrize("invalid", ["outside", "duplicate", "extra", "nan"])
def test_provider_cannot_exceed_bounds_or_add_fields(invalid):
    value = options()
    if invalid == "outside":
        value["alternatives"][0]["compression"] = 9.0
    elif invalid == "duplicate":
        value["alternatives"][1] = value["alternatives"][0]
    elif invalid == "extra":
        value["alternatives"][0]["daily_data"] = 1
    else:
        value["alternatives"][0]["duty"] = float("nan")
    with pytest.raises(ValueError):
        alternatives.checked(value, BOUNDS)


def test_bounds_are_required_ordered_and_have_a_variable_range(client):
    source = to_trade(client)
    root = f"/api/missions/{source['id']}/collaboration"
    for bounds in [
        None,
        {**BOUNDS, "duty_min": 0.3},
        dict(
            duty_min=0.1,
            duty_max=0.1,
            compression_min=2,
            compression_max=2,
            storage_min_gbit=4,
            storage_max_gbit=4,
        ),
    ]:
        result = client.post(
            root,
            json=dict(
                revision=source["revision"],
                candidate="selective",
                goal="Design alternatives",
                study="data-system",
                bounds=bounds,
            ),
        )
        assert result.status_code == 422


def test_no_eligible_options_skip_live_review_and_its_budget_reservation(client, monkeypatch):
    _, model, run_id = start(
        client,
        {
            **BOUNDS,
            "duty_min": 0.9,
            "duty_max": 1,
            "compression_max": 1,
            "storage_min_gbit": 0.001,
            "storage_max_gbit": 0.002,
        },
    )
    service = Collaboration(client.app.state.store)
    saved = service.store.get(model["id"])
    for _ in range(4):
        saved = service.step(saved.id, run_id, saved.revision)
    updated = saved.model_copy(deep=True)
    get_run(updated, run_id).data.update(mode="live", provider_model="test-model")
    saved = service.store.save(updated, "test", "Live review gate fixture", saved)
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setattr(
        alternatives,
        "request_json",
        lambda *args: pytest.fail("Ineligible alternatives must not incur a review call"),
    )
    final = service.step(saved.id, run_id, saved.revision)
    data = get_run(final, run_id).data
    assert data["status"] == "blocked"
    assert data["budget"]["attempts"][-1]["live"] is False
    assert data["budget"]["attempts"][-1]["accounted_tokens"] == 0


@pytest.mark.parametrize("recommendation", ["revise", "clarify"])
def test_systems_can_request_revision_without_selecting_an_option(
    client, monkeypatch, recommendation
):
    _, model, run_id = start(client)
    original = alternatives.perform

    def assessment(data, brief):
        result = original(data, brief)
        if data["stage"] == "systems":
            result["review"].update(
                recommendation=recommendation,
                selected_id=None,
                follow_up="Clarify acceptable compression quality",
            )
        return result

    monkeypatch.setattr(alternatives, "perform", assessment)
    for _ in range(5):
        model = command(client, model, f"collaboration/{run_id}/step")
    data = model["entities"][run_id]["data"]
    assert data["status"] == "blocked" and data["proposal_id"] is None
    assert data["systems_review"]["recommendation"] == recommendation
    assert "selected_alternative" not in data
