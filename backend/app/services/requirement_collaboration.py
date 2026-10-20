"""Manually advanced, durable requirement collaboration with sourced criterion choices."""

import os
from time import perf_counter
from typing import Literal
from uuid import uuid4

from pydantic import Field

from app.agents.requirement_provider import perform
from app.domain.models import Strict
from app.domain.requirement_checks import Criterion
from app.orchestration.scenario import entity
from app.services import run_budget
from app.services.collaboration import record
from app.services.execution_recovery import lease_deadline, lease_expired
from app.services.formalization import Formalizer, Submit, inspect
from app.services.workflow import Workflow

WORKFLOW = "requirement-collaboration"
ACTIVE = {"ready", "working", "awaiting_answers", "review_ready", "failed"}


class Start(Strict):
    revision: int = Field(ge=0)
    requirement_id: str
    mode: Literal["simulation", "live"] = "simulation"
    limits: run_budget.Limits = Field(default_factory=run_budget.Limits)


class Answers(Strict):
    revision: int = Field(ge=0)
    answers: list[str] = Field(min_length=1, max_length=25)
    criterion: Criterion | None = None


class Retry(Strict):
    revision: int = Field(ge=0)
    acknowledge_unknown: bool = Field(default=False, strict=True)


def get_run(model, ident):
    run = model.entities.get(ident)
    if not run or run.kind != "AgentRun" or run.data.get("workflow") != WORKFLOW:
        raise ValueError("Requirement collaboration does not belong to this mission")
    return run


def current_source(model, data):
    req = model.entities.get(data["input_id"])
    return req and req.model_dump(mode="json") == data["source_requirement"]


