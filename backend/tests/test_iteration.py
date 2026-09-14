from copy import deepcopy

import pytest
from test_workflow import approve, command, create, to_ready, to_trade


def edit(client, m, key, changes):
    return command(
        client,
        m,
        f"objects/{key}/edit",
        changes=changes,
        reason="Mission owner proposes revised engineering basis",
    )


def select_and_review(client, m):
    m = command(
        client,
        m,
        "select",
        candidate="selective",
        weights={"science": 0.35, "capacity": 0.45, "simplicity": 0.2},
        reason="Revised design now closes all resource budgets",
    )
    for _ in range(3):
        m = command(client, m, "advance")
    return m


def test_duty_cycle_conflict_correction_and_two_immutable_baselines(client):
    first = command(client, to_ready(client), "baseline", name="Original baseline", confirm=True)
    base = f"/api/missions/{first['id']}"
    before = client.get(base + "/export/json").json()
    first_revision = before["revision"]
    assert (
        client.post(
            base + "/objects/resources/edit",
            json={
                "revision": first_revision,
                "changes": {"confidence": 0.2},
                "reason": "Cannot mutate baseline",
            },
        ).status_code
        == 409
    )
    m = command(client, first, "reopen", reason="Evaluate a higher observation duty cycle")
    assert m["derived_from_baseline"] == first["baseline"] and not m["baseline"]
    key = "selective-data-inputs"
    values = deepcopy(m["entities"][key]["data"]["inputs"])
    values["duty"] = {"value": 10, "unit": "percent"}
    m = edit(client, m, key, {"inputs": values})
    assert m["entities"][key]["data"]["inputs"]["duty"]["value"] == 0.02
    proposal_id = next(p["id"] for p in m["proposals"].values() if p["status"] == "submitted")
    m = approve(client, m)
    assert m["phase"] == "Recalculation required"
    for id in ["selective-data-analysis", "selective-link", "trade", "selection", "review-latency"]:
        assert m["entities"][id]["state"] == "stale"
    assert m["entities"]["selective-mass"]["state"] == "accepted"
    assert (
        client.post(
            base + "/baseline",
            json={"revision": m["revision"], "name": "Premature", "confirm": True},
        ).status_code
        == 409
    )
    source = m["revision"]
    m = command(client, m, "advance")
    assert m["entities"]["selective-data"]["data"]["daily"]["value"] == pytest.approx(43.2e9)
    assert m["entities"]["selective-conflict"]["state"] == "open"
    assert m["entities"]["selective-data-analysis"]["data"]["source_revision"] == source
    assert m["entities"]["selective-data-analysis"]["data"]["inputs"]["duty"] == values["duty"]
    assert (
        client.post(
            base + "/select",
            json={
                "revision": m["revision"],
                "candidate": "selective",
                "weights": {"science": 0.35, "capacity": 0.45, "simplicity": 0.2},
                "reason": "Cannot approve a failure",
            },
        ).status_code
        == 409
    )
    link = deepcopy(m["entities"]["selective-link-inputs"]["data"]["inputs"])
    link["contact"] = {"value": 120, "unit": "minute"}
    m = approve(client, edit(client, m, "selective-link-inputs", {"inputs": link}))
    m = command(client, m, "advance")
    assert m["entities"]["selective-link"]["data"]["capacity"]["value"] == pytest.approx(50.4e9)
    assert m["entities"]["selective-conflict"]["state"] == "verified"
    m = select_and_review(client, m)
    second = command(client, m, "baseline", name="Revised baseline", confirm=True)
    assert second["baseline"] != first["baseline"]
    assert client.get(base + f"/export/json?baseline_id={first['baseline']}").json() == before
    assert client.get(base + f"/revisions/{first_revision}").json() == before
    assert [b["name"] for b in client.get(base + "/baselines").json()] == [
        "Original baseline",
        "Revised baseline",
    ]
    assert client.get(base + "/export/json").json() == second
    event = next(
        e for e in client.app.state.store.history(m["id"]) if proposal_id in e["affected_objects"]
    )
    assert event["actor"] == "human"
    foreign = create(client)
    assert (
        client.get(
            f"/api/missions/{foreign['id']}/export/json?baseline_id={first['baseline']}"
        ).status_code
        == 409
    )


def test_rejected_edit_and_stale_request_leave_values_unchanged(client):
    m = to_trade(client)
    original = deepcopy(m)
    m = edit(client, m, "req-latency", {"title": "Deliver imagery within 20 minutes."})
    pid = next(p["id"] for p in m["proposals"].values() if p["status"] == "submitted")
    m = command(
        client,
        m,
        f"proposals/{pid}/decision",
        action="reject",
        reason="Keep current latency requirement",
    )
    assert m["entities"]["req-latency"] == original["entities"]["req-latency"]
    assert m["entities"]["selective-link"]["state"] == "accepted"
    assert (
        client.post(
            f"/api/missions/{m['id']}/objects/req-latency/edit",
            json={
                "revision": original["revision"],
                "changes": {"title": "New title"},
                "reason": "Stale client",
            },
        ).status_code
        == 409
    )


