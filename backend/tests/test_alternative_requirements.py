from copy import deepcopy

import pytest
from test_data_alternatives import BOUNDS
from test_impact_checks import ASSUMPTIONS, finish
from test_workflow import approve, command, to_trade

from app.services import alternative_requirements, data_alternatives
from app.services.collaboration import Collaboration, get_run


def start(client, mandatory=None, missing=None, mode="simulation", initial=None):
    initial = initial or to_trade(client)
    store = client.app.state.store
    old = store.get(initial["id"])
    changed = old.model_copy(deep=True)
    for e in changed.entities.values():
        if e.kind == "Requirement":
            e.data["priority"] = "should"
    req = changed.entities["req-launch"]
    req.data.update(
        priority="must",
        criterion=mandatory
        or dict(metric="mass.total", operator="<=", threshold=dict(value=30, unit="kg")),
    )
    if missing:
        if missing == "criterion":
            req.data.pop("criterion", None)
        else:
            changed.entities.pop(missing)
    source = store.save(changed, "test", "Requirement study fixture", old).model_dump(mode="json")
    model = command(
        client,
        source,
        "collaboration",
        candidate="selective",
        goal="Meet mission criteria",
        study="cross-discipline",
        bounds=BOUNDS,
        impact_assumptions=ASSUMPTIONS,
        check_requirements=True,
        mode=mode,
    )
    run_id = next(k for k, e in model["entities"].items() if e["data"].get("check_requirements"))
    return source, model, run_id


def test_fresh_option_checks_do_not_overwrite_accepted_evidence(client):
    source, model, run_id = start(client)
    model = finish(client, model, run_id)
    data = model["entities"][run_id]["data"]
    assert data["status"] == "awaiting_approval"
    for ident, entity in source["entities"].items():
        if entity["kind"] in ["VerificationItem", "AnalysisRun", "Parameter"]:
            assert model["entities"][ident] == entity
    for row in data["evaluate_bus"]["alternatives"]:
        check = next(c for c in row["requirement_checks"] if c["requirement"] == "req-launch")
        assert check["status"] == "pass"
        assert check["analysis_source_revision"] == source["revision"]
        assert row["delivery"]["inputs"]["payload"] == row["data"]["inputs"]
        assert row["delivery"]["inputs"]["link_result"] == row["link"]["outputs"]
    assert approve(client, model)["phase"] == "Recalculation required"


@pytest.mark.parametrize(
    "missing", ["criterion", "mission-access-inputs", "selective-delivery-inputs"]
)
def test_missing_required_evidence_blocks_submission(client, missing):
    _, model, run_id = start(client, missing=missing)
    model = finish(client, model, run_id)
    data = model["entities"][run_id]["data"]
    assert data["status"] == "blocked" and data["proposal_id"] is None
    assert all(
        not row["eligible"] and row["requirement_blockers"]
        for row in data["evaluate_bus"]["alternatives"]
    )


def test_failed_requirement_cannot_reuse_accepted_passing_result(client):
    _, model, run_id = start(
        client,
        mandatory=dict(metric="mass.total", operator="<=", threshold=dict(value=1, unit="kg")),
    )
    model = finish(client, model, run_id)
    data = model["entities"][run_id]["data"]
    assert data["status"] == "blocked"
    assert all(
        any(c["status"] == "fail" for c in row["requirement_checks"])
        for row in data["evaluate_bus"]["alternatives"]
    )


