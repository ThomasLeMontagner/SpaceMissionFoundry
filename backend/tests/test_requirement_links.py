from copy import deepcopy

import pytest
from test_workflow import approve, command, to_trade

from app.domain.models import Model, Operation, Proposal, Relation
from app.domain.protocol import validate
from app.services.design_inputs import EditChanges, edited_entity


def propose(client, m, parents):
    return client.post(
        f"/api/missions/{m['id']}/objects/req-latency/edit",
        json=dict(
            revision=m["revision"],
            changes=dict(parent_ids=parents),
            reason="Trace latency to its observation need",
        ),
    )


def test_parent_edit_is_reviewed_preserves_data_and_recalculates(client):
    m = to_trade(client)
    original = deepcopy(m["entities"]["req-latency"])
    before_revision = m["revision"]
    response = propose(client, m, ["req-observe"])
    assert response.status_code == 200, response.text
    m = response.json()
    assert m["entities"]["req-latency"] == original
    m = approve(client, m)
    changed = m["entities"]["req-latency"]
    assert changed["title"] == original["title"]
    assert changed["data"].get("criterion") == original["data"].get("criterion")
    assert changed["data"]["formalization"]["coverage"] == "partial"
    assert changed["relations"] == [dict(type="derives_from", target="req-observe")]
    assert m["phase"] in {"Impact review", "Recalculation required"}
    historical = client.get(f"/api/missions/{m['id']}/revisions/{before_revision}")
    assert historical.status_code == 200
    assert historical.json()["entities"]["req-latency"] == original


@pytest.mark.parametrize(
    "parents", [["req-latency"], ["resources"], ["missing"], ["objective", "objective"], []]
)
def test_invalid_parent_requests_do_not_mutate(client, parents):
    m = to_trade(client)
    assert propose(client, m, parents).status_code in {409, 422}
    assert client.get(f"/api/missions/{m['id']}").json() == m


@pytest.mark.parametrize("action", ["reject", "challenge"])
def test_unapproved_links_remain_unchanged(client, action):
    m = to_trade(client)
    original = deepcopy(m["entities"]["req-latency"])
    m = propose(client, m, ["req-observe"]).json()
    p = next(p for p in m["proposals"].values() if p["status"] == "submitted")
    m = command(
        client,
        m,
        f"proposals/{p['id']}/decision",
        action=action,
        reason="Review parent applicability",
    )
    assert m["entities"]["req-latency"] == original


def test_whole_proposal_graph_and_approval_revalidation(client):
    model = Model.model_validate(to_trade(client))
    a, b = model.entities["req-observe"], model.entities["req-latency"]

    def proposal(entities):
        return Proposal(
            agent="human",
            proposal_type="design change",
            target_revision=model.revision,
            operations=[Operation(action="replace", entity=e) for e in entities],
            rationale="Review links",
            expected_consequences="Reassess scope",
            confidence=1,
        )

    ea = edited_entity(a, EditChanges(parent_ids=[b.id]))
    eb = edited_entity(b, EditChanges(parent_ids=[a.id]))
    with pytest.raises(ValueError, match="circular"):
        validate(model, proposal([ea, eb]))
    p = proposal([eb])
    validate(model, p)
    model.entities[a.id].relations = [Relation(type="derives_from", target=b.id)]
    with pytest.raises(ValueError, match="circular"):
        validate(model, p)
    model.entities[a.id].relations = []
    model.entities[a.id].state = "rejected"
    with pytest.raises(ValueError, match="accepted or stale"):
        validate(model, p)


def test_preserves_provenance_and_requires_scope_reassessment(client):
    model = Model.model_validate(to_trade(client))
    old = model.entities["req-latency"]
    old.relations.append(Relation(type="evidenced_by", target="objective"))
    old.data["decomposition"] = {"parent_id": "objective", "run_id": "historical-run"}
    updated = edited_entity(old, EditChanges(parent_ids=["req-observe"]))
    assert old.data["decomposition"] == updated.data["decomposition"]
    assert Relation(type="evidenced_by", target="objective") in updated.relations
    assert updated.data["formalization"]["open_questions"]
    updated.data.pop("formalization")
    p = Proposal(
        agent="human",
        proposal_type="design change",
        target_revision=model.revision,
        operations=[Operation(action="replace", entity=updated)],
        rationale="Change links",
        expected_consequences="Review applicability",
        confidence=1,
    )
    with pytest.raises(ValueError, match="partial scope"):
        validate(model, p)
    with pytest.raises(ValueError, match="No design changes"):
        edited_entity(old, EditChanges(parent_ids=["objective"]))
