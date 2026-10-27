from copy import deepcopy

import pytest
from test_workflow import approve, command, create, to_ready, to_trade

from app.domain.models import Model, Proposal
from app.domain.protocol import validate


def ready(client):
    return approve(client, command(client, approve(client, create(client)), "advance"))


def draft(**values):
    return dict(
        statement="The mission shall provide a daily observation report.",
        rationale="Support owner operations planning",
        source="Owner operations need, 2026-10-27",
        level="system",
        priority="must",
        verification_method="review",
        parent_ids=["objective"],
        **values,
    )


def submit(client, model, body=None):
    return client.post(
        f"/api/missions/{model['id']}/requirements",
        json={"revision": model["revision"], **(body or draft())},
    )


def pending(model):
    return next(p for p in model["proposals"].values() if p["status"] == "submitted")


def test_creation_approval_and_history(client):
    model = ready(client)
    original = deepcopy(model)
    response = submit(client, model)
    assert response.status_code == 200, response.text
    proposed = response.json()
    item = pending(proposed)["operations"][0]["entity"]
    key = item["id"]
    assert key not in proposed["entities"]
    assert proposed["entities"] == original["entities"]
    assert item["classification"] == "Explicit assumption"
    assert item["data"]["source"] == draft()["source"]
    accepted = approve(client, proposed)
    assert accepted["entities"][key]["state"] == "accepted"
    assert accepted["entities"][key]["data"]["criterion"] is None
    assert accepted["entities"][key]["data"]["formalization"]["coverage"] == "partial"
    assert accepted["entities"][key]["relations"] == [dict(type="derives_from", target="objective")]
    assert accepted["phase"] == "Requirements approved"
    historical = client.get(f"/api/missions/{model['id']}/revisions/{original['revision']}").json()
    assert historical == original
    assert (
        client.get(f"/api/missions/{model['id']}").json()["entities"][key]
        == accepted["entities"][key]
    )


@pytest.mark.parametrize("action", ["reject", "challenge"])
def test_unapproved_creation_does_not_add_requirement(client, action):
    model = ready(client)
    proposed = submit(client, model).json()
    p = pending(proposed)
    result = command(
        client,
        proposed,
        f"proposals/{p['id']}/decision",
        action=action,
        reason="Owner requests further clarification",
    )
    assert p["operations"][0]["entity"]["id"] not in result["entities"]
    assert all(result["entities"][key] == value for key, value in model["entities"].items())


@pytest.mark.parametrize(
    "changes",
    [
        {"statement": "   "},
        {"source": " "},
        {"rationale": " "},
        {"parent_ids": []},
        {"parent_ids": ["objective", "objective"]},
        {"parent_ids": ["missing"]},
        {"parent_ids": ["resources"]},
        {"criterion": {}},
        {"priority": "critical"},
    ],
)
def test_invalid_creation_is_atomic(client, changes):
    model = ready(client)
    assert submit(client, model, {**draft(), **changes}).status_code in {409, 422}
    assert client.get(f"/api/missions/{model['id']}").json() == model


def test_creation_guards_and_parent_revalidation(client):
    model = ready(client)
    assert submit(client, model, {**draft(), "revision": model["revision"] - 1}).status_code == 409
    proposed = submit(client, model).json()
    assert submit(client, proposed).status_code == 409
    p = Proposal.model_validate(pending(proposed))
    source = Model.model_validate(proposed)
    source.entities["objective"].state = "rejected"
    with pytest.raises(ValueError, match="accepted or stale"):
        validate(source, p)
    source.entities["objective"].state = "accepted"
    p.operations[0].entity.data["formalization"]["coverage"] = "full"
    with pytest.raises(ValueError, match="unverified draft"):
        validate(source, p)
    # Public mutation guards are shared with existing baseline and archive tests.
    archived = command(client, proposed, "archive", archived=True)
    assert submit(client, archived).status_code == 409


def test_new_requirement_invalidates_selection_and_stays_unverified_after_recalculation(client):
    model = to_trade(client)
    model = command(
        client,
        model,
        "select",
        candidate="selective",
        weights={"science": 0.35, "capacity": 0.45, "simplicity": 0.2},
        reason="Owner selects reference concept",
    )
    proposed = submit(client, model).json()
    key = pending(proposed)["operations"][0]["entity"]["id"]
    accepted = approve(client, proposed)
    assert accepted["selected"] is None
    assert accepted["entities"]["selection"]["state"] == "stale"
    assert accepted["phase"] == "Recalculation required"
    calculated = command(client, accepted, "advance")
    for candidate in ["wide", "selective"]:
        assert calculated["entities"][f"check-{key}-{candidate}"]["data"]["status"] == "unverified"
    assert calculated["phase"] == "Trade study"


def test_baseline_is_immutable_when_requirement_is_added_to_reopened_mission(client):
    baseline = command(
        client, to_ready(client), "baseline", name="Before new requirement", confirm=True
    )
    root = f"/api/missions/{baseline['id']}"
    snapshot = client.get(root + "/export/json").json()
    assert submit(client, baseline).status_code == 409
    reopened = command(client, baseline, "reopen", reason="Add operations requirement")
    proposed = submit(client, reopened).json()
    accepted = approve(client, proposed)
    assert accepted["phase"] == "Recalculation required"
    assert client.get(root + f"/export/json?baseline_id={baseline['baseline']}").json() == snapshot
