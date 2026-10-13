import os

import pytest
from fastapi.testclient import TestClient

from app.api.main import create_app
from app.persistence.store import Store


@pytest.fixture
def client(tmp_path):
    store = Store(os.getenv("TEST_DATABASE_URL", "sqlite:///" + str(tmp_path / "test.db")))
    try:
        store.initialize()
        with TestClient(create_app(store)) as test_client:
            yield test_client
    finally:
        # Each test owns its pool. Release idle PostgreSQL connections even when
        # setup or the test fails; otherwise the full suite exhausts max_connections.
        store.engine.dispose()