@pytest.mark.parametrize(
    "object_id, changes",
    [
        ("req-latency", {"title": "The ground segment shall deliver imagery within 20 minutes."}),
        ("resources", {"title": "Revised resource maturity assumption", "confidence": 0.3}),
    ],
)
def test_text_edits_require_explicit_impact_review(client, object_id, changes):
    m = to_ready(client)
    original = m["entities"][object_id]["created_at"]
    m = approve(client, edit(client, m, object_id, changes))
    assert m["phase"] == "Impact review"
    assert m["entities"][object_id]["created_at"] == original
    base = f"/api/missions/{m['id']}"
    assert client.post(base + "/advance", json={"revision": m["revision"]}).status_code == 409
    assert (
        client.post(
            base + "/review-impact",
            json={"revision": m["revision"], "reason": "Not confirmed", "confirm": False},
        ).status_code
        == 409
    )
    m = command(
        client,
        m,
        "review-impact",
        reason="Reviewed linked requirements and design inputs; reaffirmed for concept study",
        confirm=True,
    )
    assert m["phase"] == "Recalculation required"
    m = select_and_review(client, command(client, m, "advance"))
    assert not [e for e in m["entities"].values() if e["state"] == "stale"]
    if object_id == "req-latency":
        assert m["entities"]["verify-latency"]["data"]["success_criterion"] == changes["title"]
    command(client, m, "baseline", name="Reviewed change baseline", confirm=True)


def test_inputs_not_seed_constants_drive_every_budget(client, monkeypatch):
    m = to_trade(client)
    import app.services.design_inputs as scenario

    monkeypatch.setattr(
        scenario, "inputs", lambda *args: pytest.fail("Scenario constants used at runtime")
    )
    for tool, field, quantity, output, expected in [
        ("mass", "limit", {"value": 30, "unit": "kg"}, "margin", 16.8),
        ("power", "battery", {"value": 100, "unit": "Wh"}, "usable_battery", 60),
        ("data", "compression", {"value": 8, "unit": ""}, "daily", 4.32e9),
        ("link", "contact", {"value": 3600, "unit": "s"}, "capacity", 25.2e9),
    ]:
        key = f"selective-{tool}-inputs"
        data = deepcopy(m["entities"][key]["data"]["inputs"])
        data[field] = quantity
        m = approve(client, edit(client, m, key, {"inputs": data}))
        m = command(client, m, "advance")
        assert m["entities"][f"selective-{tool}"]["data"][output]["value"] == pytest.approx(
            expected
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("duty", {"value": 2, "unit": ""}),
        ("rate", {"value": 5, "unit": "kg"}),
        ("compression", {"value": 0, "unit": ""}),
    ],
)
def test_invalid_quantities_rejected_atomically(client, field, value):
    m = to_trade(client)
    values = deepcopy(m["entities"]["selective-data-inputs"]["data"]["inputs"])
    values[field] = value
    base = f"/api/missions/{m['id']}"
    response = client.post(
        base + "/objects/selective-data-inputs/edit",
        json={
            "revision": m["revision"],
            "changes": {"inputs": values},
            "reason": "Invalid test edit",
        },
    )
    assert response.status_code in [409, 422]
    assert client.get(base).json() == m


def test_derived_input_injection_rejected(client):
    m = to_trade(client)
    values = deepcopy(m["entities"]["selective-link-inputs"]["data"]["inputs"])
    values["demand"] = {"value": 0, "unit": "bit"}
    assert client.post(
        f"/api/missions/{m['id']}/objects/selective-link-inputs/edit",
        json={
            "revision": m["revision"],
            "changes": {"inputs": values},
            "reason": "Override real demand",
        },
    ).status_code in [409, 422]


def test_failed_tool_persists_unknown_and_blocks_selection(client, monkeypatch):
    from app.engineering_tools.calculations import TOOLS

    m = to_trade(client)
    data = deepcopy(m["entities"]["selective-data-inputs"]["data"]["inputs"])
    data["duty"]["value"] = 0.03
    m = approve(client, edit(client, m, "selective-data-inputs", {"inputs": data}))

    def fail(_):
        raise ValueError("Controlled calculation failure")

    monkeypatch.setitem(TOOLS, "data", fail)
    m = command(client, m, "advance")
    assert m["entities"]["selective-data"]["classification"] == "Unknown"
    assert m["entities"]["selective-data"]["data"]["compliant"] is None
    assert m["entities"]["selective-data-analysis"]["data"]["errors"] == [
        "Controlled calculation failure"
    ]
    assert m["entities"]["selective-link-analysis"]["data"]["status"] == "invalid"
    assert m["entities"]["selective-data-conflict"]["state"] == "open"


def test_legacy_inputs_are_explicitly_recovered_from_recorded_runs(client):
    m = to_ready(client)
    store = client.app.state.store
    old = store.get(m["id"])
    legacy = old.model_copy(deep=True)
    # Simulate a v0.1 snapshot that predates input objects and input traceability edges.
    removed = {k for k, e in legacy.entities.items() if e.kind == "Parameter"}
    legacy.entities = {k: e for k, e in legacy.entities.items() if k not in removed}
    for e in legacy.entities.values():
        e.relations = [r for r in e.relations if r.target not in removed]
    store.save(legacy, "human", "Legacy compatibility fixture", old)
    m = legacy.model_dump(mode="json")
    m = command(client, m, "initialize-inputs")
    assert "selective-data-inputs" not in m["entities"]
    m = approve(client, m)
    assert m["phase"] == "Recalculation required"
    assert (
        m["entities"]["selective-data-inputs"]["data"]["inputs"]
        == m["entities"]["selective-data-analysis"]["data"]["inputs"]
    )
    m = select_and_review(client, command(client, m, "advance"))
    command(client, m, "baseline", name="Migrated baseline", confirm=True)
