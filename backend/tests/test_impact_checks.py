from copy import deepcopy

import pytest
from test_data_alternatives import BOUNDS
from test_workflow import approve, command, to_trade

from app.engineering_tools.calculations import execute
from app.services import data_alternatives, impact_checks
from app.services.collaboration import Collaboration, get_run

ASSUMPTIONS = dict(
    storage_kg_per_gbit=0.01,
    storage_w_per_gbit=0.001,
    observation_w=1.0,
    processing_w_per_ratio=0.01,
    basis="Illustrative test coefficients, not qualified hardware",
)


def start(client, assumptions=ASSUMPTIONS):
    source = to_trade(client)
    model = command(
        client,
        source,
        "collaboration",
        candidate="selective",
        goal="Compare all budgets",
        study="cross-discipline",
        bounds={**BOUNDS, "storage_min_gbit": 300, "storage_max_gbit": 500},
        impact_assumptions=assumptions,
    )
    run_id = next(
        k for k, e in model["entities"].items() if e["data"].get("study") == "cross-discipline"
    )
    return source, model, run_id


def finish(client, model, run_id):
    for _ in range(5):
        model = command(client, model, f"collaboration/{run_id}/step")
    return model


def test_cross_discipline_approval_persists_exact_evaluated_inputs(client):
    source, model, run_id = start(client)
    model = finish(client, model, run_id)
    data = model["entities"][run_id]["data"]
    assert data["status"] == "awaiting_approval"
    selected = next(
        r for r in data["evaluate_bus"]["alternatives"] if r["id"] == data["selected_alternative"]
    )
    for tool in ["data", "mass", "power"]:
        assert (
            model["entities"][f"selective-{tool}-inputs"]
            == source["entities"][f"selective-{tool}-inputs"]
        )
    assert len(model["proposals"][data["proposal_id"]]["operations"]) == 3
    accepted = approve(client, model)
    assert accepted["phase"] == "Recalculation required"
    for tool in ["data", "mass", "power"]:
        values = deepcopy(accepted["entities"][f"selective-{tool}-inputs"]["data"]["inputs"])
        if tool == "power":
            assert "period" not in values and "eclipse" not in values
            values.update({k: selected[tool]["inputs"][k] for k in ["period", "eclipse"]})
        assert execute(tool, values, accepted["revision"])["outputs"] == selected[tool]["outputs"]
    assert selected["impact_deltas"]["added_mass_kg"] > 0


@pytest.mark.parametrize("field", [None, "storage_kg_per_gbit", "storage_w_per_gbit"])
def test_missing_assumptions_or_failed_budgets_block_without_systems_call(
    client, monkeypatch, field
):
    assumptions = None if field is None else {**ASSUMPTIONS, field: 100.0}
    _, model, run_id = start(client, assumptions)
    service = Collaboration(client.app.state.store)
    saved = service.store.get(model["id"])
    for _ in range(4):
        saved = service.step(saved.id, run_id, saved.revision)
    updated = saved.model_copy(deep=True)
    get_run(updated, run_id).data.update(mode="live", provider_model="mock-model")
    saved = service.store.save(updated, "test", "Gate test fixture", saved)
    monkeypatch.setenv("LLM_MODEL", "mock-model")
    monkeypatch.setattr(
        data_alternatives, "request_json", lambda *args: pytest.fail("Must not call model")
    )
    saved = service.step(saved.id, run_id, saved.revision)
    data = get_run(saved, run_id).data
    assert data["status"] == "blocked" and data["proposal_id"] is None
    assert all(not r["eligible"] and r["blockers"] for r in data["evaluate_bus"]["alternatives"])
    assert data["budget"]["attempts"][-1]["live"] is False


def test_increment_model_units_workload_and_no_savings_credit():
    from app.orchestration.scenario import inputs

    baseline = inputs("selective")
    data = dict(inputs=baseline, impact_assumptions=ASSUMPTIONS, source_revision=12)
    mass, power, delta = impact_checks.derived_inputs(
        data, dict(duty=0.1, compression=8, storage_gbit=300)
    )
    assert delta["added_mass_kg"] == pytest.approx(0.44)  # 32 Gbyte = 256 Gbit
    assert delta["added_average_w"] == pytest.approx(
        44 * 0.001 + 0.08 + (0.1 * 7 - 0.02 * 3) * 0.01
    )
    assert delta["added_eclipse_w"] == pytest.approx(0.044 + 1 + 0.07)
    assert baseline["power"] != power
    assert baseline["mass"] != mass
    mass, power, delta = impact_checks.derived_inputs(
        data, dict(duty=0.01, compression=1, storage_gbit=1)
    )
    assert mass == baseline["mass"] and power == baseline["power"]
    assert all(v == 0 for v in delta.values())


@pytest.mark.parametrize("value", [-1, float("inf"), True, "1"])
def test_coefficients_reject_invalid_numbers(value):
    with pytest.raises(ValueError):
        impact_checks.ImpactAssumptions.model_validate(
            {**ASSUMPTIONS, "storage_kg_per_gbit": value}
        )


def test_clarification_preserves_assumptions_and_budget(client):
    _, model, run_id = start(client)
    model = finish(client, model, run_id)
    data = model["entities"][run_id]["data"]
    model = command(
        client,
        model,
        f"proposals/{data['proposal_id']}/decision",
        action="challenge",
        reason="Reconsider resource costs",
    )
    model = command(
        client, model, f"collaboration/{run_id}/clarify", feedback="Prefer lower resource use"
    )
    new = model["entities"][run_id]["data"]
    assert new["impact_assumptions"] == ASSUMPTIONS and new["budget"] == data["budget"]
    assert new["round_history"][0]["evaluate_bus"] == data["evaluate_bus"]


def test_recovery_preserves_mass_power_evidence(client, monkeypatch):
    from test_execution_recovery import crash, expire

    from app.services.collaboration import Recovery

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


def test_changed_mass_source_discards_review(client, monkeypatch):
    _, model, run_id = start(client)
    service = Collaboration(client.app.state.store)
    saved = service.store.get(model["id"])
    for _ in range(4):
        saved = service.step(saved.id, run_id, saved.revision)
    original = data_alternatives.perform

    def change(data, brief):
        result = original(data, brief)
        current = service.store.get(saved.id)
        updated = current.model_copy(deep=True)
        updated.entities["selective-mass-inputs"].data["inputs"]["limit"]["value"] = 19
        service.store.save(updated, "test", "Concurrent mass edit", current)
        return result

    monkeypatch.setattr(data_alternatives, "perform", change)
    final = service.step(saved.id, run_id, saved.revision)
    assert get_run(final, run_id).data["status"] == "stale"
    assert get_run(final, run_id).data["proposal_id"] is None
