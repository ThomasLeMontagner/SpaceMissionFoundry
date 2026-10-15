"""Explicit incremental concept model. No hardware defaults or savings credits."""

from copy import deepcopy

from pydantic import Field, field_validator

from app.domain.models import Strict
from app.engineering_tools.calculations import execute, q


class ImpactAssumptions(Strict):
    storage_kg_per_gbit: float = Field(ge=0, le=1000, allow_inf_nan=False, strict=True)
    storage_w_per_gbit: float = Field(ge=0, le=1000, allow_inf_nan=False, strict=True)
    observation_w: float = Field(ge=0, le=1000000, allow_inf_nan=False, strict=True)
    processing_w_per_ratio: float = Field(ge=0, le=1000000, allow_inf_nan=False, strict=True)
    basis: str = Field(min_length=3, max_length=1000)

    @field_validator("basis")
    @classmethod
    def nonblank(cls, value):
        if len(value.strip()) < 3:
            raise ValueError("Explain the source and applicability of these assumptions")
        return value.strip()


def derived_inputs(data, option):
    a = ImpactAssumptions.model_validate(data["impact_assumptions"])
    baseline = data["inputs"]["data"]
    storage_delta = max(0, option["storage_gbit"] - q(baseline["storage"], "Gbit"))
    duty_delta = max(0, option["duty"] - q(baseline["duty"], ""))
    # Increment in processing workload, including higher duty at existing compression.
    workload = max(
        0,
        option["duty"] * (option["compression"] - 1)
        - q(baseline["duty"], "") * (q(baseline["compression"], "") - 1),
    )
    average_w = (
        storage_delta * a.storage_w_per_gbit
        + duty_delta * a.observation_w
        + workload * a.processing_w_per_ratio
    )
    # Assume incremental active loads can coincide with eclipse for its entire duration.
    eclipse_w = (
        storage_delta * a.storage_w_per_gbit
        + (a.observation_w if duty_delta > 0 else 0)
        + (max(0, option["compression"] - 1) * a.processing_w_per_ratio if workload > 0 else 0)
    )
    mass = deepcopy(data["inputs"]["mass"])
    power = deepcopy(data["inputs"]["power"])
    kg = storage_delta * a.storage_kg_per_gbit
    if kg:
        mass["entries"].append(
            dict(
                name=f"Storage increment at revision {data['source_revision']}",
                mass=dict(value=kg, unit="kg"),
            )
        )
    if average_w:
        for mode in power["modes"]:
            key = f"study_increment_r{data['source_revision']}"
            if key in mode["loads"]:
                raise ValueError("Increment load identifier already exists")
            mode["loads"][key] = dict(value=average_w, unit="W")
    if eclipse_w:
        power["eclipse_load"] = dict(value=q(power["eclipse_load"], "W") + eclipse_w, unit="W")
    return (
        mass,
        power,
        dict(
            storage_delta_gbit=storage_delta,
            added_mass_kg=kg,
            added_average_w=average_w,
            added_eclipse_w=eclipse_w,
        ),
    )


def evaluate(data, option):
    if not data.get("impact_assumptions"):
        return dict(
            impact_status="unverified",
            blockers=[
                "Missing impact assumptions: provide storage kg/Gbit, storage W/Gbit, observation W, processing W per compression-ratio increment and their basis in a new study."
            ],
            eligible=False,
        )
    mass, power, deltas = derived_inputs(data, option)
    orbital = execute("orbit", data["inputs"]["orbit"], data["source_revision"])
    power = {**power, **{k: orbital["outputs"].get(k) for k in ["period", "eclipse"]}}
    results = {
        name: execute(name, values, data["source_revision"], [data["impact_assumptions"]["basis"]])
        for name, values in [("mass", mass), ("power", power)]
    }
    blockers = [
        f"{name.capitalize()} budget failed or invalid"
        for name, result in results.items()
        if result["status"] != "valid" or result["outputs"].get("compliant") is not True
    ]
    return dict(
        **results,
        impact_status="evaluated",
        impact_deltas=deltas,
        blockers=blockers,
        eligible=not blockers,
    )
