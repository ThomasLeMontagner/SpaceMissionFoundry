from copy import deepcopy
from typing import Literal

from pydantic import Field, field_validator

from app.domain.engineering_inputs import validate_inputs
from app.domain.models import Strict
from app.orchestration.scenario import Q, entity, inputs

CANDIDATES = ("wide", "selective")
BUDGET_TOOLS = ("mass", "power", "data", "link")
IMPACT_KINDS = {
    "Objective",
    "Requirement",
    "Assumption",
    "Parameter",
    "ArchitectureAlternative",
    "Function",
    "Component",
    "Interface",
    "Risk",
}


class EditChanges(Strict):
    title: str | None = Field(default=None, min_length=1, max_length=2000)
    inputs: dict | None = None
    rationale: str | None = Field(default=None, min_length=1, max_length=2000)
    impact: str | None = Field(default=None, min_length=1, max_length=2000)
    confidence: float | None = Field(default=None, ge=0, le=1)
    validation_plan: str | None = Field(default=None, min_length=1, max_length=2000)
    priority: Literal["must", "should", "could"] | None = None
    level: Literal["stakeholder", "system", "subsystem"] | None = None
    verification_method: (
        Literal["analysis", "test", "inspection", "demonstration", "review"] | None
    ) = None

    @field_validator("title", "rationale", "impact", "validation_plan")
    @classmethod
    def nonempty_text(cls, value):
        if value is not None:
            value = value.strip()
            if not value:
                raise ValueError("Engineering text cannot be blank")
        return value


def parameter_id(candidate, tool):
    return f"{candidate}-{tool}-inputs"


def input_entities(model=None):
    """Seed only at proposal time, or explicitly lift a legacy run's recorded inputs."""
    records = []
    historical = model is not None and any(e.kind == "AnalysisRun" for e in model.entities.values())
    groups = [("mission", "orbit", {"altitude": Q(550, "km")}, ["orbit-assumption"])]
    for candidate in CANDIDATES:
        for tool, values in inputs(candidate).items():
            groups.append((candidate, tool, values, ["resources", "operations", "observation"]))
    for candidate, tool, values, refs in groups:
        if historical:
            analysis = model.entities.get(f"{candidate}-{tool}-analysis")
            if not analysis or analysis.data.get("status") != "valid":
                raise ValueError(
                    "Legacy inputs are missing; no scenario defaults will be substituted"
                )
            values = deepcopy(analysis.data["inputs"])
            for derived in ("period", "eclipse", "demand"):
                values.pop(derived, None)
        records.append(
            entity(
                parameter_id(candidate, tool),
                "Parameter",
                f"{candidate} · {tool} inputs",
                refs=refs,
                tool=tool,
                candidate=candidate,
                inputs=validate_inputs(tool, values),
                input_schema="1.0",
                rationale="Explicit sizing assumptions; reviewed before deterministic calculation",
            )
        )
    return records


def read_inputs(model, candidate, tool):
    parameter = model.entities.get(parameter_id(candidate, tool))
    if not parameter or parameter.kind != "Parameter" or parameter.state != "accepted":
        raise ValueError(f"Missing or unreviewed input group: {candidate} / {tool}")
    if parameter.data.get("tool") != tool or parameter.data.get("candidate") != candidate:
        raise ValueError("Input group identity mismatch")
    return validate_inputs(tool, parameter.data["inputs"])


def edited_entity(prior, changes: EditChanges):
    allowed = {
        "Parameter": {"inputs"},
        "Assumption": {"title", "rationale", "impact", "confidence", "validation_plan"},
        "Requirement": {"title", "rationale", "priority", "level", "verification_method"},
    }
    values = changes.model_dump(exclude_unset=True)
    if not values or any(v is None for v in values.values()):
        raise ValueError("Provide at least one nonempty edit")
    if prior.kind not in allowed or set(values) - allowed[prior.kind]:
        raise ValueError("This field is not editable for this object type")
    e = prior.model_copy(deep=True)
    for key, value in values.items():
        if key == "title":
            e.title = value.strip()
        else:
            e.data[key] = value
    if e.data == prior.data and e.title == prior.title:
        raise ValueError("No design changes were supplied")
    if e.kind == "Parameter":
        e.data["inputs"] = validate_inputs(e.data["tool"], e.data["inputs"])
    e.owner = "human"
    e.state = "proposed"
    return e
