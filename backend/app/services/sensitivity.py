"""Read-only, one-parameter delivery studies anchored to current recorded evidence."""

from copy import deepcopy
from typing import Literal

from pydantic import Field

from app.domain.engineering_inputs import Quantity, validate_inputs
from app.domain.models import Strict, now
from app.engineering_tools.calculations import execute, q
from app.engineering_tools.delivery import assess_deadline

PARAMETERS = {
    "storage": ("payload", "storage", "bit"),
    "downlink_rate": ("link", "rate", "bit/s"),
    "onboard_delay": ("delays", "onboard_delay", "s"),
    "ground_delay": ("delays", "ground_delay", "s"),
    "dissemination_delay": ("delays", "dissemination_delay", "s"),
}


class Study(Strict):
    revision: int = Field(ge=0)
    candidate: Literal["wide", "selective"]
    parameter: Literal[
        "storage", "downlink_rate", "onboard_delay", "ground_delay", "dissemination_delay"
    ]
    values: list[Quantity] = Field(min_length=2, max_length=15)
    deadline: Quantity | None = None


def study(model, request: Study):
    if model.revision != request.revision:
        raise ValueError("Mission changed; reload before running a sensitivity study")
    candidate = request.candidate
    source = model.entities.get(f"{candidate}-delivery-analysis")
    if not source or source.state != "accepted" or source.data.get("status") != "valid":
        raise ValueError(
            "Current valid delivery evidence is required; approve inputs and recalculate first"
        )
    group, field, unit = PARAMETERS[request.parameter]
    original = deepcopy(source.data["inputs"])
    products = sum(len(target["windows"]) for target in original["access"]["targets"])
    if products * (len(request.values) + 1) > 50000:
        raise ValueError(
            "Study exceeds 50,000 product cases; use fewer trial values or a shorter access horizon"
        )
    values = [v.model_dump() for v in request.values]
    try:
        converted = [q(v, unit) for v in values]
        deadline = q(request.deadline.model_dump(), "s") if request.deadline else None
    except Exception as exc:
        raise ValueError("Trial values and deadline must use compatible nonnegative units") from exc
    if len(set(converted)) != len(converted):
        raise ValueError("Choose distinct trial values after unit conversion")
    for value in values:
        changed = deepcopy(original[group])
        changed[field] = value
        validate_inputs({"payload": "data", "link": "link", "delays": "delivery"}[group], changed)
    rules = [
        e
        for e in model.entities.values()
        if e.kind == "Requirement"
        and e.state == "accepted"
        and (e.data.get("criterion") or {}).get("metric") == "delivery.maximum_latency"
    ]

    def run(value, reference=False):
        inputs = deepcopy(original)
        inputs[group][field] = value
        # Rate changes affect Eb/N0 as well as capacity. Never reuse the old RF margin.
        data = execute("data", inputs["payload"], model.revision)
        link = execute(
            "link", {**inputs["link"], "demand": data["outputs"].get("daily")}, model.revision
        )
        inputs["link_result"] = link["outputs"]
        delivery = execute("delivery", inputs, model.revision)
        result = dict(
            value=value,
            reference=reference,
            status=delivery["status"],
            data_analysis=data,
            link_analysis=link,
            delivery_analysis=delivery,
            deadline_check=None,
            requirement_checks=[],
        )
        if delivery["status"] == "valid":
            outputs = delivery["outputs"]
            if deadline is not None:
                result["deadline_check"] = assess_deadline(outputs, deadline)
            result["requirement_checks"] = [
                dict(
                    requirement=e.id,
                    title=e.title,
                    criterion=e.data["criterion"],
                    **assess_deadline(outputs, q(e.data["criterion"]["threshold"], "s")),
                )
                for e in rules
            ]
        return result

    return dict(
        schema_version="1.0",
        tool="delivery-sensitivity",
        version="1.0",
        timestamp=now(),
        mission_id=model.id,
        source_revision=model.revision,
        baseline_id=model.baseline,
        source_analysis_id=source.id,
        source_analysis_revision=source.revision,
        candidate=candidate,
        parameter=request.parameter,
        unit=unit,
        deadline=request.deadline.model_dump() if request.deadline else None,
        reference=run(original[group][field], True),
        trials=[run(value) for value in values],
        limitations=[
            "Exploratory one-parameter study; no design inputs, requirement conclusions, mission history or baselines are changed.",
            "Each trial reruns daily data and RF calculations before delivery. Higher downlink rates can reduce RF margin and prevent transmission.",
            "Geometry and all other recorded assumptions remain fixed. Delivery retains its finite-horizon, target-window workload and FIFO limitations.",
            "The optional study deadline is exploratory. Requirement comparisons use accepted numeric criteria but do not replace approved verification evidence.",
            "Results are held in this view; export JSON to retain the study. Apply chosen inputs separately through the reviewed design-edit workflow.",
        ],
    )
