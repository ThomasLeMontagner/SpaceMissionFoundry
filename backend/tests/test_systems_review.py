import json

import httpx
import pytest
from test_collaboration import start
from test_workflow import approve, command, to_trade

from app.agents.design_provider import DutyProposal
from app.agents.systems_review import SystemsReview


def assessment(outcome="submit"):
    return dict(
        recommendation=outcome,
        rationale="Review the science trade-off against the recorded goal.",
        findings=[
            dict(
                severity="advisory" if outcome == "submit" else "blocking",
                summary="Science adequacy requires owner assessment.",
                evidence=["mission_goal", "bus_proposal", "data_analysis"],
            )
        ],
        follow_up=""
        if outcome == "submit"
        else "Specify the minimum observation time required for science.",
    )


def review_ready(client):
    source, model, run_id = start(client)
    for _ in range(4):
        model = command(client, model, f"collaboration/{run_id}/step")
    return source, model, run_id


@pytest.mark.parametrize("outcome", ["submit", "revise", "clarify"])
def test_review_outcome_controls_submission_and_preserves_design(client, monkeypatch, outcome):
    source, model, run_id = review_ready(client)

    def reviewer(context, mode):
        assert context["bus_proposal"]["duty"] == model["entities"][run_id]["data"]["bus"]["duty"]
        assert context["data_analysis"]["status"] == "valid"
        assert context["link_analysis"]["outputs"]["compliant"]
        assert context["mission_goal"]["brief"] == model["brief"]
        return SystemsReview(**assessment(outcome)), {"tokens": 42, "cost": None}

    monkeypatch.setattr("app.services.collaboration.review", reviewer)
    model = command(client, model, f"collaboration/{run_id}/step")
    run = model["entities"][run_id]["data"]
    assert run["systems_review"]["recommendation"] == outcome
    assert run["review_usage"]["tokens"] == 42
    assert model["entities"]["selective-data-inputs"] == source["entities"]["selective-data-inputs"]
    review_event = next(e for e in run["events"] if e["type"] == "systems_review")
    assert review_event["evidence"]["context"]["data_analysis"] == run["evaluate_bus"]["data"]
    if outcome == "submit":
        assert run["status"] == "awaiting_approval"
        assert approve(client, model)["entities"][run_id]["data"]["status"] == "accepted"
    else:
        assert run["status"] == "blocked" and run["proposal_id"] is None
        assert model["proposals"] == source["proposals"]
        model = command(
            client,
            model,
            f"collaboration/{run_id}/clarify",
            feedback=run["systems_review"]["follow_up"],
            minimum_duty=0.035,
        )
        revised = model["entities"][run_id]["data"]
        assert "systems_review" not in revised
        assert revised["round_history"][0]["systems_review"]["recommendation"] == outcome
        from app.agents.design_provider import propose

        def capture_feedback(role, context, mode):
            assert context["previous_review"]["recommendation"] == outcome
            assert context["clarifications"][-1]["text"] == run["systems_review"]["follow_up"]
            return propose(role, context, mode)

        monkeypatch.setattr("app.services.collaboration.propose", capture_feedback)
        for _ in range(3):
            model = command(client, model, f"collaboration/{run_id}/step")


@pytest.mark.parametrize("action", ["cancel", "edit", "pause"])
def test_inflight_review_cannot_submit_after_interruption(client, monkeypatch, action):
    _, model, run_id = review_ready(client)

    def reviewer(context, mode):
        store = client.app.state.store
        current = store.get(model["id"])
        if action == "edit":
            updated = current.model_copy(deep=True)
            updated.entities["selective-data-inputs"].data["inputs"]["duty"]["value"] = 0.04
            store.save(updated, "human", "Concurrent design change", current)
        else:
            command(
                client,
                current.model_dump(mode="json"),
                "pause" if action == "pause" else f"collaboration/{run_id}/cancel",
            )
        return SystemsReview(**assessment()), {}

    monkeypatch.setattr("app.services.collaboration.review", reviewer)
    final = command(client, model, f"collaboration/{run_id}/step")
    run = final["entities"][run_id]["data"]
    assert run["status"] == {"cancel": "cancelled", "edit": "stale", "pause": "ready"}[action]
    assert "systems_review" not in run and run["proposal_id"] is None


def test_failed_calculations_never_call_reviewer(client, monkeypatch):
    source = to_trade(client)
    model = command(
        client, source, "collaboration", candidate="wide", goal="Inspect infeasible RF budget"
    )
    run_id = next(
        k for k, e in model["entities"].items() if e["data"].get("workflow") == "duty-collaboration"
    )

    def forbidden(*args):
        pytest.fail("Failing engineering evidence must not invoke the reviewer")

    monkeypatch.setattr("app.services.collaboration.review", forbidden)
    monkeypatch.setattr(
        "app.services.collaboration.propose",
        lambda *args: (
            DutyProposal(duty=1.0, rationale="Deliberately infeasible observation load"),
            {},
        ),
    )
    for _ in range(5):
        model = command(client, model, f"collaboration/{run_id}/step")
    assert model["entities"][run_id]["data"]["status"] == "blocked"


@pytest.mark.parametrize("invalid", [False, True])
def test_live_review_is_separate_structured_call_and_fails_closed(client, monkeypatch, invalid):
    source = to_trade(client)
    for key, value in {
        "LLM_PROVIDER": "openai-compatible",
        "LLM_MODEL": "mock-review-model",
        "LLM_BASE_URL": "https://example.invalid/v1",
        "LLM_API_KEY": "test-key",
        "LLM_MAX_PRICE_PER_MILLION": "1",
        "MAX_RUN_COST_EUR": "1",
    }.items():
        monkeypatch.setenv(key, value)
    model = command(
        client,
        source,
        "collaboration",
        candidate="selective",
        goal="Increase observation time",
        mode="live",
    )
    run_id = next(
        k for k, e in model["entities"].items() if e["data"].get("workflow") == "duty-collaboration"
    )
    calls = []
    real_client = httpx.Client

    def respond(request):
        body = json.loads(request.content)
        calls.append(body)
        if len(calls) < 3:
            result = {
                "duty": 0.1 if len(calls) == 1 else 0.03,
                "rationale": "Mock discipline proposal",
            }
        else:
            assert "independent Systems reviewer" in body["messages"][0]["content"]
            context = json.loads(body["messages"][1]["content"])
            assert context["bus_proposal"]["duty"] == 0.03
            assert context["data_analysis"]["inputs"]["duty"]["value"] == 0.03
            result = assessment()
            if invalid:
                result["findings"][0]["severity"] = "blocking"
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": json.dumps(result)}}],
                "usage": {"total_tokens": 55},
            },
        )

    monkeypatch.setattr(
        "app.agents.design_provider.httpx.Client",
        lambda **kw: real_client(transport=httpx.MockTransport(respond), **kw),
    )
    for _ in range(5):
        model = command(client, model, f"collaboration/{run_id}/step")
    assert len(calls) == 3
    run = model["entities"][run_id]["data"]
    assert run["status"] == ("failed" if invalid else "awaiting_approval")
    assert (run["proposal_id"] is None) == invalid


@pytest.mark.parametrize(
    "change",
    [
        dict(recommendation="approve"),
        dict(follow_up="", recommendation="clarify"),
        dict(duty=0.05),
        dict(
            findings=[
                dict(
                    severity="advisory", summary="Unknown evidence", evidence=["fabricated_source"]
                )
            ]
        ),
    ],
)
def test_review_contract_rejects_untrusted_fields_and_unactionable_results(change):
    with pytest.raises(ValueError):
        SystemsReview.model_validate({**assessment(), **change})
