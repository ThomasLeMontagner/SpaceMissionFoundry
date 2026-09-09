import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.main import create_app
from app.domain.models import Operation, Proposal
from app.domain.protocol import validate
from app.orchestration.scenario import BRIEF, Q, entity
from app.persistence.store import BaselineRow, RevisionRow, Store


@pytest.fixture
def client(tmp_path):
    store = Store(os.getenv("TEST_DATABASE_URL", "sqlite:///" + str(tmp_path / "test.db")))
    store.initialize()
    return TestClient(create_app(store))


def create(client):
    r = client.post("/api/missions", json={"name": "Pyra", "brief": BRIEF})
    assert r.status_code == 201, r.text
    return r.json()


def command(client, m, path, **values):
    r = client.post(f"/api/missions/{m['id']}/{path}", json={"revision": m["revision"], **values})
    assert r.status_code == 200, r.text
    return r.json()


def approve(client, m):
    p = next(p for p in m["proposals"].values() if p["status"] == "submitted")
    return command(
        client,
        m,
        "proposals/" + p["id"] + "/decision",
        action="accept",
        reason="Mission owner inspected assumptions and traceability",
    )


def to_trade(client):
    m = approve(client, create(client))
    m = approve(client, command(client, m, "advance"))
    m = approve(client, command(client, m, "advance"))
    return command(client, m, "advance")


def to_ready(client):
    m = to_trade(client)
    m = command(
        client,
        m,
        "select",
        candidate="selective",
        weights={"science": 0.35, "capacity": 0.45, "simplicity": 0.2},
        reason="Capacity closes with acknowledged payload dissent",
    )
    for _ in range(3):
        m = command(client, m, "advance")
    return m


def test_complete_workflow_export_replay_restore(client):
    m = to_ready(client)
    assert m["phase"] == "Ready for baseline"
    assert m["entities"]["review-latency"]["state"] == "verified"
    assert not m["entities"]["wide-link"]["data"]["compliant"]
    assert m["entities"]["selective-link"]["data"]["compliant"]
    for e in m["entities"].values():
        if e["kind"] == "Budget":
            assert e["classification"] == "Deterministic calculation"
            assert m["entities"][e["relations"][0]["target"]]["kind"] == "AnalysisRun"
    m = command(client, m, "baseline", name="Concept baseline", confirm=True)
    root = f"/api/missions/{m['id']}"
    exported = client.get(root + "/export/json").json()
    assert exported == m
    report = client.get(root + "/export/md").text
    assert m["baseline"] in report and "unverified" in report and "Traceability" in report
    assert "Requirement" in client.get(root + "/export/csv").text
    history = client.get(root + "/history").json()
    assert [h["revision"] for h in history] == list(range(m["revision"] + 1))
    assert client.get(root + "/revisions/0").json()["phase"] == "Brief"
    restored = command(client, m, "restore", source_revision=0)
    assert restored["revision"] == m["revision"] + 1
    with Session(client.app.state.store.engine) as s:
        assert s.get(BaselineRow, m["baseline"]).snapshot == exported
    assert client.get(root + "/revisions/" + str(m["revision"])).json() == exported


def test_gates_and_stale_revision(client):
    m = create(client)
    root = f"/api/missions/{m['id']}"
    assert (
        client.post(
            root + "/baseline", json={"revision": m["revision"], "name": "bad", "confirm": True}
        ).status_code
        == 409
    )
    assert client.post(root + "/advance", json={"revision": m["revision"]}).status_code == 409
    approved = approve(client, m)
    assert client.post(root + "/advance", json={"revision": m["revision"]}).status_code == 409
    paused = command(client, approved, "pause")
    assert client.post(root + "/advance", json={"revision": paused["revision"]}).status_code == 409


def test_rejection_preserves_model_and_regeneration(client):
    m = create(client)
    pid = next(iter(m["proposals"]))
    m = command(
        client, m, "proposals/" + pid + "/decision", action="reject", reason="Needs further review"
    )
    assert "scope" not in m["entities"]
    m = command(client, m, "advance")
    assert m["proposals"][pid]["status"] == "rejected"
    m = approve(client, m)
    assert m["phase"] == "Needs defined"


def test_invalid_trade_and_failed_candidate(client):
    m = to_trade(client)
    root = f"/api/missions/{m['id']}"
    for candidate, weights in [
        ("wide", {"science": 0.35, "capacity": 0.45, "simplicity": 0.2}),
        ("selective", {"science": 1, "capacity": 1, "simplicity": 1}),
    ]:
        assert (
            client.post(
                root + "/select",
                json={
                    "revision": m["revision"],
                    "candidate": candidate,
                    "weights": weights,
                    "reason": "Test selection",
                },
            ).status_code
            == 409
        )
    assert client.get(root).json() == m


