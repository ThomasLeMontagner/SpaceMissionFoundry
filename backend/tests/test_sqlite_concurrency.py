import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.exc import OperationalError

from app.api.main import create_app
from app.domain.models import Model
from app.persistence.store import Store


@pytest.fixture
def stores(tmp_path):
    url = "sqlite:///" + str(tmp_path / "concurrency.db")
    first, second = Store(url), Store(url)
    first.initialize()
    yield first, second
    first.engine.dispose()
    second.engine.dispose()


def seed(store):
    return store.save(
        Model(name="Concurrent mission", brief="Isolated test", baseline="baseline"),
        "human",
        "Initial snapshot",
        baseline=True,
    )


def test_in_memory_sqlite_still_works():
    store = Store("sqlite:///:memory:")
    try:
        store.initialize()
        original = seed(store)
        assert store.get(original.id) == original
    finally:
        store.engine.dispose()


def test_unrelated_database_errors_are_not_reported_as_busy(stores, monkeypatch):
    first, _ = stores

    def broken_list(archived=False):
        raise OperationalError("SELECT", {}, sqlite3.OperationalError("no such table"))

    monkeypatch.setattr(first, "list", broken_list)
    client = TestClient(create_app(first), raise_server_exceptions=False)
    response = client.get("/api/missions")
    assert response.status_code == 500
    assert "Retry-After" not in response.headers


def test_reader_keeps_snapshot_while_writer_commits(stores):
    first, second = stores
    original = seed(first)
    changed = original.model_copy(deep=True)
    changed.name = "Committed update"
    reader = first.engine.raw_connection()
    pool = ThreadPoolExecutor(max_workers=1)
    try:
        reader.execute("BEGIN")
        assert reader.execute("SELECT revision FROM missions").fetchone()[0] == 0
        future = pool.submit(second.save, changed, "human", "Concurrent change", original)
        assert future.result(timeout=5).revision == 1
        assert reader.execute("SELECT revision FROM missions").fetchone()[0] == 0
        reader.rollback()
        assert first.get(original.id).name == "Committed update"
        assert first.baseline(original.id) == original.model_dump(mode="json")
        assert first.revision(original.id, 0) == original
    finally:
        reader.rollback()
        reader.close()
        pool.shutdown()


def test_competing_writes_accept_only_one_revision(stores):
    first, second = stores
    original = seed(first)
    barrier = Barrier(2)

    def write(store, name):
        changed = original.model_copy(deep=True)
        changed.name = name
        barrier.wait(timeout=5)
        try:
            return store.save(changed, "human", name, original).name
        except ValueError as exc:
            assert "Stale revision" in str(exc)
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(write, first, "First writer")
        b = pool.submit(write, second, "Second writer")
        outcomes = [a.result(timeout=5), b.result(timeout=5)]
    assert outcomes.count(None) == 1
    winner = first.get(original.id)
    assert winner.revision == 1 and winner.name in outcomes
    assert len(first.history(original.id)) == 2
    assert first.revision(original.id, 1) == winner
    assert first.baseline(original.id) == original.model_dump(mode="json")


@pytest.mark.parametrize("archived", [False, True])
def test_study_waits_for_writer_then_rechecks_mission(stores, archived):
    first, second = stores
    original = seed(first)
    changed = original.model_copy(deep=True)
    changed.archived = archived
    changed.name = "Changed before study insertion"
    updated, release, study_started = Event(), Event(), Event()

    def hold_update(conn, cursor, statement, parameters, context, executemany):
        if statement.startswith("UPDATE missions"):
            updated.set()
            assert release.wait(timeout=5)

    def observe_study(conn, cursor, statement, parameters, context, executemany):
        if statement == "BEGIN IMMEDIATE":
            study_started.set()

    event.listen(first.engine, "after_cursor_execute", hold_update)
    event.listen(second.engine, "before_cursor_execute", observe_study)
    result = dict(source_revision=original.revision, candidate="selective", parameter="storage")
    with ThreadPoolExecutor(max_workers=2) as pool:
        writer = pool.submit(first.save, changed, "human", "Concurrent revision", original)
        try:
            assert updated.wait(timeout=5)
            saver = pool.submit(second.save_study, original.id, "Old study", result)
            assert study_started.wait(timeout=5)
        finally:
            release.set()
        writer.result(timeout=5)
        with pytest.raises(ValueError, match="archived" if archived else "Mission changed"):
            saver.result(timeout=5)
    assert first.studies(original.id) == []
    assert len(first.history(original.id)) == 2


def test_busy_api_rolls_back_and_can_retry(stores):
    first, second = stores
    original = seed(first)

    # A small timeout makes this a deterministic lock-exhaustion test, not a 30s wait.
    @event.listens_for(second.engine, "connect")
    def short_timeout(connection, record):
        connection.execute("PRAGMA busy_timeout=50")

    client = TestClient(create_app(second))
    # Pause requires an editable mission, so reopen this synthetic baseline first.
    response = client.post(
        f"/api/missions/{original.id}/reopen", json=dict(revision=0, reason="Prepare lock test")
    )
    assert response.status_code == 200
    revision = response.json()["revision"]
    before = first.get(original.id)
    with first.engine.connect() as blocker:
        blocker.exec_driver_sql("BEGIN IMMEDIATE")
        response = client.post(f"/api/missions/{original.id}/pause", json=dict(revision=revision))
        assert response.status_code == 503
        assert response.headers["Retry-After"] == "1"
        assert "Reload the mission" in response.json()["detail"]
        assert first.get(original.id) == before
        assert len(first.history(original.id)) == 2
        blocker.rollback()
    response = client.post(f"/api/missions/{original.id}/pause", json=dict(revision=revision))
    assert response.status_code == 200 and response.json()["paused"]
    assert len(first.history(original.id)) == 3
    assert first.baseline(original.id, "baseline") == original.model_dump(mode="json")
