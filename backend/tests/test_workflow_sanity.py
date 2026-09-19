from copy import deepcopy

import pytest
from test_iteration import edit
from test_workflow import approve, command, create, to_ready, to_trade

from app.domain.models import Model, Operation, Proposal
from app.orchestration.scenario import architectures, entity
from app.services.interface_checks import evaluate, guard_interfaces


def proposal(m, e, kind="custom", action="replace", agent="systems"):
    return Proposal(
        proposal_type=kind,
        agent=agent,
        target_revision=m["revision"],
        operations=[Operation(action=action, entity=e)],
        rationale="Review changed design content",
        expected_consequences="Review affected objects and recalculate",
        confidence=0.8,
    ).model_dump(mode="json")


def test_selection_preserves_pending_edit_for_approval(client):
    m = to_trade(client)
    values = deepcopy(m["entities"]["selective-data-inputs"]["data"]["inputs"])
    values["duty"]["value"] = 0.1
    m = edit(client, m, "selective-data-inputs", {"inputs": values})
    root = f"/api/missions/{m['id']}"
    response = client.post(
        root + "/select",
        json=dict(
            revision=m["revision"],
            candidate="selective",
            weights={"science": 0.35, "capacity": 0.45, "simplicity": 0.2},
            reason="Select before resolving the pending change",
        ),
    )
    assert response.status_code == 409 and "pending proposals" in response.text
    assert client.get(root).json() == m
    m = approve(client, m)
    assert m["phase"] == "Recalculation required"
    m = command(client, m, "advance")
    assert not m["entities"]["selective-link"]["data"]["compliant"]


def test_custom_component_replacement_requires_impact_review(client):
    m = to_ready(client)
    root = f"/api/missions/{m['id']}"
    e = Model.model_validate(m).entities["imager"].model_copy(deep=True)
    e.owner = "systems"
    e.title = "Revised payload component"
    response = client.post(root + "/proposals", json=proposal(m, e))
    assert response.status_code == 200, response.text
    m = approve(client, response.json())
    assert m["phase"] == "Impact review"
    assert m["entities"]["selection"]["state"] == "stale"
    m = command(client, m, "review-impact", reason="Reaffirm affected interfaces", confirm=True)
    assert m["phase"] == "Recalculation required"
    m = command(client, m, "advance")
    assert m["phase"] == "Trade study" and m["selected"] is None
    assert m["entities"]["selection"]["state"] == "superseded"


@pytest.mark.parametrize(
    "kind", ["assumptions", "requirements", "architectures", "calculation inputs"]
)
def test_mislabeled_stage_proposals_rejected_without_mutation(client, kind):
    m = to_trade(client)
    root = f"/api/missions/{m['id']}"
    e = entity("extra-component", "Component", "Additional component")
    response = client.post(root + "/proposals", json=proposal(m, e, kind, "add"))
    assert response.status_code == 409
    assert client.get(root).json() == m


def test_stage_contents_validated_even_in_matching_phase(client):
    m = create(client)
    # This is an allowed science object, but cannot stand in for an assumptions proposal.
    e = entity("extra-objective", "Objective", "Additional objective", owner="science")
    response = client.post(
        f"/api/missions/{m['id']}/proposals",
        json=proposal(m, e, "assumptions", "add", "science"),
    )
    assert response.status_code == 409


@pytest.mark.parametrize(
    "endpoints",
    [
        None,
        "imager",
        [None, "bus-component"],
        [{"id": "imager"}, "bus-component"],
        ["", "bus-component"],
    ],
)
def test_malformed_interface_rejected_and_legacy_evidence_fails(client, endpoints):
    m = to_trade(client)
    root = f"/api/missions/{m['id']}"
    e = Model.model_validate(m).entities["interface"].model_copy(deep=True)
    e.owner = "systems"
    e.data["endpoints"] = endpoints
    response = client.post(root + "/proposals", json=proposal(m, e))
    assert response.status_code == 409 and "endpoints" in response.text
    assert client.get(root).json() == m
    legacy = Model(
        name="Legacy",
        brief="Malformed legacy interface",
        entities={e.id: e for e in architectures()},
    )
    legacy.entities["interface"].data["endpoints"] = endpoints
    check = evaluate(legacy, legacy.entities["interface"])
    assert check.data["status"] == "fail"
    assert check.data["inputs"]["endpoints"] == endpoints
    with pytest.raises(ValueError, match="is fail"):
        guard_interfaces(legacy)