@pytest.mark.parametrize(
    "observed,contact,deadline,expected",
    [
        (True, True, 1000, "pass"),
        (True, False, 100, "fail"),
        (True, False, 1000, "unverified"),
        (False, True, 1000, "unverified"),
    ],
)
def test_deadline_checks_preserve_finite_horizon_semantics(
    client, observed, contact, deadline, expected
):
    _, model, run_id = start(
        client,
        mandatory=dict(
            metric="delivery.maximum_latency",
            operator="<=",
            threshold=dict(value=deadline, unit="s"),
        ),
    )
    data = model["entities"][run_id]["data"]
    option = dict(id="A", duty=0.01, compression=8.0, storage_gbit=32.0, rationale="Test option")
    proposal = dict(
        alternatives=[option, {**option, "id": "B", "duty": 0.02}],
        rationale="Two test configurations",
    )
    rows = data_alternatives.evaluate({**data, "check_requirements": False}, proposal)[
        "alternatives"
    ]
    shared = alternative_requirements.geometry(data, 2)
    shared["access"]["outputs"].update(
        horizon=dict(value=200, unit="s"),
        sample_step=dict(value=1, unit="s"),
        targets=[
            dict(name="Test target", windows=[dict(start_s=10, end_s=20)] if observed else [])
        ],
        network_windows=[dict(start_s=30, end_s=190)] if contact else [],
    )
    data["inputs"]["delivery"] = {
        k: dict(value=0, unit="s") for k in ["onboard_delay", "ground_delay", "dissemination_delay"]
    }
    result = alternative_requirements.evaluate(
        data, data_alternatives.inputs(data, option), rows[0], shared
    )
    check = next(c for c in result["requirement_checks"] if c["priority"] == "must")
    assert check["status"] == expected
    assert result["requirements_eligible"] == (expected == "pass")


def test_requirement_changes_discard_inflight_systems_review(client, monkeypatch):
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
        updated.entities["req-launch"].data["criterion"]["threshold"]["value"] = 1
        service.store.save(updated, "test", "Concurrent criterion change", current)
        return result

    monkeypatch.setattr(data_alternatives, "perform", change)
    saved = service.step(saved.id, run_id, saved.revision)
    assert get_run(saved, run_id).data["status"] == "stale"
    assert get_run(saved, run_id).data["proposal_id"] is None


def test_recovery_preserves_requirement_checks(client, monkeypatch):
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


def test_live_provider_receives_requirement_evidence_and_selects_only_eligible(client, monkeypatch):
    import json

    import httpx
    from test_data_alternatives import options

    initial = to_trade(client)

    for key, value in dict(
        LLM_PROVIDER="openai-compatible",
        LLM_MODEL="test-model",
        LLM_BASE_URL="https://example.invalid",
        LLM_API_KEY="test-key",
        LLM_MAX_PRICE_PER_MILLION="1",
        MAX_RUN_COST_EUR="1",
    ).items():
        monkeypatch.setenv(key, value)
    _, model, run_id = start(client, mode="live", initial=initial)
    calls = []
    real_client = httpx.Client

    def respond(request):
        body = json.loads(request.content)
        context = json.loads(body["messages"][1]["content"])
        calls.append(context)
        payload = options()
        if len(calls) == 2:
            assert "mission_requirements" in context["calculations"]["alternatives"][0]
        if len(calls) == 3:
            assert all(
                any(c["requirement"] == "req-launch" and c["status"] == "pass" for c in r["checks"])
                for r in context["requirement_analysis"]
            )
            assert "B" in context["eligible_ids"]
            payload = dict(
                recommendation="submit",
                selected_id="B",
                rationale="Review recorded mandatory criterion and budgets",
                findings=[
                    dict(
                        severity="advisory",
                        summary="Finite-horizon evidence remains conditional",
                        evidence=["requirement_analysis"],
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
    model = finish(client, model, run_id)
    assert len(calls) == 3
    assert model["entities"][run_id]["data"]["status"] == "awaiting_approval"


def test_workload_bound_marks_access_invalid(monkeypatch):
    def execute(tool, inputs, revision):
        return dict(
            status="valid",
            outputs={"targets": [{"windows": [{}] * 1001}]} if tool == "access" else {},
            errors=[],
        )

    monkeypatch.setattr(alternative_requirements, "execute", execute)
    result = alternative_requirements.geometry(
        dict(inputs={"orbit": {"altitude": {}}}, source_revision=1), 3
    )
    assert result["access"]["status"] == "invalid"
    assert "3,000" in result["access"]["errors"][0]
