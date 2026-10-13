from datetime import timedelta

import pytest
from test_execution_recovery import crash, expire
from test_workflow import command, to_trade

from app.agents.design_provider import CALL_TOKEN_RESERVATION, propose
from app.agents.systems_review import review
from app.persistence.store import Store
from app.services import execution_recovery as clock
from app.services.collaboration import Collaboration, Recovery, get_run
from app.services.run_budget import Limits, totals


def start_budget(client, monkeypatch, **limits):
    source = to_trade(client)
    monkeypatch.setenv("LLM_PROVIDER", "openai-compatible")
    monkeypatch.setenv("LLM_MODEL", "budget-test")
    monkeypatch.setenv("LLM_MAX_PRICE_PER_MILLION", "1")
    calls = []

    def proposal(role, context, mode):
        calls.append(role)
        result, _ = propose(role, context, "simulation")
        return result, {"tokens": 50, "cost": None}

    def assessment(context, mode):
        calls.append("systems")
        result, _ = review(context, "simulation")
        return result, {"tokens": 75, "cost": None}

    monkeypatch.setattr("app.services.collaboration.propose", proposal)
    monkeypatch.setattr("app.services.collaboration.review", assessment)
    model = command(
        client,
        source,
        "collaboration",
        candidate="selective",
        goal="Test budget control",
        mode="live",
        limits=limits,
    )
    run_id = next(
        k for k, e in model["entities"].items() if e["data"].get("workflow") == "duty-collaboration"
    )
    return (
        Collaboration(client.app.state.store),
        client.app.state.store.get(model["id"]),
        run_id,
        calls,
    )


@pytest.mark.parametrize("limits", [{"tokens": CALL_TOKEN_RESERVATION - 1}, {"cost_eur": 0.001}])
def test_insufficient_reservation_stops_automatic_run_before_any_call(client, monkeypatch, limits):
    service, saved, run_id, calls = start_budget(client, monkeypatch, **limits)
    claimed = service.begin_execution(saved.id, run_id, saved.revision)
    service.execute_remaining(saved.id, run_id, get_run(claimed, run_id).data["execution"]["id"])
    final = service.store.get(saved.id)
    data = get_run(final, run_id).data
    assert data["status"] == "budget_blocked" and calls == []
    assert data["budget"]["attempts"] == [] and data["attempts"] == 0
    assert data["execution"]["status"] == "stopped"
    assert final.entities["selective-data-inputs"] == saved.entities["selective-data-inputs"]
    cancelled = service.cancel(final.id, run_id, final.revision)
    assert get_run(cancelled, run_id).data["status"] == "cancelled"


def test_known_usage_replaces_reservation_and_accumulates_across_rounds(client, monkeypatch):
    service, saved, run_id, calls = start_budget(client, monkeypatch)
    for _ in range(5):
        saved = service.step(saved.id, run_id, saved.revision)
    budget = get_run(saved, run_id).data["budget"]
    assert calls == ["payload", "bus", "systems"]
    assert totals(budget) == {"tokens": 175, "cost_eur": 0.000175}
    assert len(budget["attempts"]) == 5
    assert all(e["elapsed_seconds"] is not None for e in budget["attempts"])
    proposal_id = get_run(saved, run_id).data["proposal_id"]
    m = command(
        client,
        saved.model_dump(mode="json"),
        f"proposals/{proposal_id}/decision",
        action="challenge",
        reason="Need more observation time",
    )
    m = command(
        client, m, f"collaboration/{run_id}/clarify", feedback="Please revise", minimum_duty=0.035
    )
    assert m["entities"][run_id]["data"]["budget"] == budget
    saved = service.step(saved.id, run_id, m["revision"])
    new_budget = get_run(saved, run_id).data["budget"]
    assert totals(new_budget)["tokens"] == 225
    assert new_budget["deadline"] == budget["deadline"]
    assert new_budget["attempts"][-1]["round"] == 1


def test_each_later_call_needs_room_for_its_full_reservation(client, monkeypatch):
    service, saved, run_id, calls = start_budget(client, monkeypatch, tokens=CALL_TOKEN_RESERVATION)
    for _ in range(3):
        saved = service.step(saved.id, run_id, saved.revision)
    data = get_run(saved, run_id).data
    assert calls == ["payload"]
    assert data["status"] == "budget_blocked" and data["stage"] == "bus"
    assert totals(data["budget"])["tokens"] == 50