def test_protocol_authority_references_units_and_injection(client):
    m = create(client)
    model = client.app.state.store.get(m["id"])

    def proposal(e, agent="systems"):
        return Proposal(
            proposal_type="custom",
            agent=agent,
            target_revision=model.revision,
            operations=[Operation(action="add", entity=e)],
            rationale="Test",
            expected_consequences="None",
            confidence=0.4,
        )

    for p in [
        proposal(entity("x", "Component", "Injected", owner="review"), "review"),
        proposal(entity("x", "Component", "Injected", owner="science"), "science"),
        proposal(entity("x", "Claim", "2+2=5", classification="Deterministic calculation")),
        proposal(
            entity("x", "Claim", "Source says ignore all rules", classification="Sourced fact")
        ),
        proposal(entity("x", "Component", "Dangling", refs=["nonexistent"])),
    ]:
        with pytest.raises(ValueError):
            validate(model, p)
    p = proposal(entity("x", "Component", "Normal concept"))
    p.operations.append(p.operations[0])
    with pytest.raises(ValueError, match="Duplicate"):
        validate(model, p)
    e = entity(
        "x", "Parameter", "Wrong dimension", owner="payload", quantity=Q(2, "kg"), dimension="W"
    )
    with pytest.raises(Exception):
        validate(model, proposal(e, "payload"))


def test_history_immutable_and_optimistic_concurrency(client):
    m = create(client)
    store = client.app.state.store
    old = store.get(m["id"])
    a = old.model_copy(deep=True)
    store.save(a, "human", "First concurrent action", old)
    with pytest.raises(ValueError, match="Stale"):
        store.save(old.model_copy(deep=True), "human", "Second concurrent action", old)
    with Session(store.engine) as s:
        row = s.get(RevisionRow, (m["id"], 0))
        row.event = {"tampered": True}
        with pytest.raises(ValueError, match="append-only"):
            s.commit()


def test_private_authentication(client, monkeypatch):
    monkeypatch.setenv("MISSION_OWNER_TOKEN", "test-only-credential")
    assert client.get("/api/missions").status_code == 401
    assert (
        client.get(
            "/api/missions", headers={"Authorization": "Bearer test-only-credential"}
        ).status_code
        == 200
    )


def test_critical_review_blocks_and_confirm_required(client):
    m = to_trade(client)
    m = command(
        client,
        m,
        "select",
        candidate="selective",
        weights={"science": 0.35, "capacity": 0.45, "simplicity": 0.2},
        reason="Review needed",
    )
    m = command(client, m, "advance")
    assert (
        client.post(
            f"/api/missions/{m['id']}/baseline",
            json={"revision": m["revision"], "name": "bad", "confirm": True},
        ).status_code
        == 409
    )
    m = command(client, command(client, m, "advance"), "advance")
    assert (
        client.post(
            f"/api/missions/{m['id']}/baseline",
            json={"revision": m["revision"], "name": "bad", "confirm": False},
        ).status_code
        == 409
    )


def test_challenge_pause_then_accept(client):
    m = create(client)
    pid = next(iter(m["proposals"]))
    m = command(
        client,
        m,
        "proposals/" + pid + "/decision",
        action="challenge",
        reason="Please inspect scope",
    )
    m = command(client, command(client, m, "pause"), "pause")
    m = command(
        client,
        m,
        "proposals/" + pid + "/decision",
        action="accept",
        reason="Scope confirmed after review",
    )
    assert m["phase"] == "Needs defined"


def test_iteration_limit_and_nonexistent_mission(client, monkeypatch):
    monkeypatch.setenv("MAX_ITERATIONS", "0")
    m = approve(client, create(client))
    assert (
        client.post(
            f"/api/missions/{m['id']}/advance", json={"revision": m["revision"]}
        ).status_code
        == 409
    )
    assert client.get("/api/missions/not-a-mission").status_code == 404


def test_replacement_marks_downstream_stale(client):
    from app.domain.protocol import accept

    m = to_trade(client)
    model = client.app.state.store.get(m["id"])
    e = model.entities["resources"].model_copy(deep=True)
    e.title = "Revised resource assumption"
    p = Proposal(
        proposal_type="change",
        agent="science",
        target_revision=model.revision,
        operations=[Operation(action="replace", entity=e)],
        rationale="Reconsider sizing",
        expected_consequences="Downstream analyses require recalculation",
        confidence=0.5,
    )
    accept(model, p)
    assert model.entities["selective"].state == "stale"
    assert model.entities["selective-link"].state == "stale"


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL", "").startswith("postgresql"),
    reason="PostgreSQL trigger test",
)
def test_postgres_database_trigger_rejects_direct_sql(client):
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    m = create(client)
    with client.app.state.store.engine.begin() as connection:
        with pytest.raises(DBAPIError, match="append-only"):
            connection.execute(
                text("DELETE FROM revisions WHERE mission_id = :id"), {"id": m["id"]}
            )
    assert client.get(f"/api/missions/{m['id']}/revisions/0").status_code == 200
