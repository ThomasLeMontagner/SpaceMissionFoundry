from copy import deepcopy

import pytest
from test_delivery import fixture
from test_workflow import command, to_ready

from app.domain.models import Model
from app.engineering_tools.calculations import execute
from app.orchestration.scenario import Q, entity
from app.services.sensitivity import Study, study


def model():
    m = Model(name="Sensitivity test", brief="Synthetic delivery workload")
    record = execute("delivery", fixture(), 0)
    m.entities["selective-delivery-analysis"] = entity(
        "selective-delivery-analysis", "AnalysisRun", "Recorded delivery", "tool", **record
    )
    return m


def request(parameter="ground_delay", values=None, **kw):
    return Study(
        revision=0,
        candidate="selective",
        parameter=parameter,
        values=values or [Q(0, "s"), Q(2, "minute")],
        deadline=Q(1, "minute"),
        **kw,
    )


def test_delay_deadlines_and_reference_are_read_only():
    m = model()
    before = m.model_dump()
    result = study(m, request())
    assert result["reference"]["delivery_analysis"]["outputs"]["maximum_latency"] == Q(49, "s")
    a, b = result["trials"]
    assert a["deadline_check"]["status"] == "pass"
    assert b["deadline_check"]["status"] == "fail"
    assert b["delivery_analysis"]["outputs"]["pending_count"] == 1
    assert b["delivery_analysis"]["outputs"]["maximum_latency"] is None
    assert m.model_dump() == before


def test_storage_overflow_and_rf_rate_recomputation():
    storage = study(model(), request("storage", [Q(99, "bit"), Q(100, "bit")]))
    assert storage["trials"][0]["delivery_analysis"]["outputs"]["dropped_count"] == 1
    assert storage["trials"][1]["delivery_analysis"]["outputs"]["delivered_count"] == 1
    rate = study(model(), request("downlink_rate", [Q(10, "bit/s"), Q(1e15, "bit/s")]))
    slow, fast = rate["trials"]
    assert slow["link_analysis"]["outputs"]["link_margin_db"]["value"] > 0
    assert fast["link_analysis"]["outputs"]["link_margin_db"]["value"] < 0
    assert fast["delivery_analysis"]["outputs"]["transmitted"]["value"] == 0


@pytest.mark.parametrize(
    "parameter,values",
    [
        ("storage", [Q(1, "s"), Q(2, "s")]),
        ("ground_delay", [Q(60, "s"), Q(1, "minute")]),
        ("ground_delay", [Q(0, "s"), Q(8, "day")]),
        ("downlink_rate", [Q(0, "bit/s"), Q(1, "bit/s")]),
    ],
)
def test_reject_invalid_or_duplicate_trials(parameter, values):
    with pytest.raises(ValueError):
        study(model(), request(parameter, values))


def test_limits_stale_missing_invalid_and_optional_deadline():
    with pytest.raises(ValueError):
        request(values=[Q(1, "s")])
    with pytest.raises(ValueError):
        request(values=[Q(i, "s") for i in range(16)])
    m = model()
    for state, status in [("stale", "valid"), ("accepted", "invalid")]:
        m.entities["selective-delivery-analysis"].state = state
        m.entities["selective-delivery-analysis"].data["status"] = status
        with pytest.raises(ValueError):
            study(m, request())
    m.entities.clear()
    with pytest.raises(ValueError):
        study(m, request())
    req = request().model_copy(update={"deadline": None})
    assert study(model(), req)["trials"][0]["deadline_check"] is None
    with pytest.raises(ValueError):
        study(model(), request().model_copy(update={"revision": 1}))


def test_baseline_endpoint_preserves_history_and_approved_checks(client):
    m = command(client, to_ready(client), "baseline", name="Sensitivity source", confirm=True)
    base = f"/api/missions/{m['id']}"
    snapshot = client.get(base + "/export/json").json()
    body = dict(
        revision=m["revision"],
        candidate="selective",
        parameter="ground_delay",
        values=[Q(0, "minute"), Q(30, "minute")],
        deadline=Q(30, "minute"),
    )
    response = client.post(base + "/sensitivity", json=body)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["baseline_id"] == m["baseline"]
    assert result["source_revision"] == m["revision"]
    assert client.get(base).json() == m
    assert client.get(base + "/export/json").json() == snapshot
    assert client.post(base + "/sensitivity", json={**body, "revision": 0}).status_code == 409


def test_accepted_criteria_compared_without_rewriting_verification():
    m = model()
    m.entities["deadline"] = entity(
        "deadline",
        "Requirement",
        "Delivery deadline",
        "human",
        rationale="Test",
        source="owner",
        level="system",
        priority="must",
        verification_method="analysis",
        criterion=dict(metric="delivery.maximum_latency", operator="<=", threshold=Q(50, "s")),
    )
    before = deepcopy(m.model_dump())
    result = study(m, request())
    assert result["trials"][0]["requirement_checks"][0]["status"] == "pass"
    assert result["trials"][1]["requirement_checks"][0]["status"] == "fail"
    assert m.model_dump() == before


def test_failed_trial_cannot_report_a_deadline_pass(monkeypatch):
    from app.engineering_tools.calculations import TOOLS

    m = model()

    def fail(_):
        raise ValueError("Controlled calculation failure")

    monkeypatch.setitem(TOOLS, "link", fail)
    result = study(m, request())
    for row in [result["reference"], *result["trials"]]:
        assert row["status"] == "invalid"
        assert row["deadline_check"] is None
        assert row["requirement_checks"] == []


def test_product_case_bound():
    m = model()
    windows = m.entities["selective-delivery-analysis"].data["inputs"]["access"]["targets"][0][
        "windows"
    ]
    windows.extend([deepcopy(windows[0]) for _ in range(17000)])
    with pytest.raises(ValueError, match="50,000"):
        study(m, request())