def test_unknown_usage_survives_crash_recovery_and_database_reopen(client, monkeypatch):
    service, saved, run_id, calls = start_budget(client, monkeypatch, tokens=CALL_TOKEN_RESERVATION)
    saved = crash(service, saved, run_id, monkeypatch)
    expire(monkeypatch)
    reopened = Store(service.store.engine.url.render_as_string(hide_password=False))
    try:
        service = Collaboration(reopened)
        recovered = service.recover(
            saved.id, run_id, Recovery(revision=saved.revision, retry_uncertain=True)
        )
        assert get_run(recovered, run_id).data["budget"] == get_run(saved, run_id).data["budget"]
        final = service.step(saved.id, run_id, recovered.revision)
        data = get_run(final, run_id).data
        assert data["status"] == "budget_blocked" and calls == []
        assert totals(data["budget"])["tokens"] == CALL_TOKEN_RESERVATION
        assert data["budget"]["attempts"][0]["reported_tokens"] is None
    finally:
        reopened.engine.dispose()


@pytest.mark.parametrize("outcome", ["error", "missing", "cancel"])
def test_unknown_or_cancelled_call_keeps_reservation(client, monkeypatch, outcome):
    service, saved, run_id, calls = start_budget(client, monkeypatch)
    original = service.perform

    def uncertain(m, run):
        if outcome == "error":
            raise ValueError("private provider detail")
        result = original(m, run)
        if outcome == "missing":
            result["usage"]["tokens"] = None
        else:
            service.cancel(m.id, run_id, m.revision)
        return result

    monkeypatch.setattr(service, "perform", uncertain)
    final = service.step(saved.id, run_id, saved.revision)
    data = get_run(final, run_id).data
    assert totals(data["budget"])["tokens"] == CALL_TOKEN_RESERVATION
    assert data["budget"]["attempts"][0]["status"] == "unknown"
    assert "private provider detail" not in final.model_dump_json()


@pytest.mark.parametrize("during", [False, True])
def test_elapsed_limit_blocks_start_or_discards_overdue_result(client, monkeypatch, during):
    service, saved, run_id, calls = start_budget(client, monkeypatch, elapsed_seconds=1)
    original = service.perform
    later = clock.utc_now() + timedelta(seconds=2)
    if during:

        def slow(m, run):
            result = original(m, run)
            monkeypatch.setattr(clock, "utc_now", lambda: later)
            return result

        monkeypatch.setattr(service, "perform", slow)
    else:
        monkeypatch.setattr(clock, "utc_now", lambda: later)
    final = service.step(saved.id, run_id, saved.revision)
    data = get_run(final, run_id).data
    assert data["status"] == "budget_blocked"
    assert calls == (["payload"] if during else [])
    assert "payload" not in data and data["completed"] == []
    assert totals(data["budget"])["tokens"] == (50 if during else 0)


def test_reported_overrun_blocks_result_publication(client, monkeypatch):
    service, saved, run_id, _ = start_budget(client, monkeypatch, tokens=CALL_TOKEN_RESERVATION)
    original = service.perform

    def overrun(m, run):
        result = original(m, run)
        result["usage"]["tokens"] = CALL_TOKEN_RESERVATION + 1
        return result

    monkeypatch.setattr(service, "perform", overrun)
    final = service.step(saved.id, run_id, saved.revision)
    data = get_run(final, run_id).data
    assert data["status"] == "budget_blocked" and "payload" not in data
    assert totals(data["budget"])["tokens"] == CALL_TOKEN_RESERVATION + 1


@pytest.mark.parametrize("change", ["price", "legacy"])
def test_changed_pricing_and_unknown_legacy_spending_fail_closed(client, monkeypatch, change):
    service, saved, run_id, calls = start_budget(client, monkeypatch)
    if change == "price":
        monkeypatch.setenv("LLM_MAX_PRICE_PER_MILLION", "2")
    else:
        legacy = saved.model_copy(deep=True)
        get_run(legacy, run_id).data.pop("budget")
        saved = service.store.save(legacy, "test", "Legacy run", saved)
    final = service.step(saved.id, run_id, saved.revision)
    assert get_run(final, run_id).data["status"] == "budget_blocked" and calls == []


@pytest.mark.parametrize(
    "limits",
    [
        {"tokens": -1},
        {"tokens": 1.5},
        {"elapsed_seconds": 0},
        {"cost_eur": float("inf")},
        {"cost_eur": -1},
    ],
)
def test_limits_are_finite_and_bounded(limits):
    with pytest.raises(ValueError):
        Limits(**limits)
