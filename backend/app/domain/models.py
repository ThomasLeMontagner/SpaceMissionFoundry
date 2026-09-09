from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


def now() -> str:
    return datetime.now(UTC).isoformat()


class Classification(StrEnum):
    FACT = "Sourced fact"
    CALCULATION = "Deterministic calculation"
    ESTIMATE = "Engineering estimate"
    ANALOGY = "Analogy"
    ASSUMPTION = "Explicit assumption"
    HUMAN = "Human decision"
    UNKNOWN = "Unknown"


Kind = Literal[
    "Mission",
    "Objective",
    "Requirement",
    "Function",
    "Component",
    "Interface",
    "Parameter",
    "Budget",
    "BudgetEntry",
    "Claim",
    "Evidence",
    "Assumption",
    "AnalysisRun",
    "ArchitectureAlternative",
    "TradeStudy",
    "Proposal",
    "Decision",
    "ReviewFinding",
    "Risk",
    "VerificationItem",
    "AgentDefinition",
    "AgentRun",
    "ModelRevision",
    "Baseline",
    "DomainEvent",
]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Relation(Strict):
    type: Literal[
        "derives_from",
        "allocated_to",
        "satisfies",
        "verifies",
        "depends_on",
        "evidenced_by",
        "contains",
        "connects",
        "supersedes",
    ]
    target: str


class Entity(Strict):
    id: str = Field(default_factory=lambda: str(uuid4()))
    kind: Kind
    title: str = Field(min_length=1)
    state: Literal[
        "proposed",
        "accepted",
        "rejected",
        "open",
        "resolved",
        "verified",
        "closed",
        "waived",
        "stale",
        "superseded",
    ] = "accepted"
    owner: str
    created_at: str = Field(default_factory=now)
    modified_at: str = Field(default_factory=now)
    revision: int = 0
    classification: Classification = Classification.ASSUMPTION
    relations: list[Relation] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def required_fields(self):
        required = {
            "Requirement": ["rationale", "source", "level", "priority", "verification_method"],
            "Assumption": ["rationale", "impact", "confidence", "validation_plan"],
            "Interface": ["endpoints", "exchanges", "direction", "medium", "constraints"],
            "ReviewFinding": ["severity", "resolution"],
            "Decision": ["rationale", "alternatives", "consequences"],
            "TradeStudy": ["criteria", "weights", "scores", "recommendation", "dissent"],
        }
        missing = set(required.get(self.kind, [])) - self.data.keys()
        if missing:
            raise ValueError(f"{self.kind} missing fields: {sorted(missing)}")
        return self


class Operation(Strict):
    action: Literal["add", "replace"]
    entity: Entity


class Proposal(Strict):
    created_at: str = Field(default_factory=now)
    modified_at: str = Field(default_factory=now)
    revision: int = 0
    owner: str = ""
    id: str = Field(default_factory=lambda: str(uuid4()))
    proposal_type: str
    agent: str
    agent_version: str = "1.0"
    target_revision: int = Field(ge=0)
    operations: list[Operation] = Field(min_length=1, max_length=100)
    rationale: str = Field(min_length=1)
    evidence_references: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    expected_consequences: str
    confidence: float = Field(ge=0, le=1)
    requested_reviewers: list[str] = Field(default_factory=lambda: ["human"])
    status: Literal["submitted", "challenged", "accepted", "rejected", "superseded"] = "submitted"

    @model_validator(mode="after")
    def identity(self):
        self.owner = self.agent
        return self


class Model(Strict):
    schema_version: str = "1.0"
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    brief: str
    owner: str = "human"
    created_at: str = Field(default_factory=now)
    modified_at: str = Field(default_factory=now)
    revision: int = 0
    phase: str = "Brief"
    entities: dict[str, Entity] = Field(default_factory=dict)
    proposals: dict[str, Proposal] = Field(default_factory=dict)
    selected: str | None = None
    baseline: str | None = None
    paused: bool = False
    steps: int = 0
