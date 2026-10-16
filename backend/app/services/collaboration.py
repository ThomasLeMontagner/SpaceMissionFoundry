"""Bounded design collaboration with revision-safe checkpoints and event evidence."""

import os
from copy import deepcopy
from time import perf_counter
from typing import Literal
from uuid import uuid4

from pydantic import Field, model_validator

from app.agents.design_provider import propose
from app.agents.systems_review import SystemsReview, review
from app.domain.models import Operation, Proposal, Strict, now
from app.domain.protocol import validate
from app.engineering_tools.calculations import execute, fraction
from app.orchestration.scenario import entity
from app.services import data_alternatives, run_budget
from app.services.design_inputs import IMPACT_KINDS, EditChanges, edited_entity, read_inputs
from app.services.execution_recovery import (
    STAGES,
    fingerprint,
    lease_deadline,
    lease_expired,
    recovery_details,
)
from app.services.impact_checks import ImpactAssumptions
from app.services.workflow import Workflow

ACTIVE = {"ready", "working", "failed", "interrupted", "budget_blocked"}


class Start(Strict):
    revision: int = Field(ge=0)
    candidate: Literal["wide", "selective"]
    goal: str = Field(min_length=3, max_length=1000)
    mode: Literal["simulation", "live"] = "simulation"
    limits: run_budget.Limits = Field(default_factory=run_budget.Limits)
    study: Literal["duty", "data-system", "cross-discipline"] = "duty"
    bounds: data_alternatives.Bounds | None = None
    impact_assumptions: ImpactAssumptions | None = None
    check_requirements: bool = Field(default=False, strict=True)

    @model_validator(mode="after")
    def study_bounds(self):
        if (self.study != "duty") != (self.bounds is not None):
            raise ValueError("Provide explicit bounds only for a data-system study")
        if self.impact_assumptions is not None and self.study != "cross-discipline":
            raise ValueError("Impact assumptions require a cross-discipline study")
        if self.check_requirements and self.study != "cross-discipline":
            raise ValueError("Mission requirement checks require a cross-discipline study")
        return self


class Clarification(Strict):
    revision: int = Field(ge=0)
    feedback: str = Field(min_length=3, max_length=2000)
    minimum_duty: float | None = Field(default=None, ge=0, le=1)


class Recovery(Strict):
    revision: int = Field(ge=0)
    retry_uncertain: bool = Field(default=False, strict=True)


def record(run, kind, sender, recipient, summary, evidence=None):
    events = run.data["events"]
    events.append(
        dict(
            id=str(uuid4()),
            sequence=len(events) + 1,
            timestamp=now(),
            type=kind,
            task=run.data["stage"],
            sender=sender,
            recipient=recipient,
            summary=summary,
            reply_to=events[-1]["id"] if events else None,
            objects=[run.data["input_id"]],
            evidence=evidence,
            source_revision=run.data["source_revision"],
            mode=run.data["mode"],
            round=run.data.get("round", 0),
        )
    )


def get_run(model, run_id):
    run = model.entities.get(run_id)
    if not run or run.kind != "AgentRun" or run.data.get("workflow") != "duty-collaboration":
        raise ValueError("Collaboration run does not belong to this mission")
    return run


def stop_execution(run, reason):
    execution = run.data.get("execution", {})
    if execution.get("status") == "running":
        execution.update(status="stopped", finished_at=now(), reason=reason)
        record(run, "execution_stopped", "orchestrator", "human", reason)


def advance_pending_metadata(model):
    # Agent activity alone does not change the design a pending proposal targets.
    for proposal in model.proposals.values():
        if (
            proposal.status in ["submitted", "challenged"]
            and proposal.target_revision == model.revision
        ):
            proposal.target_revision += 1


