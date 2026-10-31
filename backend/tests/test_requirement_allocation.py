from copy import deepcopy

import pytest
from test_workflow import approve, command, to_ready, to_trade

from app.domain.models import Model, Proposal, Relation
from app.domain.protocol import invalidate_dependents, validate
from app.domain.requirement_quality import report
from app.services.design_inputs import EditChanges, edited_entity


def propose(client, m, targets, key="req-observe"):
    return client.post(
        f"/api/missions/{m['id']}/objects/{key}/edit",
        json=dict(
            revision=m["revision"],
            changes=dict(allocation_ids=targets),
            reason="Assign observation responsibility to architecture",
        ),
    )


def pending(m):
    return next(p for p in m["proposals"].values() if p["status"] == "submitted")


def test_allocation_approval_and_removal_preserve_history(client):
    m = to_trade(client)
    before = deepcopy(m)
    response = propose(client, m, ["detect", "imager"])
    assert response.status_code == 200, response.text
    proposed = response.json()
    assert proposed["entities"] == before["entities"]
    m = approve(client, proposed)
    req = m["entities"]["req-observe"]
    assert req["title"] == before["entities"]["req-observe"]["title"]
    assert req["data"]["formalization"]["coverage"] == "partial"
    assert {r["target"] for r in req["relations"] if r["type"] == "allocated_to"} == {
        "detect",
        "imager",
    }
    assert {r["target"] for r in req["relations"] if r["type"] == "derives_from"} == {"objective"}
    assert m["phase"] == "Impact review"
    assert m["entities"]["imager"]["state"] == "stale"
    assert any(
        f["code"] == "stale_allocation" and f["requirement_id"] == "req-observe"
        for f in report(Model.model_validate(m))["findings"]
    )
    m = command(
        client,
        m,
        "review-impact",
        confirm=True,
        reason="Review function and component responsibility",
    )
    m = command(client, m, "advance")
    assert m["entities"]["check-req-observe-selective"]["data"]["status"] == "unverified"
    m = approve(client, propose(client, m, []).json())
    assert not any(r["type"] == "allocated_to" for r in m["entities"]["req-observe"]["relations"])
    historical = client.get(f"/api/missions/{m['id']}/revisions/{before['revision']}").json()
    assert historical == before


@pytest.mark.parametrize(
    "targets",
    [["missing"], ["objective"], ["req-observe"], ["detect", "detect"], [""], ["imager"] * 21],
)
def test_invalid_allocations_are_atomic(client, targets):
    m = to_trade(client)
    assert propose(client, m, targets).status_code in {409, 422}
    assert client.get(f"/api/missions/{m['id']}").json() == m


@pytest.mark.parametrize("action", ["reject", "challenge"])
def test_unapproved_allocations_leave_requirement_unchanged(client, action):
    m = to_trade(client)
    original = deepcopy(m["entities"])
    proposed = propose(client, m, ["detect"]).json()
    p = pending(proposed)
    result = command(
        client,
        proposed,
        f"proposals/{p['id']}/decision",
        action=action,
        reason="Responsibility needs review",
    )
    assert all(result["entities"][key] == value for key, value in original.items())


def test_acceptance_revalidates_targets_and_partial_scope(client):
    m = to_trade(client)
    proposed = propose(client, m, ["imager"]).json()
    model = Model.model_validate(proposed)
    p = Proposal.model_validate(pending(proposed))
    model.entities["imager"].state = "rejected"
    with pytest.raises(ValueError, match="active accepted or stale"):
        validate(model, p)
    model.entities["imager"].state = "accepted"
    p.operations[0].entity.data.pop("formalization")
    with pytest.raises(ValueError, match="partial scope"):
        validate(model, p)


def test_target_changes_invalidate_allocated_requirement_and_preserve_provenance(client):
    m = Model.model_validate(to_trade(client))
    prior = m.entities["req-cost"]
    prior.data["decomposition"] = {"parent_id": "objective", "run_id": "historical"}
    changed = edited_entity(prior, EditChanges(allocation_ids=["imager"]))
    assert changed.data["decomposition"] == prior.data["decomposition"]
    m.entities[prior.id] = changed
    m.entities[prior.id].state = "accepted"
    invalidate_dependents(m, {"imager"})
    assert m.entities[prior.id].state == "stale"
    with pytest.raises(ValueError, match="No design changes"):
        edited_entity(changed, EditChanges(allocation_ids=["imager"]))


def test_baseline_allocation_guard_and_immutable_export(client):
    m = command(client, to_ready(client), "baseline", name="Before allocations", confirm=True)
    root = f"/api/missions/{m['id']}"
    snapshot = client.get(root + "/export/json").json()
    assert propose(client, m, ["imager"]).status_code == 409
    reopened = command(client, m, "reopen", reason="Review requirement responsibility")
    approve(client, propose(client, reopened, ["imager"]).json())
    assert client.get(root + f"/export/json?baseline_id={m['baseline']}").json() == snapshot


def test_quality_flags_missing_allocation_and_invalid_targets(client):
    model = Model.model_validate(to_trade(client))

    def codes():
        return {
            f["code"] for f in report(model)["findings"] if f["requirement_id"] == "req-observe"
        }

    assert "unallocated_requirement" in codes()
    model.entities["req-observe"].relations.append(Relation(type="allocated_to", target="missing"))
    assert "invalid_allocation" in codes()
    model.entities["req-observe"].relations[-1] = Relation(type="allocated_to", target="imager")
    assert "invalid_allocation" not in codes()
    assert "unallocated_requirement" not in codes()
    model.entities["imager"].state = "rejected"
    assert "invalid_allocation" in codes()
