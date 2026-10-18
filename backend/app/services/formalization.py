"""Bounded owner-guided formalization. Suggestions are deterministic, never evidence."""

import math
import re
from uuid import uuid4

from pydantic import Field

from app.domain.formalization import Formalization
from app.domain.models import Operation, Proposal, Strict
from app.domain.protocol import validate
from app.domain.requirement_checks import METRICS, Criterion
from app.orchestration.scenario import entity
from app.services.workflow import Workflow


class Note(Strict):
    revision: int = Field(ge=0)
    question: str = Field(min_length=3, max_length=1000)
    answer: str = Field(default="", max_length=2000)
    reply_to: str | None = Field(default=None, max_length=80)


class Submit(Strict):
    revision: int = Field(ge=0)
    criterion: Criterion | None
    coverage: str = "partial"
    basis: str = Field(min_length=3, max_length=2000)
    open_questions: list[str] = Field(default_factory=list, max_length=10)
    clarification_ids: list[str] = Field(default_factory=list, max_length=10)
    confirm_full_coverage: bool = Field(default=False, strict=True)


def inspect(requirement):
    suggestion = None
    # Extract only an explicit acquisition-to-delivery deadline. Never map mass
    # to deployer volume, nor fabricate values for lifetime, quality or cost.
    matches = list(
        re.finditer(
            r"within\s+(\d+(?:\.\d+)?)\s+(seconds?|minutes?|hours?)\s+of\s+acquisition",
            requirement.title,
            re.I,
        )
    )
    if (
        "deliver" in requirement.title.lower()
        and len(matches) == 1
        and math.isfinite(float(matches[0][1]))
    ):
        match = matches[0]
        suggestion = dict(
            criterion=dict(
                metric="delivery.maximum_latency",
                operator="<=",
                threshold=dict(
                    value=float(match[1]),
                    unit={"s": "s", "m": "minute", "h": "hour"}[match[2][0].lower()],
                ),
            ),
            source_quote=match[0],
            coverage="partial",
            explanation="Extracted explicit delivery deadline only. Image usefulness, complete workload and operational applicability still need owner assessment.",
        )
    scope = requirement.data.get("formalization")
    if scope:
        current = scope.get("statement") == requirement.title and scope.get(
            "criterion"
        ) == requirement.data.get("criterion")
        status = scope.get("coverage") if current else "needs_review"
    else:
        status = "unassessed" if requirement.data.get("criterion") else "needs_clarification"
    return dict(
        id=requirement.id,
        title=requirement.title,
        priority=requirement.data.get("priority"),
        status=status,
        criterion=requirement.data.get("criterion"),
        formalization=scope,
        suggestion=suggestion,
        questions=[
            "What observable quantity and threshold would demonstrate this requirement?",
            "Which conditions, workload, horizon and sources justify the criterion?",
            "Which parts of the statement remain outside this calculation?",
        ],
    )


def overview(model):
    requirements = [
        e
        for e in model.entities.values()
        if e.kind == "Requirement" and e.state in ["accepted", "stale"]
    ]
    return dict(
        revision=model.revision,
        metrics=METRICS,
        requirements=[inspect(e) for e in requirements],
        notes=[
            dict(id=e.id, **e.data)
            for e in model.entities.values()
            if e.kind == "AgentRun" and e.data.get("workflow") == "requirement-formalization"
        ],
    )


