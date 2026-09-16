import math
from copy import deepcopy

import pytest
from test_iteration import edit
from test_workflow import approve, command, to_ready, to_trade

from app.domain.engineering_inputs import validate_inputs
from app.engineering_tools.access import MU, RADIUS, ROTATION, elevation, position
from app.engineering_tools.calculations import execute
from app.services.design_inputs import access_values


def equatorial():
    inputs = access_values()
    inputs.update(
        altitude={"value": 550, "unit": "km"},
        inclination={"value": 0, "unit": "deg"},
        duration={"value": 1500, "unit": "s"},
        step={"value": 1, "unit": "s"},
        minimum_elevation={"value": 0, "unit": "deg"},
    )
    site = dict(
        name="Equator", latitude={"value": 0, "unit": "deg"}, longitude={"value": 0, "unit": "deg"}
    )
    inputs["targets"] = [site]
    inputs["stations"] = [deepcopy(site)]
    return inputs


def result(inputs):
    run = execute("access", inputs, 7)
    assert run["status"] == "valid", run["errors"]
    return run["outputs"]


def test_position_and_elevation_against_analytic_geometry():
    radius = RADIUS + 550000
    assert position(0, radius, 0, 0, 0, 0) == (radius, 0, 0)
    assert elevation((radius, 0, 0), (1, 0, 0)) == pytest.approx(math.pi / 2)
    central = math.acos(RADIUS / radius)
    assert elevation(
        (radius * math.cos(central), radius * math.sin(central), 0), (1, 0, 0)
    ) == pytest.approx(0, abs=1e-12)
    assert elevation((-radius, 0, 0), (1, 0, 0)) < 0
    period = 2 * math.pi / math.sqrt(MU / radius**3)
    xyz = position(period, radius, 0, 0, 0, 0)
    assert math.sqrt(sum(v * v for v in xyz)) == pytest.approx(radius)
    assert math.atan2(xyz[1], xyz[0]) == pytest.approx(-ROTATION * period)
    polar = position(period / 4, radius, math.pi / 2, 0, 0, 0)
    assert polar[2] == pytest.approx(radius)


def test_equatorial_horizon_crossing_union_and_determinism():
    inputs = equatorial()
    before = deepcopy(inputs)
    output = result(inputs)
    radius = RADIUS + 550000
    crossing = math.acos(RADIUS / radius) / (math.sqrt(MU / radius**3) - ROTATION)
    event = output["network_windows"][0]
    assert event["start_s"] == 0 and event["boundary_truncated"]
    assert abs(event["end_s"] - crossing) <= 1
    assert output["targets"][0]["max_observed_revisit"] is None
    assert output["opportunity_wait"]["value"] == 0
    assert output == result(inputs) and inputs == before
    inputs["stations"].append({**inputs["stations"][0], "name": "Co-located station"})
    assert result(inputs)["contact"] == output["contact"]
    inputs["minimum_elevation"] = {"value": 20, "unit": "deg"}
    assert result(inputs)["contact"]["value"] < output["contact"]["value"]


def test_no_access_and_sampling_refinement():
    inputs = equatorial()
    inputs["targets"][0]["latitude"]["value"] = 90
    inputs["stations"][0]["latitude"]["value"] = 90
    output = result(inputs)
    assert output["observed_fraction"]["value"] == 0
    assert output["contact"]["value"] == 0
    assert output["largest_target_gap"]["value"] == 1500
    assert output["opportunity_wait"] is None
    inputs["targets"][0]["latitude"]["value"] = 0
    waiting = result(inputs)
    assert waiting["observations_without_later_contact"] > 0
    assert waiting["opportunity_wait"] is None
    inputs = equatorial()
    coarse = result({**inputs, "step": {"value": 20, "unit": "s"}})
    fine = result(inputs)
    assert abs(coarse["contact"]["value"] - fine["contact"]["value"]) <= 20
    radians = deepcopy(inputs)
    radians["inclination"] = {"value": 0, "unit": "rad"}
    radians["duration"] = {"value": 25, "unit": "minute"}
    assert result(radians)["contact"] == fine["contact"]


def test_equatorial_revisit_matches_relative_rotation_period():
    inputs = equatorial()
    inputs["duration"] = {"value": 15000, "unit": "s"}
    output = result(inputs)
    relative_period = 2 * math.pi / (math.sqrt(MU / (RADIUS + 550000) ** 3) - ROTATION)
    assert output["targets"][0]["max_observed_revisit"]["value"] == pytest.approx(
        relative_period, abs=2
    )