class Collaboration:
    def __init__(self, store):
        self.store = store
        self.workflow = Workflow(store)

    def start(self, mission_id, request):
        old = self.store.get(mission_id)
        self.workflow.guard(old, request.revision)
        self.workflow.no_pending(old)
        if old.paused or old.phase not in ["Trade study", "Ready for baseline"]:
            raise ValueError(
                "Resume an analyzed mission before starting collaboration; reopen baselines first"
            )
        if not request.goal.strip():
            raise ValueError("Describe the design goal")
        if any(
            e.data.get("workflow") == "duty-collaboration" and e.data.get("status") in ACTIVE
            for e in old.entities.values()
        ):
            raise ValueError("Finish or cancel the active collaboration first")
        if request.mode == "live" and os.getenv("LLM_PROVIDER", "mock") != "openai-compatible":
            raise ValueError("Configure a provider before selecting live execution")
        inputs = {tool: read_inputs(old, request.candidate, tool) for tool in ["data", "link"]}
        if any(e.state == "stale" for e in old.entities.values() if e.kind in IMPACT_KINDS):
            raise ValueError("Review stale design inputs before starting collaboration")
        if request.study == "cross-discipline":
            inputs.update(
                {tool: read_inputs(old, request.candidate, tool) for tool in ["mass", "power"]}
            )
            inputs["orbit"] = read_inputs(old, "mission", "orbit")
        requirement_input_blockers = []
        if request.check_requirements:
            for scope, tool in [("mission", "access"), (request.candidate, "delivery")]:
                try:
                    inputs[tool] = read_inputs(old, scope, tool)
                except ValueError as exc:
                    requirement_input_blockers.append(str(exc))
        m = old.model_copy(deep=True)
        run = entity(
            str(uuid4()),
            "AgentRun",
            f"{request.candidate} · {request.study + ' alternatives' if request.study != 'duty' else 'observation duty collaboration'}",
            "orchestrator",
            workflow="duty-collaboration",
            version="1.6",
            study=request.study,
            check_requirements=request.check_requirements,
            requirements=[
                e.model_dump(mode="json")
                for e in old.entities.values()
                if e.kind == "Requirement" and e.state in ["accepted", "stale"]
            ]
            if request.check_requirements
            else [],
            requirement_input_blockers=requirement_input_blockers,
            impact_assumptions=request.impact_assumptions.model_dump()
            if request.impact_assumptions
            else None,
            bounds=request.bounds.model_dump() if request.bounds else None,
            budget=run_budget.create(request.limits, request.mode),
            mode=request.mode,
            provider_model=os.getenv("LLM_MODEL")
            if request.mode == "live"
            else "scripted simulation",
            candidate=request.candidate,
            goal=request.goal.strip(),
            stage="payload",
            status="ready",
            source_revision=old.revision,
            fingerprint=fingerprint(old),
            inputs=inputs,
            input_id=f"{request.candidate}-data-inputs",
            events=[],
            completed=[],
            attempts=0,
            proposal_id=None,
        )
        record(run, "request", "human", "payload", request.goal.strip())
        m.entities[run.id] = run
        return self.store.save(m, "human", "Started explicitly selected collaboration mode", old)

    def cancel(self, mission_id, run_id, revision):
        old = self.store.get(mission_id)
        self.workflow.guard(old, revision)
        run = get_run(old, run_id)
        if run.data["status"] not in ACTIVE:
            raise ValueError(
                "Only active collaboration can be cancelled; pending proposals use the decision controls"
            )
        m = old.model_copy(deep=True)
        run = get_run(m, run_id)
        run.data["status"] = "cancelled"
        stop_execution(run, "Cancelled by mission owner; in-flight response will be discarded")
        record(
            run,
            "cancelled",
            "human",
            run.data["stage"],
            "Future work cancelled; any in-flight response will be discarded.",
        )
        return self.store.save(m, "human", "Cancelled collaboration", old)

    def clarify(self, mission_id, run_id, request):
        old = self.store.get(mission_id)
        self.workflow.guard(old, request.revision)
        original = get_run(old, run_id)
        proposal_id = original.data.get("proposal_id")
        proposal = old.proposals.get(proposal_id)
        if not (
            original.data["status"] == "blocked"
            or (
                original.data["status"] == "awaiting_approval"
                and proposal
                and proposal.status == "challenged"
            )
        ):
            raise ValueError(
                "Challenge the pending proposal before requesting revision, or revise a blocked negotiation"
            )
        if any(
            p.status in ["submitted", "challenged"] and p.id != proposal_id
            for p in old.proposals.values()
        ):
            raise ValueError("Resolve other pending proposals before requesting revision")
        if any(
            e.id != run_id
            and e.data.get("workflow") == "duty-collaboration"
            and e.data.get("status") in ACTIVE
            for e in old.entities.values()
        ):
            raise ValueError("Finish or cancel the other active collaboration first")
        if fingerprint(old) != original.data["fingerprint"]:
            raise ValueError("Design inputs changed; start a new collaboration from current inputs")
        if original.data.get("round", 0) >= 3:
            raise ValueError(
                "Three revision rounds reached; start a new collaboration after resolving this proposal"
            )
        if (
            original.data.get("study") in ["data-system", "cross-discipline"]
            and request.minimum_duty is not None
            and request.minimum_duty > original.data["bounds"]["duty_max"]
        ):
            raise ValueError(
                "Minimum duty exceeds this study's bounds; start a new study to change bounds"
            )
        if len(request.feedback.strip()) < 3:
            raise ValueError("Describe the clarification in at least three characters")
        m = old.model_copy(deep=True)
        run = get_run(m, run_id)
        data = run.data
        stop_execution(
            run,
            "Revision requested; automatic progression must be started explicitly for the new round",
        )
        history = {
            key: deepcopy(data.get(key))
            for key in [
                "round",
                "proposal_id",
                "payload",
                "bus",
                "evaluate_payload",
                "evaluate_bus",
                "minimum_duty",
                "systems_review",
                "review_usage",
                "selected_alternative",
            ]
        }
        data.setdefault("round_history", []).append(history)
        if proposal:
            m.proposals[proposal_id].status = "superseded"
        feedback = dict(
            text=request.feedback.strip(),
            challenge=next(
                (
                    e["summary"]
                    for e in reversed(data["events"])
                    if e["type"] == "challenge"
                    and (e.get("evidence") or {}).get("proposal_id") == proposal_id
                ),
                None,
            ),
            previous_proposal=proposal_id,
            source_revision=old.revision,
        )
        data.setdefault("clarifications", []).append(feedback)
        data["minimum_duty"] = (
            request.minimum_duty if request.minimum_duty is not None else data.get("minimum_duty")
        )
        for key in [
            "payload",
            "bus",
            "evaluate_payload",
            "evaluate_bus",
            "systems_review",
            "review_usage",
            "selected_alternative",
        ]:
            data.pop(key, None)
        data.update(
            round=data.get("round", 0) + 1,
            stage="payload",
            status="ready",
            completed=[],
            attempts=0,
            proposal_id=None,
        )
        record(
            run,
            "clarification",
            "human",
            "payload",
            request.feedback.strip(),
            {"previous_proposal": proposal_id, "minimum_duty": data["minimum_duty"]},
        )
        return self.store.save(m, "human", "Requested collaboration revision", old)

    def begin_execution(self, mission_id, run_id, revision):
        old = self.store.get(mission_id)
        self.workflow.guard(old, revision)
        self.workflow.no_pending(old)
        run = get_run(old, run_id)
        if old.paused or run.data["status"] != "ready" or run.data["attempts"] >= 10:
            raise ValueError(
                "Automatic progression requires a resumed, ready task; retry failures explicitly"
            )
        if run.data.get("execution", {}).get("status") == "running":
            raise ValueError(
                "Automatic progression already claimed; recover an expired checkpoint or cancel"
            )
        if fingerprint(old) != run.data["fingerprint"]:
            raise ValueError("Design changed; start a new collaboration")
        m = old.model_copy(deep=True)
        run = get_run(m, run_id)
        run.data["execution"] = dict(
            id=str(uuid4()), status="running", started_at=now(), lease_expires_at=lease_deadline()
        )
        record(
            run,
            "execution_started",
            "human",
            "orchestrator",
            "Run remaining tasks until review, pause, cancellation or failure. No automatic approval or retry.",
        )
        return self.store.save(m, "human", "Requested automatic collaboration progression", old)

    def recovery(self, mission_id, run_id):
        model = self.store.get(mission_id)
        return recovery_details(model, get_run(model, run_id))

    def recover(self, mission_id, run_id, request):
        old = self.store.get(mission_id)
        self.workflow.guard(old, request.revision)
        run = get_run(old, run_id)
        details = recovery_details(old, run)
        if not details["available"]:
            raise ValueError(details["reason"])
        if details["requires_confirmation"] and not request.retry_uncertain:
            raise ValueError(
                "The previous model call has an unknown outcome and may already have incurred a charge. Explicitly confirm retry before recovering."
            )
        if any(
            e.id != run_id
            and e.data.get("workflow") == "duty-collaboration"
            and e.data.get("status") in ACTIVE
            for e in old.entities.values()
        ):
            raise ValueError("Finish or cancel the other active collaboration first")
        m = old.model_copy(deep=True)
        run = get_run(m, run_id)
        previous_attempt = run.data.get("attempt")
        stop_execution(run, "Expired execution superseded by explicit checkpoint recovery")
        run.data.update(status="ready", attempt=str(uuid4()), task_lease=None)
        record(
            run,
            "recovered",
            "human",
            "orchestrator",
            "Checkpoint recovered without executing work. Completed tasks and evidence are preserved; explicitly run the next task or run until review.",
            {
                "previous_attempt": previous_attempt,
                "completed": list(run.data["completed"]),
                "unknown_model_outcome": details["requires_confirmation"],
                "retry_confirmed": request.retry_uncertain,
            },
        )
        return self.store.save(m, "human", "Recovered interrupted collaboration checkpoint", old)

    def execute_remaining(self, mission_id, run_id, execution_id):
        # The durable claim fences competing requests. The worker is deliberately bounded
        # to one round, with no retries, auto-approval or restart after a server crash.
        reason = "Round requires review"
        try:
            for _ in range(len(STAGES)):
                current = self.store.get(mission_id)
                run = get_run(current, run_id)
                execution = run.data.get("execution", {})
                if execution.get("id") != execution_id or execution.get("status") != "running":
                    return
                if lease_expired(execution.get("lease_expires_at")):
                    return  # Preserve the expired claim for explicit recovery, never replay work.
                if current.archived or current.baseline:
                    return
                if current.paused:
                    reason = "Mission paused; resume and explicitly run again to continue"
                    break
                if run.data["status"] != "ready":
                    reason = f"Stopped for {run.data['status']}; human action required"
                    break
                if any(p.status in ["submitted", "challenged"] for p in current.proposals.values()):
                    reason = "Resolve pending proposals before continuing"
                    break
                self.step(mission_id, run_id, current.revision, execution_id)
        except Exception:
            reason = "Execution interrupted; reload and inspect the run. Retry explicitly or cancel; no task was automatically retried."
        # A concurrent mutation can win this bookkeeping write. Never overwrite it;
        # an uncleared claim can be recovered after expiry or cancelled.
        try:
            current = self.store.get(mission_id)
            run = get_run(current, run_id)
            execution = run.data.get("execution", {})
            if (
                current.archived
                or current.baseline
                or execution.get("id") != execution_id
                or execution.get("status") != "running"
            ):
                return
            updated = current.model_copy(deep=True)
            run = get_run(updated, run_id)
            run.data["execution"].update(status="stopped", finished_at=now(), reason=reason)
            record(run, "execution_stopped", "orchestrator", "human", reason)
            advance_pending_metadata(updated)
            self.store.save(updated, "orchestrator", "Automatic progression stopped", current)
        except Exception:
            return

    def step(self, mission_id, run_id, revision, execution_id=None):
        old = self.store.get(mission_id)
        self.workflow.guard(old, revision)
        self.workflow.no_pending(old)
        run = get_run(old, run_id)
        execution = run.data.get("execution", {})
        if execution_id is not None:
            if execution.get("id") != execution_id or execution.get("status") != "running":
                raise ValueError("Execution claim is no longer active")
            if lease_expired(execution.get("lease_expires_at")):
                raise ValueError("Execution lease expired; recover from the saved checkpoint")
        elif execution.get("status") == "running":
            raise ValueError(
                "Automatic progression owns this run; pause or cancel before manual work"
            )
        if old.paused:
            raise ValueError("Workflow paused; resume before the next collaboration step")
        if run.data["status"] not in ["ready", "failed"] or run.data["attempts"] >= 10:
            raise ValueError(
                "Run cannot advance; recover an expired checkpoint, or cancel and start a new run"
            )
        m = old.model_copy(deep=True)
        run = get_run(m, run_id)
        if fingerprint(old) != run.data["fingerprint"]:
            run.data["status"] = "stale"
            record(
                run,
                "stale",
                "orchestrator",
                "human",
                "Design changed. Start a new collaboration from current inputs.",
            )
            return self.store.save(m, "orchestrator", "Collaboration source became stale", old)
        blocked = run_budget.reason(run.data, before=True)
        if blocked:
            run.data["status"] = "budget_blocked"
            record(run, "budget_blocked", "orchestrator", "human", blocked)
            stop_execution(run, blocked)
            return self.store.save(m, "orchestrator", "Collaboration budget blocked task", old)
        stage = run.data["stage"]
        attempt = str(uuid4())
        run_budget.reserve(run.data, attempt)
        run.data.update(
            status="working",
            attempt=attempt,
            attempts=run.data["attempts"] + 1,
            task_lease=lease_deadline(),
        )
        if run.data.get("execution", {}).get("status") == "running":
            run.data["execution"]["lease_expires_at"] = run.data["task_lease"]
        record(
            run,
            "started",
            "orchestrator",
            stage,
            "Executing one bounded task; no accepted design inputs are changed.",
        )
        started = self.store.save(m, "orchestrator", "Collaboration task started", old)
        timer = perf_counter()
        error = False
        try:
            result = self.perform(started, get_run(started, run_id))
        except Exception:
            error = True
            result = None
        # Re-read after a provider/tool call. Pause/cancel/edit may have occurred meanwhile.
        current = self.store.get(mission_id)
        current_run = get_run(current, run_id)
        if current_run.data.get("attempt") != attempt or current_run.data["status"] != "working":
            return current
        if current.archived or current.baseline:
            return current  # Recover after expiry and restoring/reopening, or cancel.
        updated = current.model_copy(deep=True)
        run = get_run(updated, run_id)
        elapsed = perf_counter() - timer
        run_budget.settle(run.data, attempt, result, elapsed)
        blocked = run_budget.reason(run.data)
        if blocked:
            run.data["status"] = "budget_blocked"
            record(run, "budget_blocked", "orchestrator", "human", blocked)
        elif lease_expired(run.data.get("task_lease")):
            run.data["status"] = "interrupted"
            record(
                run,
                "interrupted",
                "orchestrator",
                "human",
                "Task lease expired; late response discarded. Recover the checkpoint explicitly before retrying.",
            )
        elif fingerprint(current) != run.data["fingerprint"]:
            run.data["status"] = "stale"
            record(
                run,
                "stale",
                "orchestrator",
                "human",
                "Source changed during execution; response discarded.",
            )
        elif error:
            run.data["status"] = "failed"
            record(
                run,
                "failed",
                stage,
                "human",
                "Task failed validation or execution. Check provider configuration and inputs; retry explicitly or cancel.",
            )
        elif stage == "systems" and (
            current.paused
            or any(p.status in ["submitted", "challenged"] for p in current.proposals.values())
        ):
            run.data["status"] = "ready"
            record(
                run,
                "blocked",
                "systems",
                "human",
                "Resume and resolve pending proposals before submission.",
            )
        else:
            try:
                self.finish(updated, run, stage, result)
            except Exception:
                updated = current.model_copy(deep=True)
                run = get_run(updated, run_id)
                run_budget.settle(run.data, attempt, result, elapsed)
                run.data["status"] = "failed"
                record(
                    run,
                    "failed",
                    stage,
                    "human",
                    "Result could not be validated or submitted; retry explicitly or cancel.",
                )
        run.data["events"][-1]["elapsed_seconds"] = perf_counter() - timer
        if run.data["status"] not in ["ready", "working"]:
            stop_execution(
                run, f"Stopped for {run.data['status']}: {run.data['events'][-1]['summary']}"
            )
        # Compare-and-swap preserves concurrent mutations; a losing worker cannot overwrite them.
        if run.data["status"] != "interrupted":
            run.data["task_lease"] = None
        if run.data.get("execution", {}).get("status") == "running":
            run.data["execution"]["lease_expires_at"] = lease_deadline()
        advance_pending_metadata(updated)
        return self.store.save(updated, "orchestrator", "Collaboration task result", current)

    def perform(self, model, run):
        data = run.data
        stage = data["stage"]
        if (
            data["mode"] == "live"
            and stage in ["payload", "bus", "systems"]
            and os.getenv("LLM_MODEL") != data["provider_model"]
        ):
            raise ValueError("Provider model changed; start a new run")
        if data.get("study") in ["data-system", "cross-discipline"]:
            return data_alternatives.perform(data, model.brief)
        if stage in ["payload", "bus"]:
            context = dict(
                brief=model.brief,
                goal=data["goal"],
                candidate=data["candidate"],
                inputs=data["inputs"],
                clarifications=data.get("clarifications", []),
                previous_proposal=data.get("round_history", [{}])[-1].get("bus"),
                minimum_duty=data.get("minimum_duty"),
                previous_review=data.get("round_history", [{}])[-1].get("systems_review"),
            )
            if stage == "bus":
                context.update(
                    payload_proposal=data["payload"], evaluation=data["evaluate_payload"]
                )
            proposal, usage = propose(stage, context, data["mode"])
            return dict(proposal=proposal.model_dump(), usage=usage)
        if stage.startswith("evaluate_"):
            author = stage.removeprefix("evaluate_")
            values = deepcopy(data["inputs"]["data"])
            values["duty"] = dict(value=data[author]["duty"], unit="dimensionless")
            calculated = execute("data", values, data["source_revision"])
            link = execute(
                "link",
                {**data["inputs"]["link"], "demand": calculated["outputs"].get("daily")},
                data["source_revision"],
            )
            return dict(data=calculated, link=link)
        if stage == "systems":
            # Failing deterministic evidence never incurs a model review or bypasses the gate.
            minimum = data.get("minimum_duty")
            if (minimum is not None and data["bus"]["duty"] < minimum) or not all(
                data["evaluate_bus"][t]["outputs"].get("compliant") is True
                for t in ["data", "link"]
            ):
                return None
            context = dict(
                mission_goal={
                    "brief": model.brief,
                    "goal": data["goal"],
                    "candidate": data["candidate"],
                },
                owner_feedback={
                    "clarifications": data.get("clarifications", []),
                    "minimum_duty": minimum,
                },
                payload_proposal=data["payload"],
                bus_proposal=data["bus"],
                data_analysis=data["evaluate_bus"]["data"],
                link_analysis=data["evaluate_bus"]["link"],
            )
            assessment, usage = review(context, data["mode"])
            return {"review": assessment.model_dump(), "usage": usage, "context": context}
        return None

    def finish(self, model, run, stage, result):
        data = run.data
        if data.get("study") in ["data-system", "cross-discipline"]:
            if data_alternatives.finish(model, run, stage, result, record):
                data["completed"].append(stage)
                if stage != "systems":
                    data.update(stage=STAGES[STAGES.index(stage) + 1], status="ready")
            return
        if stage in ["payload", "bus"]:
            data[stage] = result["proposal"]
            record(
                run,
                "proposal" if stage == "payload" else "response",
                stage,
                "tools",
                result["proposal"]["rationale"],
                result,
            )
        elif stage.startswith("evaluate_"):
            data[stage] = result
            if any(result[t]["status"] != "valid" for t in ["data", "link"]):
                data["status"] = "failed"
                record(
                    run,
                    "failed",
                    "tools",
                    "human",
                    "Tool inputs could not be evaluated. Inspect the recorded errors; retry or cancel.",
                    result,
                )
                return
            passed = all(result[t]["outputs"]["compliant"] for t in ["data", "link"])
            record(
                run,
                "tool_result",
                "tools",
                "bus" if stage == "evaluate_payload" else "systems",
                "Declared data and link constraints pass."
                if passed
                else "Data or downlink constraint fails; revision or owner review is needed.",
                result,
            )
        else:
            evidence = data["evaluate_bus"]
            minimum = data.get("minimum_duty")
            if minimum is not None and data["bus"]["duty"] < minimum:
                data["status"] = "blocked"
                record(
                    run,
                    "blocked",
                    "systems",
                    "human",
                    "Proposed duty is below the owner's minimum. Clarify the goal or request another revision; no change submitted.",
                    {"minimum_duty": minimum, "proposed_duty": data["bus"]["duty"]},
                )
                return
            if not all(evidence[t]["outputs"]["compliant"] for t in ["data", "link"]):
                data["status"] = "blocked"
                record(
                    run,
                    "blocked",
                    "systems",
                    "human",
                    "Bus proposal still fails data/link constraints. Inspect evidence and start a revised study; no change submitted.",
                )
                return
            assessment = SystemsReview.model_validate(result["review"])
            data["systems_review"] = assessment.model_dump()
            data["review_usage"] = result["usage"]
            record(
                run,
                "systems_review",
                "systems",
                "human" if assessment.recommendation != "revise" else "bus",
                assessment.rationale,
                result,
            )
            if assessment.recommendation != "submit":
                data["status"] = "blocked"
                record(
                    run,
                    "revision_requested"
                    if assessment.recommendation == "revise"
                    else "clarification_requested",
                    "systems",
                    "human",
                    assessment.follow_up,
                    {"recommendation": assessment.recommendation},
                )
                return
            prior = model.entities[data["input_id"]]
            duty = data["bus"]["duty"]
            if fraction(prior.data["inputs"]["duty"]) == duty:
                data["status"] = "completed"
                record(
                    run,
                    "completed",
                    "systems",
                    "human",
                    "Reviewed duty already equals the accepted input; no change required.",
                )
            else:
                values = deepcopy(data["inputs"]["data"])
                values["duty"] = dict(value=duty, unit="dimensionless")
                edited = edited_entity(prior, EditChanges(inputs=values))
                edited.owner = "systems"
                proposal = Proposal(
                    proposal_type="design change",
                    agent="systems",
                    target_revision=model.revision,
                    operations=[Operation(action="replace", entity=edited)],
                    rationale=data["bus"]["rationale"]
                    + "\nSystems review: "
                    + assessment.rationale,
                    evidence_references=[run.id],
                    expected_consequences="Change observation duty only; all dependent calculations and selection require review. Science adequacy and operational delivery are not certified.",
                    confidence=0.5,
                )
                validate(model, proposal)
                proposal.target_revision += 1
                model.proposals[proposal.id] = proposal
                data.update(proposal_id=proposal.id, status="awaiting_approval")
                record(
                    run,
                    "approval_requested",
                    "systems",
                    "human",
                    "Review the proposed duty change and science trade-off. Accepted inputs remain unchanged.",
                    {"proposal_id": proposal.id, "duty": duty},
                )
            data["completed"].append(stage)
            return
        data["completed"].append(stage)
        data.update(stage=STAGES[STAGES.index(stage) + 1], status="ready")
