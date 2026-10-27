"""Bounded owner-authored requirements, awaiting separate human approval."""

from typing import Literal

from pydantic import Field, field_validator

from app.domain.models import Classification, Relation, Strict
from app.orchestration.scenario import entity


class RequirementDraft(Strict):
    statement: str = Field(min_length=3, max_length=2000)
    rationale: str = Field(min_length=3, max_length=2000)
    source: str = Field(min_length=3, max_length=2000)
    level: Literal["stakeholder", "system", "subsystem"] = "system"
    priority: Literal["must", "should", "could"] = "must"
    verification_method: Literal["analysis", "test", "inspection", "demonstration", "review"] = (
        "review"
    )
    parent_ids: list[str] = Field(min_length=1, max_length=20)

    @field_validator("statement", "rationale", "source")
    @classmethod
    def meaningful_text(cls, value):
        if len(value.strip()) < 3:
            raise ValueError("Provide nonblank statement, source and rationale")
        return value.strip()

    @field_validator("parent_ids")
    @classmethod
    def distinct_parents(cls, values):
        if len(set(values)) != len(values) or any(not v.strip() or len(v) > 200 for v in values):
            raise ValueError("Parent IDs must be distinct and nonblank")
        return sorted(values)


def make_requirement(identifier, draft):
    item = entity(
        identifier,
        "Requirement",
        draft.statement,
        "human",
        **draft.model_dump(exclude={"statement", "parent_ids"}),
        criterion=None,
        formalization=dict(
            statement=draft.statement,
            criterion=None,
            coverage="partial",
            basis="Owner-authored requirement; verification scope has not been assessed.",
            open_questions=[
                "Which criterion, conditions and evidence will verify this requirement?"
            ],
            clarification_ids=[],
        ),
    )
    item.state = "proposed"
    item.relations = [Relation(type="derives_from", target=key) for key in draft.parent_ids]
    return item


def validate_creation(model, proposal):
    if proposal.agent != "human" or len(proposal.operations) != 1:
        raise ValueError("Manual creation requires one owner-authored requirement")
    op = proposal.operations[0]
    item = op.entity
    if op.action != "add" or item.kind != "Requirement" or item.id in model.entities:
        raise ValueError("Manual creation must add a new requirement")
    draft = RequirementDraft(
        statement=item.title,
        parent_ids=[r.target for r in item.relations if r.type == "derives_from"],
        **{
            key: item.data.get(key)
            for key in ("rationale", "source", "level", "priority", "verification_method")
        },
    )
    expected = make_requirement(item.id, draft)
    if (
        item.title != expected.title
        or item.data != expected.data
        or item.relations != expected.relations
        or item.owner != "human"
        or item.classification != Classification.ASSUMPTION
        or item.state != "proposed"
    ):
        raise ValueError("Manual requirements must retain their unverified draft and parent links")