@pytest.mark.parametrize(
    "key,value",
    [
        ("step", {"value": 0, "unit": "s"}),
        ("duration", {"value": 8, "unit": "day"}),
        ("footprint_width", {"value": 100, "unit": "W"}),
        ("inclination", {"value": 181, "unit": "deg"}),
        ("minimum_elevation", {"value": -1, "unit": "deg"}),
    ],
)
def test_invalid_inputs(key, value):
    values = access_values()
    values[key] = value
    with pytest.raises(ValueError):
        validate_inputs("access", values)


def test_invalid_sites_work_limit_and_derived_altitude():
    values = access_values()
    values["stations"][0]["longitude"]["value"] = -181
    with pytest.raises(ValueError):
        validate_inputs("access", values)
    values = access_values()
    values["duration"] = {"value": 7, "unit": "day"}
    values["step"] = {"value": 1, "unit": "s"}
    with pytest.raises(ValueError):
        validate_inputs("access", values)
    values = access_values()
    values["altitude"] = {"value": 550, "unit": "km"}
    with pytest.raises(ValueError):
        validate_inputs("access", values)
    values["altitude"]["value"] = 0
    assert execute("access", values, 1)["status"] == "invalid"


def test_access_edit_stale_checks_recalculation_and_baseline_preservation(client):
    first = command(client, to_ready(client), "baseline", name="Coverage baseline", confirm=True)
    base = f"/api/missions/{first['id']}"
    original = client.get(base + "/export/json").json()
    m = command(client, first, "reopen", reason="Test inclination change")
    values = deepcopy(m["entities"]["mission-access-inputs"]["data"]["inputs"])
    values["inclination"] = {"value": 0, "unit": "deg"}
    m = approve(client, edit(client, m, "mission-access-inputs", {"inputs": values}))
    assert m["entities"]["mission-access-analysis"]["state"] == "stale"
    assert m["entities"]["selection"]["state"] == "stale"
    m = command(client, m, "advance")
    assert (
        m["entities"]["mission-access-analysis"]["data"]["outputs"]["observed_fraction"]["value"]
        == 0
    )
    assert m["entities"]["check-req-latency-selective"]["data"]["status"] == "unverified"
    assert client.get(base + "/export/json?baseline_id=" + first["baseline"]).json() == original


def test_legacy_access_enable_requires_approval(client):
    m = to_trade(client)
    store = client.app.state.store
    old = store.get(m["id"])
    legacy = old.model_copy(deep=True)
    removed = {key for key in legacy.entities if key.startswith("mission-access-")}
    legacy.entities = {key: e for key, e in legacy.entities.items() if key not in removed}
    for e in legacy.entities.values():
        e.relations = [r for r in e.relations if r.target not in removed]
    m = store.save(legacy, "test", "Simulate pre-access snapshot", old).model_dump()
    m = command(client, m, "initialize-access")
    assert "mission-access-inputs" not in m["entities"]
    m = approve(client, m)
    assert m["phase"] == "Recalculation required"
    m = command(client, m, "advance")
    assert m["entities"]["mission-access-analysis"]["data"]["status"] == "valid"


def test_access_criteria_use_shared_evidence_and_failed_runs_are_unverified(client, monkeypatch):
    from app.engineering_tools.calculations import TOOLS

    m = to_trade(client)
    rule = {
        "metric": "access.contact",
        "operator": ">=",
        "threshold": {"value": 0, "unit": "minute"},
    }
    m = approve(client, edit(client, m, "req-launch", {"criterion": rule}))
    m = command(client, m, "advance")
    for candidate in ["wide", "selective"]:
        check = m["entities"][f"check-req-launch-{candidate}"]
        assert check["data"]["status"] == "pass"
        assert any(r["target"] == "mission-access-analysis" for r in check["relations"])

    def fail(_):
        raise ValueError("Controlled access failure")

    monkeypatch.setitem(TOOLS, "access", fail)
    values = deepcopy(m["entities"]["mission-access-inputs"]["data"]["inputs"])
    values["step"] = {"value": 20, "unit": "s"}
    m = approve(client, edit(client, m, "mission-access-inputs", {"inputs": values}))
    assert m["entities"]["check-req-launch-selective"]["data"]["status"] == "stale"
    m = command(client, m, "advance")
    assert m["entities"]["mission-access-analysis"]["data"]["status"] == "invalid"
    assert m["entities"]["check-req-launch-selective"]["data"]["status"] == "unverified"
