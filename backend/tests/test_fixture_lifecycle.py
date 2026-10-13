import pytest
from conftest import client as client_fixture
from sqlalchemy import event


@pytest.mark.parametrize("failed", [False, True])
def test_client_fixture_closes_its_pool_on_success_and_failure(tmp_path, failed):
    # Exercise the real fixture lifecycle, including teardown after an exception.
    lifecycle = client_fixture.__wrapped__(tmp_path)
    client = next(lifecycle)
    engine = client.app.state.store.engine
    closed = []
    event.listen(engine, "close", lambda connection, record: closed.append(True))
    client.app.state.store.list()
    assert engine.pool.checkedin() > 0
    if failed:
        with pytest.raises(RuntimeError, match="simulated test failure"):
            lifecycle.throw(RuntimeError("simulated test failure"))
    else:
        with pytest.raises(StopIteration):
            next(lifecycle)
    assert closed
    assert engine.pool.checkedin() == 0
    assert engine.pool.checkedout() == 0
