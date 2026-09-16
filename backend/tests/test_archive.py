from test_workflow import approve, command, create, to_ready


def test_archive_restore_pending_mission_and_edit_guards(client):
    mission = create(client)
    other = create(client)
    base = f"/api/missions/{mission['id']}"
    archived = command(client, mission, "archive", archived=True)
    assert archived["archived"] is True
    assert mission["id"] not in [m["id"] for m in client.get("/api/missions").json()]
    assert other["id"] in [m["id"] for m in client.get("/api/missions").json()]
    assert mission["id"] in [m["id"] for m in client.get("/api/missions?archived=true").json()]
    assert client.get(base).json()["archived"] is True
    for path, extra in [
        ("advance", {}),
        ("pause", {}),
        ("restore", {"source_revision": 0}),
        ("reopen", {"reason": "Cannot reopen archived mission"}),
    ]:
        response = client.post(base + "/" + path, json={"revision": archived["revision"], **extra})
        assert response.status_code == 409 and "archiv" in response.text.lower()
    # Repeating the same state at the current revision does not append another event.
    assert command(client, archived, "archive", archived=True) == archived
    restored = command(client, archived, "archive", archived=False)
    assert not restored["archived"]
    assert restored["phase"] == mission["phase"] and restored["paused"] == mission["paused"]
    assert mission["id"] in [m["id"] for m in client.get("/api/missions").json()]
    assert not any(
        m["id"] == mission["id"] for m in client.get("/api/missions?archived=true").json()
    )
    assert approve(client, restored)["phase"] == "Needs defined"
    history = client.get(base + "/history").json()
    assert any("Archived mission" in event["reason"] for event in history)
    assert any("Restored mission to active" in event["reason"] for event in history)


def test_archive_preserves_baseline_exports_and_historical_revisions(client):
    m = command(client, to_ready(client), "baseline", name="Keep this snapshot", confirm=True)
    base = f"/api/missions/{m['id']}"
    exported = client.get(base + "/export/json").json()
    baseline_list = client.get(base + "/baselines").json()
    revision = client.get(base + f"/revisions/{m['revision']}").json()
    archived = command(client, m, "archive", archived=True)
    assert archived["baseline"] == m["baseline"]
    assert client.get(base + "/export/json").json() == exported
    assert client.get(base + "/baselines").json() == baseline_list
    assert client.get(base + f"/revisions/{m['revision']}").json() == revision
    restored = command(client, archived, "archive", archived=False)
    assert restored["baseline"] == m["baseline"]
    assert restored["entities"] == m["entities"]
    assert client.get(base + "/export/json").json() == exported


def test_archive_rejects_stale_revision_and_unknown_mission(client):
    m = create(client)
    archived = command(client, m, "archive", archived=True)
    response = client.post(
        f"/api/missions/{m['id']}/archive", json={"revision": m["revision"], "archived": False}
    )
    assert response.status_code == 409
    assert client.get(f"/api/missions/{m['id']}").json() == archived
    assert (
        client.post(
            "/api/missions/missing/archive", json={"revision": 0, "archived": True}
        ).status_code
        == 404
    )