class RequirementCollaboration:
    def __init__(self, store):
        self.store, self.workflow = store, Workflow(store)

    def load(self, mission_id, ident, revision, source=True):
        model = self.store.get(mission_id)
        self.workflow.guard(model, revision)
        self.workflow.no_pending(model)
        if model.paused:
            raise ValueError("Resume the mission before continuing")
        run = get_run(model, ident)
        if source and not current_source(model, run.data):
            raise ValueError("Requirement changed; cancel and start a new collaboration")
        return model, run

    def start(self, mission_id, request):
        model, requirement = Formalizer(self.store).source(
            mission_id, request.requirement_id, request.revision
        )
        if model.paused:
            raise ValueError("Resume the mission before starting")
        if any(
            e.data.get("workflow") == WORKFLOW and e.data.get("status") in ACTIVE
            for e in model.entities.values()
        ):
            raise ValueError("Finish or cancel the active requirement collaboration first")
        if request.mode == "live" and os.getenv("LLM_PROVIDER", "mock") != "openai-compatible":
            raise ValueError("Configure an openai-compatible provider before live execution")
        criteria = {}
        if requirement.data.get("criterion"):
            criteria["accepted-criterion"] = dict(
                criterion=Criterion.model_validate(requirement.data["criterion"]).model_dump(),
                source="Existing accepted requirement criterion; scope still requires review",
            )
        suggestion = inspect(requirement)["suggestion"]
        if suggestion:
            criteria["literal-deadline"] = dict(
                criterion=suggestion["criterion"], source=suggestion["source_quote"]
            )
        notes = [
            e
            for e in model.entities.values()
            if e.data.get("workflow") == "requirement-formalization"
            and e.data.get("requirement_id") == requirement.id
            and e.data.get("source_requirement") == requirement.model_dump(mode="json")
        ]
        note_ids = [e.id for e in notes]
        superseded = {e.data.get("reply_to") for e in notes}
        notes = [e for e in notes if e.id not in superseded]
        m = model.model_copy(deep=True)
        run = entity(
            str(uuid4()),
            "AgentRun",
            "Requirement clarification collaboration",
            "orchestrator",
            workflow=WORKFLOW,
            version="1.0",
            status="ready",
            stage="mission",
            mode=request.mode,
            input_id=requirement.id,
            source_requirement=requirement.model_dump(mode="json"),
            source_revision=model.revision,
            criteria=criteria,
            source_questions=list(
                dict.fromkeys(
                    [
                        *(n.data["question"] for n in notes if not n.data["answer"]),
                        *(requirement.data.get("formalization") or {}).get("open_questions", []),
                    ]
                )
            ),
            note_ids=note_ids,
            notes=[
                dict(id=n.id, question=n.data["question"], answer=n.data["answer"]) for n in notes
            ],
            answers=[],
            pending_questions=[],
            events=[],
            round=0,
            attempts=0,
            attempt=None,
            task_lease=None,
            provider_model=os.getenv("LLM_MODEL") if request.mode == "live" else "simulation",
            budget=run_budget.create(request.limits, request.mode),
        )
        record(
            run,
            "created",
            "human",
            "mission",
            "Started bounded requirement clarification; each task requires an explicit action. No automatic approval.",
        )
        m.entities[run.id] = run
        return self.store.save(m, "human", "Started requirement collaboration", model)

    def answer(self, mission_id, ident, request):
        model, old = self.load(mission_id, ident, request.revision)
        d = old.data
        if d["status"] != "awaiting_answers" or d["round"] >= 3:
            raise ValueError(
                "Answers require a waiting run with fewer than three clarification rounds"
            )
        if len(request.answers) != len(d["pending_questions"]) or any(
            len(a.strip()) < 3 or len(a) > 2000 for a in request.answers
        ):
            raise ValueError("Answer every pending question with 3–2,000 characters")
        m = model.model_copy(deep=True)
        run = get_run(m, ident)
        run.data["answers"].extend(
            dict(question=q, answer=a.strip())
            for q, a in zip(d["pending_questions"], request.answers)
        )
        if request.criterion:
            run.data["criteria"]["owner-criterion"] = dict(
                criterion=request.criterion.model_dump(),
                source="Explicit owner-supplied criterion in clarification round "
                + str(d["round"] + 1),
            )
        run.data.update(
            status="ready", stage="formalize", round=d["round"] + 1, pending_questions=[]
        )
        record(
            run,
            "clarification",
            "human",
            "formalize",
            "Owner answered all pending questions; Systems must assess applicability.",
            {
                "answers": run.data["answers"][-len(request.answers) :],
                "criterion": request.criterion.model_dump() if request.criterion else None,
            },
        )
        return self.store.save(m, "human", "Recorded requirement answers", model)

    def cancel(self, mission_id, ident, revision):
        model = self.store.get(mission_id)
        self.workflow.guard(model, revision)
        old = get_run(model, ident)
        if old.data["status"] not in ACTIVE:
            raise ValueError("Only active requirement runs can be cancelled")
        m = model.model_copy(deep=True)
        run = get_run(m, ident)
        run.data.update(status="cancelled", attempt=None)
        record(
            run,
            "cancelled",
            "human",
            "orchestrator",
            "Cancelled; late responses cannot change this run.",
        )
        # Cancellation during unrelated pending approval must not invalidate it.
        from app.services.collaboration import advance_pending_metadata

        advance_pending_metadata(m)
        return self.store.save(m, "human", "Cancelled requirement collaboration", model)

    def retry(self, mission_id, ident, request):
        model, old = self.load(mission_id, ident, request.revision)
        d = old.data
        if d["status"] != "failed" and not (
            d["status"] == "working" and lease_expired(d["task_lease"])
        ):
            raise ValueError("Retry requires a failed task or expired checkpoint")
        if d["mode"] == "live" and not request.acknowledge_unknown:
            raise ValueError(
                "A previous call may have incurred a charge; acknowledge its unknown outcome before retrying"
            )
        if d["attempts"] >= 10:
            raise ValueError("Attempt limit reached; cancel this run")
        m = model.model_copy(deep=True)
        run = get_run(m, ident)
        run.data.update(status="ready", attempt=None, task_lease=None)
        record(
            run,
            "recovered",
            "human",
            "orchestrator",
            "Prepared explicit retry; completed results and conservative usage reservations remain recorded.",
        )
        return self.store.save(m, "human", "Prepared requirement task retry", model)

    def step(self, mission_id, ident, revision):
        model, old = self.load(mission_id, ident, revision)
        d = old.data
        if d["status"] != "ready" or d["attempts"] >= 10:
            raise ValueError(
                "Run the next task only from a ready checkpoint with attempts remaining"
            )
        if d["mode"] == "live" and os.getenv("LLM_MODEL") != d["provider_model"]:
            raise ValueError("Provider model changed; restore it or start a new run")
        reason = run_budget.reason(d, before=True)
        if reason:
            raise ValueError(reason)
        m = model.model_copy(deep=True)
        run = get_run(m, ident)
        attempt = str(uuid4())
        run.data.update(
            status="working",
            attempt=attempt,
            task_lease=lease_deadline(),
            attempts=d["attempts"] + 1,
        )
        run_budget.reserve(run.data, attempt)
        record(run, "started", "orchestrator", d["stage"], "Started " + d["stage"] + " task")
        self.store.save(m, "orchestrator", "Claimed requirement task", model)
        context = {
            k: run.data.get(k)
            for k in [
                "source_requirement",
                "criteria",
                "notes",
                "answers",
                "mission",
                "proposal",
                "review",
            ]
        }
        started = perf_counter()
        try:
            result, usage = perform(d["stage"], context, d["mode"])
            if (
                d["stage"] == "formalize"
                and result.criterion_id is not None
                and result.criterion_id not in d["criteria"]
            ):
                raise ValueError("Agent selected an unsourced criterion")
            failure = None
        except Exception:
            result, usage, failure = (
                None,
                None,
                "Task failed provider or contract validation. No requirement changed. Retry explicitly or cancel.",
            )
        latest = self.store.get(mission_id)
        latest_run = get_run(latest, ident)
        if latest_run.data["attempt"] != attempt or latest_run.data["status"] != "working":
            return latest
        # Pause, edits, pending approvals and expired leases fence completion. The
        # reserved checkpoint remains recoverable; no late result is applied.
        if (
            latest.archived
            or latest.baseline
            or latest.paused
            or not current_source(latest, latest_run.data)
            or lease_expired(latest_run.data["task_lease"])
            or any(p.status in ["submitted", "challenged"] for p in latest.proposals.values())
        ):
            return latest
        m = latest.model_copy(deep=True)
        run = get_run(m, ident)
        run_budget.settle(run.data, attempt, {"usage": usage or {}}, perf_counter() - started)
        failure = failure or run_budget.reason(run.data)
        if failure:
            run.data.update(status="failed", error=failure)
            record(run, "failed", d["stage"], "human", failure)
        else:
            payload = result.model_dump()
            stage = d["stage"]
            record(
                run,
                "completed",
                stage,
                "human" if stage == "review" else "formalize" if stage == "mission" else "review",
                payload.get("summary") or payload.get("basis") or payload["rationale"],
                payload,
            )
            if stage == "mission":
                questions = list(dict.fromkeys([*result.questions, *d["source_questions"]]))
                run.data.update(
                    mission=payload,
                    pending_questions=questions,
                    status="awaiting_answers" if questions else "ready",
                    stage="formalize",
                )
            elif stage == "formalize":
                run.data.update(proposal=payload, stage="review", status="ready")
            else:
                has_criterion = bool(run.data["proposal"]["criterion_id"])
                questions = result.questions or (
                    []
                    if has_criterion
                    else ["Provide an explicit supported criterion or cancel this unresolved run."]
                )
                run.data.update(
                    review=payload,
                    pending_questions=questions,
                    status="review_ready"
                    if result.recommendation == "submit" and has_criterion
                    else "awaiting_answers",
                )
        return self.store.save(m, "orchestrator", "Recorded requirement task result", latest)

    def submit(self, mission_id, ident, revision):
        model, run = self.load(mission_id, ident, revision)
        d = run.data
        if (
            d["status"] != "review_ready"
            or d["review"]["recommendation"] != "submit"
            or d["pending_questions"]
        ):
            raise ValueError(
                "Independent review must recommend submission with no pending questions"
            )
        # New owner-guided questions recorded after start must not be ignored.
        known = set(d["note_ids"])
        if any(
            e.data.get("workflow") == "requirement-formalization"
            and e.data.get("requirement_id") == d["input_id"]
            and e.data.get("source_requirement") == d["source_requirement"]
            and e.id not in known
            for e in model.entities.values()
        ):
            raise ValueError("Clarification history changed; start a new run to include it")
        answered = {a["question"] for a in d["answers"]}
        if any(q not in answered for q in d["source_questions"]):
            raise ValueError("Answer all source clarification questions before submission")
        choice = d["criteria"][d["proposal"]["criterion_id"]]["criterion"]
        return Formalizer(self.store).propose(
            mission_id,
            d["input_id"],
            Submit(
                revision=revision,
                criterion=choice,
                coverage="partial",
                basis=d["proposal"]["basis"],
                open_questions=d["proposal"]["limitations"],
            ),
            source_run_id=ident,
        )
