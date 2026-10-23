from types import SimpleNamespace

from test_workflow import to_trade

from app.domain.models import Relation
from app.domain.requirement_quality import report
from app.orchestration.scenario import entity


def node(key, title=None, kind="Requirement", parents=(), state="accepted", **data):
    if kind == "Requirement":
        data = dict(
            level="system",
            priority="must",
            rationale="Test basis",
            source="Owner",
            verification_method="analysis",
            **data,
        )
    e = entity(key, kind, title or key, **data)
    e.state = state
    e.relations = [Relation(type="derives_from", target=p) for p in parents]
    return e


def check(*nodes):
    return report(SimpleNamespace(revision=4, entities={e.id: e for e in nodes}))


def codes(result, key):
    return {f["code"] for f in result["findings"] if f["requirement_id"] == key}


def test_traceability_cycles_missing_and_inactive_parents():
    result = check(
        node("objective", kind="Objective"),
        node("a", parents=["b"]),
        node("b", parents=["a"]),
        node("downstream", parents=["a"]),
        node("self", parents=["self"]),
        node("orphan", parents=["missing", "rejected", "component"]),
        node("rejected", state="rejected"),
        node("component", kind="Mission"),
    )
    for key in ["a", "b", "self"]:
        assert "derivation_cycle" in codes(result, key)
    assert "derivation_cycle" not in codes(result, "downstream")
    assert {"orphan", "invalid_parent"} <= codes(result, "orphan")
    assert "unsupported_objective" in codes(result, "objective")
    assert not codes(result, "rejected")


def test_supported_objective_and_duplicate_wording_are_advisory():
    result = check(
        node("objective", kind="Objective"),
        node("parent", parents=["objective"]),
        node("a", "Deliver useful imagery and data.", parents=["parent"]),
        node("b", "  DELIVER useful imagery and data ", parents=["parent"]),
        node("ignored", "Deliver useful imagery and data.", state="proposed"),
    )
    assert not codes(result, "objective")
    assert {"duplicate_statement", "ambiguous_wording", "possibly_compound"} <= codes(result, "a")
    finding = next(f for f in result["findings"] if f["id"] == "a:duplicate_statement")
    assert finding["related_ids"] == ["b"]
    assert result["advisory"] is True and result["revision"] == 4


def test_scope_is_bound_to_statement_and_criterion():
    rule = dict(metric="mass.total", operator="<=", threshold=dict(value=24, unit="kg"))
    e = node("req", "Mass shall not exceed 24 kg", criterion=rule)
    assert "unresolved_scope" in codes(check(e), "req")
    e.data["formalization"] = dict(
        statement=e.title, criterion=rule, coverage="full", basis="Owner reviewed all conditions"
    )
    assert "unresolved_scope" not in codes(check(e), "req")
    e.title += " including adapter"
    assert "unresolved_scope" in codes(check(e), "req")
    e.data["criterion"] = dict(
        metric="imaginary", operator="<=", threshold=dict(value=1, unit="kg")
    )
    assert "unsupported_verification" in codes(check(e), "req")


def test_report_is_read_only_and_repeatable(client):
    m = to_trade(client)
    path = f"/api/missions/{m['id']}"
    before = client.get(path).json()
    first = client.get(path + "/requirement-formalization").json()["quality"]
    assert first == client.get(path + "/requirement-formalization").json()["quality"]
    assert client.get(path).json() == before
    assert first["checked_requirements"] > 0
    assert any(f["code"] == "unsupported_verification" for f in first["findings"])


def test_long_chain_does_not_require_recursion():
    nodes = [node("objective", kind="Objective")]
    for i in range(1050):
        nodes.append(node(str(i), parents=[str(i - 1) if i else "objective"]))
    result = check(*nodes)
    assert not any(
        f["code"] in {"orphan", "derivation_cycle", "unsupported_objective"}
        for f in result["findings"]
    )
