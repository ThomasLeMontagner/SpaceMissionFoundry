import pytest
from test_requirement_checks import criterion
from test_workflow import approve, command, to_trade

from app.domain.formalization import apply_scope
from app.domain.models import Model
from app.services.formalization import inspect


def submit(client, m, **values):
    return client.post(
        f"/api/missions/{m['id']}/requirements/req-launch/formalize",
        json=dict(
            revision=m["revision"],
            criterion=criterion(),
            coverage="partial",
            basis="Preliminary mass allocation; deployer geometry remains unresolved",
            **values,
        ),
    )


def test_clarification_approval_and_scope(client):
    m = to_trade(client)
    original = m["entities"]["req-launch"]
    overview = client.get(f"/api/missions/{m['id']}/requirement-formalization").json()
    assert overview["revision"] == m["revision"]
    m = command(
        client, m, "requirements/req-launch/clarify", question="Which deployer envelope applies?"
    )
    note = next(
        e
        for e in m["entities"].values()
        if e["data"].get("workflow") == "requirement-formalization"
    )
    r = client.post(
        f"/api/missions/{m['id']}/requirements/req-launch/formalize",
        json=dict(
            revision=m["revision"],
            criterion=criterion(),
            coverage="full",
            basis="Mass allocation",
            confirm_full_coverage=True,
        ),
    )
    assert r.status_code == 409
    m = command(
        client,
        m,
        "requirements/req-launch/clarify",
        question=note["data"]["question"],
        answer="Geometry remains a separate unresolved obligation",
        reply_to=note["id"],
    )
    assert m["entities"][note["id"]] == note
    r = submit(client, m)
    assert r.status_code == 200, r.text
    m = r.json()
    assert m["entities"]["req-launch"] == original
    proposal = next(p for p in m["proposals"].values() if p["status"] == "submitted")
    assert proposal["evidence_references"] and note["id"] not in proposal["evidence_references"]
    m = approve(client, m)
    if m["phase"] == "Impact review":
        m = command(client, m, "review-impact", confirm=True, reason="Reviewed requirement scope")
    m = command(client, m, "advance")
    check = m["entities"]["check-req-launch-selective"]["data"]
    assert check["status"] == "unverified" and check["numeric_status"] == "pass"
    assert check["criterion_coverage"] == "partial"
    assert (
        client.post(
            f"/api/missions/{m['id']}/requirements/req-launch/clarify",
            json=dict(
                revision=m["revision"],
                question=note["data"]["question"],
                answer="Old answer",
                reply_to=note["id"],
            ),
        ).status_code
        == 409
    )


@pytest.mark.parametrize(
    "coverage,status,expected",
    [("partial", "pass", "unverified"), ("partial", "fail", "fail"), ("full", "pass", "pass")],
)
def test_coverage_binding(client, coverage, status, expected):
    m = Model.model_validate(to_trade(client))
    req = m.entities["req-launch"]
    req.data.update(
        criterion=criterion(),
        formalization=dict(
            statement=req.title,
            criterion=criterion(),
            coverage=coverage,
            basis="Owner assessed scope",
            open_questions=[],
            clarification_ids=[],
        ),
    )
    result = {"status": status}
    apply_scope(req, result)
    assert result["status"] == expected
    req.title += " and another obligation"
    result = {"status": "pass"}
    apply_scope(req, result)
    assert result["status"] == "unverified" and result["criterion_coverage"] == "needs_review"


def test_suggestion_is_literal_and_bounded(client):
    req = Model.model_validate(to_trade(client)).entities["req-latency"]
    req.title = "Deliver useful imagery within 2 hours of acquisition"
    assert inspect(req)["suggestion"]["criterion"]["threshold"] == {"value": 2, "unit": "hour"}
    req.title = "Keep cost low and lifetime long"
    assert inspect(req)["suggestion"] is None
    req.title = "Deliver within 2 hours of acquisition or within 3 hours of acquisition"
    assert inspect(req)["suggestion"] is None


def test_confirmation_revision_and_pending_guards(client):
    m = to_trade(client)
    url = f"/api/missions/{m['id']}/requirements/req-launch/formalize"
    body = dict(
        revision=m["revision"],
        criterion=criterion(),
        coverage="full",
        basis="Owner confirms the full scope",
    )
    assert client.post(url, json=body).status_code == 409
    assert (
        client.post(
            url, json={**body, "revision": m["revision"] - 1, "confirm_full_coverage": True}
        ).status_code
        == 409
    )
    r = client.post(url, json={**body, "confirm_full_coverage": True})
    assert r.status_code == 200, r.text
    proposed = r.json()
    assert submit(client, proposed).status_code == 409
    accepted = approve(client, proposed)
    assert accepted["entities"]["req-launch"]["data"]["formalization"]["coverage"] == "full"


def test_clarification_thread_bound_and_immutable_reply(client):
    m = to_trade(client)
    for i in range(10):
        m = command(client, m, "requirements/req-launch/clarify", question=f"Question {i}?")
    url = f"/api/missions/{m['id']}/requirements/req-launch/clarify"
    assert (
        client.post(
            url, json=dict(revision=m["revision"], question="Eleventh question")
        ).status_code
        == 409
    )
    note = next(
        e
        for e in m["entities"].values()
        if e["data"].get("workflow") == "requirement-formalization"
    )
    m = command(
        client,
        m,
        "requirements/req-launch/clarify",
        question=note["data"]["question"],
        answer="Explicit answer",
        reply_to=note["id"],
    )
    assert (
        client.post(
            url,
            json=dict(
                revision=m["revision"],
                question=note["data"]["question"],
                answer="Duplicate answer",
                reply_to=note["id"],
            ),
        ).status_code
        == 409
    )
    assert m["entities"][note["id"]] == note
