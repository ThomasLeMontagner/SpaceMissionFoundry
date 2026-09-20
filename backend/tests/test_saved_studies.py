import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session
from test_workflow import command, create, to_ready

from app.api.main import create_app
from app.orchestration.scenario import Q
from app.persistence.store import Store, StudyRow


def body(m, name="Ground delay study"):
    return dict(
        name=name,
        study=dict(
            revision=m["revision"],
            candidate="selective",
            parameter="ground_delay",
            values=[Q(0, "minute"), Q(60, "minute")],
            deadline=Q(30, "minute"),
        ),
    )


def test_save_reload_scope_archive_and_baseline_integrity(client):
    m = command(client, to_ready(client), "baseline", name="Study source", confirm=True)
    base = f"/api/missions/{m['id']}"
    snapshot = client.get(base + "/export/json").json()
    response = client.post(base + "/sensitivity-studies", json=body(m))
    assert response.status_code == 201, response.text
    saved = response.json()
    assert saved["result"]["study_request"] == body(m)["study"]
    assert saved["result"]["trials"][0]["deadline_check"]["status"] == "pass"
    assert saved["result"]["trials"][1]["deadline_check"]["status"] == "fail"
    assert client.get(base).json() == m
    assert client.get(base + "/export/json").json() == snapshot
    # str(URL) masks passwords; connection reuse must preserve the actual credentials.
    reopened_store = Store(client.app.state.store.engine.url.render_as_string(hide_password=False))
    try:
        with TestClient(create_app(reopened_store)) as reopened:
            assert reopened.get(base + "/sensitivity-studies/" + saved["id"]).json() == saved
            assert reopened.get(base + "/sensitivity-studies").json()[0]["id"] == saved["id"]
    finally:
        reopened_store.engine.dispose()
    other = create(client)
    assert (
        client.get(f"/api/missions/{other['id']}/sensitivity-studies/{saved['id']}").status_code
        == 404
    )
    m = command(client, m, "archive", archived=True)
    assert client.post(base + "/sensitivity-studies", json=body(m)).status_code == 409
    assert client.get(base + "/sensitivity-studies/" + saved["id"]).json() == saved
    assert client.get(base + "/export/json").json() == snapshot


def test_reject_forged_stale_blank_and_orm_changes(client):
    m = to_ready(client)
    base = f"/api/missions/{m['id']}/sensitivity-studies"
    assert client.post(base, json={**body(m), "result": {"status": "pass"}}).status_code == 422
    assert client.post(base, json=body(m, "   ")).status_code == 409
    stale = body(m)
    stale["study"]["revision"] = 0
    assert client.post(base, json=stale).status_code == 409
    assert client.get(base).json() == []
    saved = client.post(base, json=body(m)).json()
    with Session(client.app.state.store.engine) as session:
        row = session.get(StudyRow, saved["id"])
        row.name = "Changed"
        with pytest.raises(ValueError, match="append-only"):
            session.commit()
    with Session(client.app.state.store.engine) as session:
        session.delete(session.get(StudyRow, saved["id"]))
        with pytest.raises(ValueError, match="append-only"):
            session.commit()


def test_migration_preserves_existing_mission_and_blocks_sql_mutation(tmp_path):
    url = "sqlite:///" + str(tmp_path / "migration.db")
    env = {**os.environ, "DATABASE_URL": url}
    cwd = Path(__file__).resolve().parents[1]

    def migrate(target):
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", target],
            cwd=cwd,
            env=env,
            check=True,
            capture_output=True,
        )

    migrate("0001")
    store = Store(url)
    client = TestClient(create_app(store))
    m = to_ready(client)
    migrate("head")
    assert store.get(m["id"]).model_dump() == m
    base = f"/api/missions/{m['id']}/sensitivity-studies"
    response = client.post(base, json=body(m))
    assert response.status_code == 201, response.text
    saved = response.json()
    for query in [
        "DELETE FROM sensitivity_studies",
        "UPDATE sensitivity_studies SET name = 'changed'",
    ]:
        with store.engine.begin() as connection:
            with pytest.raises(DBAPIError, match="append-only"):
                connection.execute(text(query))
    assert client.get(base + "/" + saved["id"]).json() == saved
