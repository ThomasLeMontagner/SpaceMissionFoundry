from copy import deepcopy

from test_iteration import edit
from test_saved_studies import body
from test_workflow import approve, command, create, to_ready


def saved(client, m):
    response = client.post(f"/api/missions/{m['id']}/sensitivity-studies", json=body(m))
    assert response.status_code == 201, response.text
    return response.json()


def propose(client, m, record, **overrides):
    return client.post(
        f"/api/missions/{m['id']}/sensitivity-studies/{record['id']}/propose",
        json={
            "revision": m["revision"],
            "trial_index": 0,
            "reason": "Reduce processing time based on recorded study",
            **overrides,
        },
    )


def test_trial_proposal_requires_review_and_preserves_baseline_and_study(client):
    m = command(client, to_ready(client), "baseline", name="Original", confirm=True)
    base = f"/api/missions/{m['id']}"
    snapshot = client.get(base + "/export/json").json()
    record = saved(client, m)
    assert propose(client, m, record).status_code == 409
    m = command(client, m, "reopen", reason="Explore reduced processing delay")
    old_inputs = deepcopy(m["entities"]["selective-delivery-inputs"]["data"]["inputs"])
    response = propose(client, m, record)
    assert response.status_code == 200, response.text
    m = response.json()
    assert m["entities"]["selective-delivery-inputs"]["data"]["inputs"] == old_inputs
    p = next(p for p in m["proposals"].values() if p["status"] == "submitted")
    assert p["source_study"]["id"] == record["id"]
    assert p["source_study"]["trial_index"] == 0
    proposed = p["operations"][0]["entity"]["data"]["inputs"]
    assert proposed == {**old_inputs, "ground_delay": {"value": 0, "unit": "minute"}}
    assert propose(client, m, record).status_code == 409
    m = approve(client, m)
    assert m["entities"]["selective-delivery-analysis"]["state"] == "stale"
    assert m["entities"]["selection"]["state"] == "stale"
    m = command(client, m, "advance")
    assert m["entities"]["selective-delivery-analysis"]["data"]["inputs"]["delays"] == proposed
    assert client.get(base + "/sensitivity-studies/" + record["id"]).json() == record
    assert client.get(base + "/export/json?baseline_id=" + snapshot["baseline"]).json() == snapshot


def test_scope_revision_noop_and_rejection(client):
    m = to_ready(client)
    record = saved(client, m)
    other = approve(client, create(client))
    assert propose(client, other, record).status_code == 404
    response = client.post(
        f"/api/missions/{m['id']}/sensitivity-studies/{record['id']}/propose",
        json=dict(revision=0, trial_index=0, reason="Stale request"),
    )
    assert response.status_code == 409
    assert propose(client, m, record, trial_index=14).status_code == 409
    assert propose(client, m, record, reason="   ").status_code == 409
    before = deepcopy(m["entities"])
    m = propose(client, m, record).json()
    p = next(p for p in m["proposals"].values() if p["status"] == "submitted")
    m = command(
        client, m, f"proposals/{p['id']}/decision", action="reject", reason="Keep current input"
    )
    assert all(m["entities"][key] == value for key, value in before.items())
    assert all(e["kind"] == "Decision" for key, e in m["entities"].items() if key not in before)
    request = body(m)
    request["study"]["values"][0] = {"value": 2, "unit": "minute"}
    noop = client.post(f"/api/missions/{m['id']}/sensitivity-studies", json=request).json()
    assert "already matches" in propose(client, m, noop).text


def test_changed_design_and_archive_require_new_review(client):
    m = to_ready(client)
    record = saved(client, m)
    values = deepcopy(m["entities"]["selective-delivery-inputs"]["data"]["inputs"])
    values["onboard_delay"]["value"] += 1
    m = approve(client, edit(client, m, "selective-delivery-inputs", {"inputs": values}))
    assert propose(client, m, record).status_code == 409
    m = command(client, m, "advance")
    assert "differ" in propose(client, m, record).text
    m = command(client, m, "archive", archived=True)
    assert propose(client, m, record).status_code == 409
