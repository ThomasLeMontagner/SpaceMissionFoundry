import os

import pytest
from fastapi.testclient import TestClient

from app.api.main import create_app
from app.persistence.store import Store


@pytest.fixture
def client(tmp_path):
    store = Store(os.getenv("TEST_DATABASE_URL", "sqlite:///" + str(tmp_path / "test.db")))
    store.initialize()
    return TestClient(create_app(store))