class Formalizer:
    def __init__(self, store):
        self.store = store
        self.workflow = Workflow(store)

    def source(self, mission_id, requirement_id, revision):
        model = self.store.get(mission_id)
        self.workflow.guard(model, revision)
        self.workflow.no_pending(model)
        requirement = model.entities.get(requirement_id)
        if (
            not requirement
            or requirement.kind != "Requirement"
            or requirement.state not in ["accepted", "stale"]
        ):
            raise ValueError("Choose an accepted or stale requirement")
        return model, requirement

    def note(self, mission_id, requirement_id, request):
        model, requirement = self.source(mission_id, requirement_id, request.revision)
        if len(request.question.strip()) < 3:
            raise ValueError("Describe the clarification question")
        if request.reply_to:
            prior = model.entities.get(request.reply_to)
            if (
                not prior
                or prior.data.get("workflow") != "requirement-formalization"
                or prior.data.get("requirement_id") != requirement_id
                or prior.data.get("source_requirement") != requirement.model_dump(mode="json")
            ):
                raise ValueError("Reply must refer to a clarification of the current requirement")
            if request.question.strip() != prior.data["question"] or not request.answer.strip():
                raise ValueError("Answer the original question without changing it")
            if any(e.data.get("reply_to") == prior.id for e in model.entities.values()):
                raise ValueError("This clarification already has a reply")
        current_notes = [
            e
            for e in model.entities.values()
            if e.data.get("workflow") == "requirement-formalization"
            and e.data.get("requirement_id") == requirement_id
            and e.data.get("source_requirement") == requirement.model_dump(mode="json")
        ]
        superseded = {e.data.get("reply_to") for e in current_notes}
        if not request.reply_to and sum(e.id not in superseded for e in current_notes) >= 10:
            raise ValueError(
                "At most ten clarification questions per requirement revision; answer an existing question"
            )
        updated = model.model_copy(deep=True)
        note = entity(
            str(uuid4()),
            "AgentRun",
            "Owner requirement clarification",
            "human",
            workflow="requirement-formalization",
            version="1.0",
            status="answered" if request.answer.strip() else "open",
            requirement_id=requirement_id,
            source_revision=model.revision,
            source_requirement=requirement.model_dump(mode="json"),
            reply_to=request.reply_to,
            question=request.question.strip(),
            answer=request.answer.strip(),
            mode="owner-guided; no model call",
        )
        updated.entities[note.id] = note
        return self.store.save(
            updated,
            "human",
            "Recorded requirement clarification without changing accepted requirements",
            model,
        )

    def propose(self, mission_id, requirement_id, request):
        model, requirement = self.source(mission_id, requirement_id, request.revision)
        questions = list(request.open_questions)
        current_notes = [
            e
            for e in model.entities.values()
            if e.kind == "AgentRun"
            and e.data.get("workflow") == "requirement-formalization"
            and e.data.get("requirement_id") == requirement_id
            and e.data.get("source_requirement") == requirement.model_dump(mode="json")
        ]
        superseded = {e.data.get("reply_to") for e in current_notes}
        identifiers = list(
            dict.fromkeys(
                [
                    *request.clarification_ids,
                    *(e.id for e in current_notes if e.id not in superseded),
                ]
            )
        )
        for ident in identifiers:
            note = model.entities.get(ident)
            if (
                not note
                or note.data.get("workflow") != "requirement-formalization"
                or note.data.get("requirement_id") != requirement_id
            ):
                raise ValueError("Clarification must belong to this mission and requirement")
            if note.data.get("source_requirement") != requirement.model_dump(mode="json"):
                raise ValueError(
                    "Clarification refers to an earlier requirement; record a new clarification"
                )
            if not note.data["answer"]:
                questions.append(note.data["question"])
        if request.coverage == "full" and not request.confirm_full_coverage:
            raise ValueError("Explicitly confirm that the criterion covers the entire requirement")
        scope = Formalization(
            statement=requirement.title,
            criterion=request.criterion,
            coverage=request.coverage,
            basis=request.basis,
            open_questions=questions,
            clarification_ids=identifiers,
        )
        proposed = requirement.model_copy(deep=True)
        proposed.owner, proposed.state = "human", "proposed"
        proposed.data.update(
            criterion=request.criterion.model_dump() if request.criterion else None,
            formalization=scope.model_dump(),
        )
        if proposed.data == requirement.data:
            raise ValueError("No formalization changes supplied")
        proposal = Proposal(
            agent="human",
            proposal_type="design change",
            target_revision=model.revision,
            operations=[Operation(action="replace", entity=proposed)],
            rationale=request.basis,
            evidence_references=identifiers,
            expected_consequences="Human approval updates criterion and owner-assessed scope, invalidates dependent evidence and requires recalculation. Partial coverage cannot verify the full requirement.",
            confidence=1,
        )
        validate(model, proposal)
        updated = model.model_copy(deep=True)
        proposal.target_revision += 1
        updated.proposals[proposal.id] = proposal
        return self.store.save(
            updated,
            "human",
            "Proposed requirement formalization for separate human approval",
            model,
        )
