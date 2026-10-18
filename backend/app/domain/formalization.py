"""Owner-assessed criterion scope, bound to the exact reviewed statement and rule."""

from typing import Literal

from pydantic import Field, field_validator, model_validator

from app.domain.models import Strict
from app.domain.requirement_checks import Criterion


class Formalization(Strict):
    statement: str = Field(min_length=1, max_length=10000)
    criterion: Criterion | None
    coverage: Literal["partial", "full"]
    basis: str = Field(min_length=3, max_length=2000)
    open_questions: list[str] = Field(default_factory=list, max_length=10)
    clarification_ids: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("basis")
    @classmethod
    def basis_nonblank(cls, value):
        if len(value.strip()) < 3:
            raise ValueError("Explain why this metric applies and what remains unresolved")
        return value.strip()

    @field_validator("open_questions")
    @classmethod
    def questions(cls, values):
        if any(not v.strip() or len(v) > 1000 for v in values):
            raise ValueError("Questions must be nonblank and at most 1,000 characters")
        return list(dict.fromkeys(v.strip() for v in values))

    @model_validator(mode="after")
    def full_scope(self):
        if self.coverage == "full" and (self.criterion is None or self.open_questions):
            raise ValueError("Full coverage requires a criterion and no unresolved questions")
        return self


def apply_scope(requirement, result):
    raw = requirement.data.get("formalization")
    if raw is None:
        result["criterion_coverage"] = "legacy_unassessed"
        return
    try:
        scope = Formalization.model_validate(raw)
        rule = scope.criterion.model_dump() if scope.criterion else None
        current = scope.statement == requirement.title and rule == requirement.data.get("criterion")
        result["criterion_coverage"] = scope.coverage if current else "needs_review"
        result["open_questions"] = scope.open_questions
        complete = current and scope.coverage == "full"
    except ValueError:
        result["criterion_coverage"] = "needs_review"
        complete = False
    if not complete and result["status"] == "pass":
        result.update(
            numeric_status="pass",
            status="unverified",
            reason="The numeric check passes, but its coverage of the complete requirement is partial or needs review. Resolve questions and submit a new formalization for approval.",
        )
