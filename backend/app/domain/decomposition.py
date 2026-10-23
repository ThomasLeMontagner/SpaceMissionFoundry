"""Extractive, source-bound child requirements; no inferred numeric targets or parent roll-up."""

from uuid import uuid4

from pydantic import Field, model_validator

from app.domain.formalization import Formalization
from app.domain.models import Entity, Relation, Strict


class Child(Strict):
    source_ref: str = Field(min_length=1, max_length=80)
    source_quote: str = Field(min_length=3, max_length=1000)
    criterion_id: str | None = Field(default=None, max_length=80)
    rationale: str = Field(min_length=3, max_length=1000)
    unresolved: list[str] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def text(self):
        if (
            len(self.source_quote.strip()) < 3
            or not self.rationale.strip()
            or any(not q.strip() or len(q) > 1000 for q in self.unresolved)
        ):
            raise ValueError(
                "Child statements, rationale and unresolved obligations must be nonblank and bounded"
            )
        return self


class Decomposition(Strict):
    basis: str = Field(min_length=3, max_length=2000)
    children: list[Child] = Field(min_length=2, max_length=5)
    limitations: list[str] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def text(self):
        if not self.basis.strip() or any(not q.strip() or len(q) > 1000 for q in self.limitations):
            raise ValueError("Explain the decomposition and its limitations")
        if len({c.source_quote.strip().casefold() for c in self.children}) != len(self.children):
            raise ValueError("Child statements must be distinct")
        return self


def sources(data):
    return {
        "parent": data["source_requirement"]["title"],
        **{f"answer-{i}": a["answer"] for i, a in enumerate(data.get("answers", []))},
    }


def validate_plan(data, raw):
    plan = Decomposition.model_validate(raw)
    texts = sources(data)
    for child in plan.children:
        if child.source_ref not in texts or child.source_quote not in texts[child.source_ref]:
            raise ValueError(
                "Child statement must quote the parent or a recorded owner answer exactly"
            )
        if child.criterion_id is not None and child.criterion_id not in data["criteria"]:
            raise ValueError("Child criterion must reference a supplied source-backed criterion")
    return plan


def children_exist(model, parent):
    return any(
        e.kind == "Requirement"
        and e.data.get("decomposition", {}).get("parent_id") == parent
        and e.state != "rejected"
        for e in model.entities.values()
    )


def make_child(data, run_id, child, index, ident=None):
    parent = data["source_requirement"]
    criterion = data["criteria"][child.criterion_id]["criterion"] if child.criterion_id else None
    scope = Formalization(
        statement=child.source_quote,
        criterion=criterion,
        coverage="partial",
        basis=child.rationale,
        open_questions=child.unresolved,
    )
    return Entity(
        id=ident or str(uuid4()),
        kind="Requirement",
        title=child.source_quote,
        owner="systems",
        state="proposed",
        classification="Explicit assumption",
        relations=[
            Relation(type="derives_from", target=parent["id"]),
            Relation(type="evidenced_by", target=run_id),
        ],
        data=dict(
            rationale=child.rationale,
            source=f"Requirement decomposition run {run_id}; {child.source_ref}",
            level=parent["data"]["level"],
            priority=parent["data"]["priority"],
            verification_method="analysis" if criterion else "review",
            criterion=criterion,
            formalization=scope.model_dump(),
            decomposition=dict(
                parent_id=parent["id"],
                run_id=run_id,
                index=index,
                source_ref=child.source_ref,
                source_quote=child.source_quote,
                criterion_id=child.criterion_id,
            ),
        ),
    )


def validate_submission(model, proposal):
    refs = [model.entities.get(ref) for ref in proposal.evidence_references]
    runs = [
        r
        for r in refs
        if r
        and r.kind == "AgentRun"
        and r.data.get("workflow") == "requirement-collaboration"
        and r.data.get("study") == "decomposition"
    ]
    if len(runs) != 1 or proposal.agent != "systems":
        raise ValueError("Decomposition must reference its reviewed Systems run")
    run = runs[0]
    d = run.data
    parent = model.entities.get(d["input_id"])
    if (
        not parent
        or parent.model_dump(mode="json") != d["source_requirement"]
        or children_exist(model, parent.id)
    ):
        raise ValueError("Parent changed or already has a decomposition")
    if (
        d["status"] not in ["review_ready", "submitted"]
        or d.get("review", {}).get("recommendation") != "submit"
        or d["pending_questions"]
        or d.get("execution", {}).get("status") == "running"
    ):
        raise ValueError("Decomposition requires completed independent review")
    if d["status"] == "submitted" and d.get("proposal_id") != proposal.id:
        raise ValueError("Decomposition is already submitted")
    plan = validate_plan(d, d["proposal"])
    if len(proposal.operations) != len(plan.children):
        raise ValueError("Decomposition must preserve all reviewed children")
    for i, (op, child) in enumerate(zip(proposal.operations, plan.children)):
        expected = make_child(d, run.id, child, i, op.entity.id)
        fields = {"kind", "title", "state", "owner", "classification", "relations", "data"}
        if op.action != "add" or op.entity.model_dump(include=fields) != expected.model_dump(
            include=fields
        ):
            raise ValueError("Decomposition operations must match the reviewed children exactly")
