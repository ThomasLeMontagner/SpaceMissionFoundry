from copy import deepcopy

import pytest
from test_iteration import edit, select_and_review
from test_workflow import approve, command, to_trade

from app.domain.models import Model
from app.services.requirement_checks import evaluate


def criterion(value=30000, unit="g", operator="<=", metric="mass.total"):
    return dict(metric=metric, operator=operator, threshold=dict(value=value, unit=unit))


def revise(client, model, rule):
    model = edit(client, model, "req-launch", {"criterion": rule})
    model = approve(client, model)
    if model["phase"] == "Impact review":
        model = command(client, model, "review-impact", confirm=True, reason="Reviewed scope")
    return command(client, model, "advance")


def test_requirement_limits_evidence_stale_and_immutable_baseline(client):
    m = revise(client, to_trade(client), criterion())
    key = "check-req-launch-selective"
    check = m["entities"][key]
    assert check["data"]["status"] == "pass"
    assert check["data"]["actual"]["unit"] == "kg"
    assert (
        check["data"]["evidence_revision"] == m["entities"]["selective-mass-analysis"]["revision"]
    )
    assert {r["target"] for r in check["relations"]} == {"req-launch", "selective-mass-analysis"}
    assert m["entities"]["check-req-latency-selective"]["data"]["status"] == "unverified"
    first = command(client, select_and_review(client, m), "baseline", name="Checked", confirm=True)
    url = f"/api/missions/{m['id']}/export/json?baseline_id={first['baseline']}"
    snapshot = client.get(url).json()
    assert (
        "req-latency"
        in snapshot["entities"]["baseline-approval"]["data"]["outstanding_requirements"]
    )
    m = command(client, first, "reopen", reason="Tighten the allocation")
    m = edit(client, m, "req-launch", {"criterion": criterion(1, "kg")})
    m = approve(client, m)
    assert m["entities"][key]["state"] == "stale"
    assert m["entities"][key]["data"]["status"] == "stale"
    m = command(client, m, "advance")
    assert m["entities"][key]["data"]["status"] == "fail"
    response = client.post(
        f"/api/missions/{m['id']}/select",
        json=dict(
            revision=m["revision"],
            candidate="selective",
            weights={"science": 0.35, "capacity": 0.45, "simplicity": 0.2},
            reason="Cannot select",
        ),
    )
    assert response.status_code == 409 and "criterion" in response.text
    assert client.get(url).json() == snapshot
    m = revise(client, m, None)
    assert m["entities"][key]["data"]["status"] == "unverified"
    assert m["entities"][key]["data"]["actual"] is None


@pytest.mark.parametrize(
    "rule",
    [
        criterion(unit="s"),
        criterion(value=-1),
        criterion(value=float("inf")),
        criterion(operator="=="),
        criterion(metric="orbit.latency"),
    ],
)
def test_reject_invalid_criteria(client, rule):
    m = to_trade(client)
    # JSON cannot represent infinity; Pydantic is also tested directly for that case.
    from app.domain.requirement_checks import Criterion

    with pytest.raises(ValueError):
        Criterion.model_validate(rule)
    if rule["threshold"]["value"] != float("inf"):
        response = client.post(
            f"/api/missions/{m['id']}/objects/req-launch/edit",
            json={
                "revision": m["revision"],
                "changes": {"criterion": rule},
                "reason": "Invalid criterion",
            },
        )
        assert response.status_code in [409, 422]
        assert client.get(f"/api/missions/{m['id']}").json()["revision"] == m["revision"]


def test_missing_failed_stale_evidence_and_lower_bound(client):
    m = Model.model_validate(to_trade(client))
    req = m.entities["req-launch"]
    req.data["criterion"] = criterion(0, "Wh", ">=", "power.margin")
    assert evaluate(m, req, "selective").data["status"] == "pass"
    source = m.entities["selective-power-analysis"]
    source.data["outputs"]["margin"]["value"] = -2
    assert evaluate(m, req, "selective").data["status"] == "fail"
    source.state = "stale"
    assert evaluate(m, req, "selective").data["status"] == "stale"
    source.state = "accepted"
    source.data["status"] = "invalid"
    assert evaluate(m, req, "selective").data["status"] == "unverified"
    del m.entities[source.id]
    assert evaluate(m, req, "selective").data["status"] == "unverified"


def test_input_changes_invalidate_requirement_evidence(client):
    m = revise(client, to_trade(client), criterion())
    values = deepcopy(m["entities"]["selective-mass-inputs"]["data"]["inputs"])
    values["entries"][0]["mass"] = {"value": 40, "unit": "kg"}
    m = approve(client, edit(client, m, "selective-mass-inputs", {"inputs": values}))
    assert m["entities"]["check-req-launch-selective"]["data"]["status"] == "stale"
    m = command(client, m, "advance")
    assert m["entities"]["check-req-launch-selective"]["data"]["status"] == "fail"
