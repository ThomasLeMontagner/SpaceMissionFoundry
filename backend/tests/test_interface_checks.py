from copy import deepcopy

import pytest
from test_iteration import edit
from test_workflow import approve, command, to_ready, to_trade

from app.domain.interfaces import DataContract
from app.domain.models import Model
from app.domain.protocol import invalidate_dependents
from app.orchestration.scenario import Q, architectures
from app.services.interface_checks import evaluate, guard_interfaces, refresh_interfaces


def contract(**changes):
    return dict(
        source_endpoint="imager",
        sink_endpoint="bus-component",
        source_protocol="SpaceWire",
        sink_protocol="spacewire",
        source_rate=Q(20, "Mbit/s"),
        sink_capacity=Q(20000, "kbit/s"),
        **changes,
    )


def model():
    return Model(
        name="Interfaces",
        brief="Synthetic interface test",
        entities={e.id: e for e in architectures()},
    )


def test_missing_contract_units_protocol_rate_direction_and_states():
    m = model()
    interface = m.entities["interface"]
    assert evaluate(m, interface).data["status"] == "unverified"
    interface.data["data_contract"] = contract()
    assert evaluate(m, interface).data["status"] == "pass"
    interface.data["data_contract"]["sink_capacity"] = Q(19, "Mbit/s")
    assert evaluate(m, interface).data["status"] == "fail"
    interface.data["data_contract"] = {**contract(), "sink_protocol": "CAN"}
    assert evaluate(m, interface).data["status"] == "fail"
    interface.data["data_contract"] = {**contract(), "sink_protocol": None}
    assert evaluate(m, interface).data["status"] == "unverified"
    interface.data["data_contract"] = {**contract(), "sink_capacity": None}
    assert evaluate(m, interface).data["status"] == "unverified"
    interface.data["data_contract"] = {**contract(), "sink_endpoint": "imager"}
    assert evaluate(m, interface).data["status"] == "fail"
    interface.data["data_contract"] = contract()
    refresh_interfaces(m)
    invalidate_dependents(m, {"imager"})
    assert m.entities["interface-check-interface"].state == "stale"
    assert m.entities["interface-check-interface"].data["status"] == "stale"
    with pytest.raises(ValueError, match="stale"):
        guard_interfaces(m)


def test_missing_wrong_endpoints_and_invalid_rate_units():
    m = model()
    interface = m.entities["interface"]
    interface.data["data_contract"] = contract()
    del m.entities["imager"]
    assert evaluate(m, interface).data["status"] == "fail"
    m = model()
    m.entities["imager"].state = "proposed"
    assert evaluate(m, m.entities["interface"]).data["status"] == "unverified"
    for rate in [Q(20, "W"), Q(-1, "bit/s")]:
        with pytest.raises(ValueError):
            DataContract.model_validate({**contract(), "source_rate": rate})


def test_reviewed_contract_failure_guard_correction_and_baseline(client):
    m = to_trade(client)
    assert m["entities"]["interface-check-interface"]["data"]["status"] == "unverified"
    before = deepcopy(m["entities"]["interface"])
    m = edit(
        client, m, "interface", {"data_contract": {**contract(), "sink_capacity": Q(10, "Mbit/s")}}
    )
    assert m["entities"]["interface"] == before
    m = approve(client, m)
    assert m["entities"]["interface-check-interface"]["state"] == "stale"
    m = command(client, m, "advance")
    assert m["entities"]["interface-check-interface"]["data"]["status"] == "fail"
    response = client.post(
        f"/api/missions/{m['id']}/select",
        json=dict(
            revision=m["revision"],
            candidate="selective",
            weights={"science": 0.35, "capacity": 0.45, "simplicity": 0.2},
            reason="Cannot select a mismatched interface",
        ),
    )
    assert response.status_code == 409 and "Interface" in response.text
    m = command(
        client,
        approve(client, edit(client, m, "interface", {"data_contract": contract()})),
        "advance",
    )
    assert m["entities"]["interface-check-interface"]["data"]["status"] == "pass"
    m = command(
        client,
        m,
        "select",
        candidate="selective",
        weights={"science": 0.35, "capacity": 0.45, "simplicity": 0.2},
        reason="Declared contract checks pass",
    )
    for _ in range(3):
        m = command(client, m, "advance")
    m = command(client, m, "baseline", name="Interface checked", confirm=True)
    base = f"/api/missions/{m['id']}"
    snapshot = client.get(base + "/export/json").json()
    m = command(client, m, "reopen", reason="Remove an unsupported contract")
    m = approve(client, edit(client, m, "interface", {"data_contract": None}))
    assert m["entities"]["selection"]["state"] == "stale"
    m = command(client, m, "advance")
    assert m["entities"]["interface-check-interface"]["data"]["status"] == "unverified"
    assert client.get(base + "/export/json?baseline_id=" + snapshot["baseline"]).json() == snapshot


def test_unknown_interfaces_remain_outstanding_on_concept_baseline(client):
    m = command(client, to_ready(client), "baseline", name="Unverified interfaces", confirm=True)
    assert m["entities"]["baseline-approval"]["data"]["outstanding_interfaces"] == ["interface"]
