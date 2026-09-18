from copy import deepcopy

import pytest
from test_iteration import edit
from test_workflow import approve, command, to_ready, to_trade

from app.domain.engineering_inputs import validate_inputs
from app.engineering_tools.calculations import execute
from app.engineering_tools.delivery import assess_deadline, simulate
from app.orchestration.scenario import Q, inputs


def fixture():
    return dict(
        delays=dict(onboard_delay=Q(0, "s"), ground_delay=Q(2, "s"), dissemination_delay=Q(3, "s")),
        payload=dict(
            rate=Q(10, "bit/s"), duty=Q(1, ""), compression=Q(1, ""), storage=Q(1000, "bit")
        ),
        link={**inputs("selective")["link"], "rate": Q(10, "bit/s"), "efficiency": Q(1, "")},
        link_result=dict(link_margin_db=Q(1, "")),
        access=dict(
            horizon=Q(100, "s"),
            targets=[dict(name="A", windows=[dict(start_s=1, end_s=11)])],
            network_windows=[dict(start_s=20, end_s=25), dict(start_s=40, end_s=50)],
        ),
    )


def test_fragmented_contact_fifo_conservation_and_delays():
    values = fixture()
    before = deepcopy(values)
    output = simulate(values)
    job = output["observations"][0]
    assert job["downlinked_at_s"] == 45
    assert job["delivered_at_s"] == 50
    assert job["latency_s"] == 49
    assert output["produced"]["value"] == output["transmitted"]["value"] == 100
    assert output["queued"]["value"] == 0
    assert assess_deadline(output, 49)["status"] == "pass"
    assert assess_deadline(output, 48)["status"] == "fail"
    assert values == before and simulate(values) == output
    values["access"]["network_windows"].append(dict(start_s=20, end_s=25))
    assert simulate(values) == output
    values["access"]["targets"][0]["windows"].append(dict(start_s=2, end_s=12))
    output = simulate(values)
    assert output["pending_count"] == 1
    assert output["maximum_latency"] is None
    assert output["produced"]["value"] == output["transmitted"]["value"] + output["queued"]["value"]
    assert assess_deadline(output, 200)["status"] == "unverified"
    assert assess_deadline(output, 50)["status"] == "fail"


def test_overflow_rf_failure_no_observations_and_truncation():
    values = fixture()
    values["payload"]["storage"] = Q(99, "bit")
    output = simulate(values)
    assert output["dropped_count"] == 1
    assert output["dropped"]["value"] == output["produced"]["value"]
    assert assess_deadline(output, 1000)["status"] == "fail"
    values = fixture()
    values["link_result"]["link_margin_db"] = Q(-1, "")
    assert simulate(values)["transmitted"]["value"] == 0
    values = fixture()
    values["access"]["targets"][0]["windows"][0]["boundary_truncated"] = True
    assert assess_deadline(simulate(values), 1000)["status"] == "unverified"
    values["access"]["targets"] = []
    assert assess_deadline(simulate(values), 1000)["status"] == "unverified"


def test_processing_and_readiness_horizon_and_units():
    values = fixture()
    values["delays"]["ground_delay"] = Q(2, "minute")
    output = simulate(values)
    assert output["observations"][0]["status"] == "ground_processing"
    assert output["delivered_count"] == 0
    assert assess_deadline(output, 100)["status"] == "unverified"
    assert assess_deadline(output, 90)["status"] == "fail"
    values["delays"]["onboard_delay"] = Q(1, "minute")
    assert simulate(values)["transmitted"]["value"] == 0
    values["delays"]["onboard_delay"] = Q(1, "kg")
    assert execute("delivery", values, 1)["status"] == "invalid"
    with pytest.raises(ValueError):
        validate_inputs("delivery", {**fixture()["delays"], "ground_delay": Q(8, "day")})


def test_delivery_workflow_deadline_staleness_and_failure(client, monkeypatch):
    from app.engineering_tools.calculations import TOOLS

    m = to_trade(client)
    run = m["entities"]["selective-delivery-analysis"]
    assert run["data"]["status"] == "valid", run["data"]["errors"]
    assert "ground_track" not in run["data"]["inputs"]["access"]
    m = approve(
        client,
        edit(
            client,
            m,
            "req-latency",
            {
                "criterion": dict(
                    metric="delivery.maximum_latency", operator="<=", threshold=Q(0, "minute")
                )
            },
        ),
    )
    if m["phase"] == "Impact review":
        m = command(
            client, m, "review-impact", confirm=True, reason="Reviewed latency dependencies"
        )
    m = command(client, m, "advance")
    check = m["entities"]["check-req-latency-selective"]["data"]
    assert check["status"] == "fail"
    response = client.post(
        f"/api/missions/{m['id']}/select",
        json=dict(
            revision=m["revision"],
            candidate="selective",
            weights={"science": 0.35, "capacity": 0.45, "simplicity": 0.2},
            reason="Test deadline guard",
        ),
    )
    assert response.status_code == 409 and "criterion" in response.text
    values = deepcopy(m["entities"]["selective-delivery-inputs"]["data"]["inputs"])
    values["ground_delay"] = Q(3, "minute")
    m = approve(client, edit(client, m, "selective-delivery-inputs", {"inputs": values}))
    assert m["entities"]["check-req-latency-selective"]["data"]["status"] == "stale"

    def fail(_):
        raise ValueError("Controlled delivery failure")

    monkeypatch.setitem(TOOLS, "delivery", fail)
    m = command(client, m, "advance")
    assert m["entities"]["selective-delivery-analysis"]["data"]["status"] == "invalid"
    assert m["entities"]["check-req-latency-selective"]["data"]["status"] == "unverified"


def test_legacy_delivery_requires_approval(client):
    m = to_trade(client)
    store = client.app.state.store
    old = store.get(m["id"])
    legacy = old.model_copy(deep=True)
    removed = {k for k in legacy.entities if "-delivery-" in k}
    legacy.entities = {k: e for k, e in legacy.entities.items() if k not in removed}
    for e in legacy.entities.values():
        e.relations = [r for r in e.relations if r.target not in removed]
    m = store.save(legacy, "test", "Simulate pre-delivery snapshot", old).model_dump()
    m = command(client, m, "initialize-delivery")
    assert "selective-delivery-inputs" not in m["entities"]
    m = command(client, approve(client, m), "advance")
    assert m["entities"]["selective-delivery-analysis"]["data"]["status"] == "valid"


def test_delivery_edit_invalidates_selection_and_preserves_baseline(client):
    m = command(client, to_ready(client), "baseline", name="Delivery baseline", confirm=True)
    url = f"/api/missions/{m['id']}/export/json?baseline_id={m['baseline']}"
    snapshot = client.get(url).json()
    m = command(client, m, "reopen", reason="Revise delivery assumptions")
    values = deepcopy(m["entities"]["selective-delivery-inputs"]["data"]["inputs"])
    values["ground_delay"] = Q(5, "minute")
    m = approve(client, edit(client, m, "selective-delivery-inputs", {"inputs": values}))
    assert m["entities"]["selection"]["state"] == "stale"
    assert m["entities"]["selective-delivery-analysis"]["state"] == "stale"
    m = command(client, m, "advance")
    assert m["entities"]["selective-delivery-analysis"]["data"]["inputs"]["delays"][
        "ground_delay"
    ] == Q(5, "minute")
    assert client.get(url).json() == snapshot
