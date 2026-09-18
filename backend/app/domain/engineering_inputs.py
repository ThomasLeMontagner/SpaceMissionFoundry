"""Validated, editable calculator inputs. Derived values are deliberately excluded."""

from typing import Literal

from pint.errors import PintError
from pydantic import Field

from app.domain.models import Strict
from app.engineering_tools.calculations import U, fraction, q


class Quantity(Strict):
    value: float = Field(ge=0, strict=True)
    unit: str = Field(max_length=40)


class MassEntry(Strict):
    name: str = Field(min_length=1, max_length=80)
    mass: Quantity


class Mode(Strict):
    name: str = Field(min_length=1, max_length=80)
    fraction: Quantity
    loads: dict[str, Quantity] = Field(min_length=1, max_length=30)


class MassInputs(Strict):
    entries: list[MassEntry] = Field(min_length=1, max_length=40)
    margin: Quantity
    limit: Quantity


class PowerInputs(Strict):
    modes: list[Mode] = Field(min_length=1, max_length=20)
    solar: Quantity
    battery: Quantity
    depth_of_discharge: Quantity
    eclipse_load: Quantity


class DataInputs(Strict):
    rate: Quantity
    duty: Quantity
    compression: Quantity
    storage: Quantity


class LinkInputs(Strict):
    frequency: Quantity
    range: Quantity
    rate: Quantity
    tx_power: Quantity
    tx_gain_db: Quantity
    rx_gain_db: Quantity
    loss_db: Quantity
    required_ebn0_db: Quantity
    noise_temperature: Quantity
    contact: Quantity
    efficiency: Quantity


class OrbitInputs(Strict):
    altitude: Quantity


class DeliveryInputs(Strict):
    onboard_delay: Quantity
    ground_delay: Quantity
    dissemination_delay: Quantity


class Angle(Strict):
    value: float = Field(strict=True)
    unit: Literal["deg", "degree", "rad", "radian"]


class Site(Strict):
    name: str = Field(min_length=1, max_length=80)
    latitude: Angle
    longitude: Angle


class AccessInputs(Strict):
    inclination: Angle
    raan: Angle
    argument_of_latitude: Angle
    earth_rotation_angle: Angle
    duration: Quantity
    step: Quantity
    footprint_width: Quantity
    minimum_elevation: Angle
    targets: list[Site] = Field(min_length=1, max_length=12)
    stations: list[Site] = Field(min_length=1, max_length=8)


Tool = Literal["mass", "power", "data", "link", "orbit", "access", "delivery"]
INPUT_SCHEMAS = {
    "mass": MassInputs,
    "power": PowerInputs,
    "data": DataInputs,
    "link": LinkInputs,
    "orbit": OrbitInputs,
    "access": AccessInputs,
    "delivery": DeliveryInputs,
}


def validate_inputs(tool: str, inputs: dict) -> dict:
    if tool not in INPUT_SCHEMAS:
        raise ValueError("Unsupported editable calculator")
    values = INPUT_SCHEMAS[tool].model_validate(inputs).model_dump()
    units = {
        "mass": {"limit": "kg", "margin": ""},
        "power": {"solar": "W", "battery": "Wh", "depth_of_discharge": "", "eclipse_load": "W"},
        "data": {"rate": "bit/s", "duty": "", "compression": "", "storage": "bit"},
        "link": {
            "frequency": "Hz",
            "range": "m",
            "rate": "bit/s",
            "tx_power": "W",
            "tx_gain_db": "",
            "rx_gain_db": "",
            "loss_db": "",
            "required_ebn0_db": "",
            "noise_temperature": "K",
            "contact": "s",
            "efficiency": "",
        },
        "orbit": {"altitude": "m"},
        "access": {"duration": "s", "step": "s", "footprint_width": "km"},
        "delivery": {"onboard_delay": "s", "ground_delay": "s", "dissemination_delay": "s"},
    }
    try:
        converted = {key: q(values[key], unit) for key, unit in units[tool].items()}
        for key in ["margin", "depth_of_discharge", "duty", "efficiency"]:
            if key in values:
                fraction(values[key])
        if tool == "mass":
            if len({e["name"] for e in values["entries"]}) != len(values["entries"]):
                raise ValueError("Mass entry names must be unique")
            for entry in values["entries"]:
                q(entry["mass"], "kg")
        if tool == "power":
            if abs(sum(fraction(m["fraction"]) for m in values["modes"]) - 1) > 1e-6:
                raise ValueError("Operational mode fractions must sum to one")
            for mode in values["modes"]:
                for load in mode["loads"].values():
                    q(load, "W")
        if tool == "data" and converted["compression"] < 1:
            raise ValueError("Compression ratio must be at least one")
        if tool == "link":
            if any(
                converted[k] <= 0
                for k in ["frequency", "range", "rate", "tx_power", "noise_temperature"]
            ):
                raise ValueError("RF inputs must be positive")
            if converted["contact"] > 86400:
                raise ValueError("Daily ground contact cannot exceed 24 hours")
        if tool == "orbit" and converted["altitude"] <= 0:
            raise ValueError("Orbit altitude must be positive")
        if tool == "delivery" and any(value > 604800 for value in converted.values()):
            raise ValueError("Each delivery delay must be at most 7 days")
        if tool == "access":

            def angle(value, lower, upper):
                number = U.Quantity(value["value"], value["unit"]).to("degree").magnitude
                if not lower <= number <= upper:
                    raise ValueError(f"Angle must be between {lower} and {upper} degrees")

            angle(values["inclination"], 0, 180)
            for key in ["raan", "argument_of_latitude", "earth_rotation_angle"]:
                angle(values[key], 0, 360)
            angle(values["minimum_elevation"], 0, 90)
            if not 60 <= converted["duration"] <= 604800:
                raise ValueError("Analysis duration must be between 1 minute and 7 days")
            if not 1 <= converted["step"] <= 60:
                raise ValueError("Sampling step must be between 1 and 60 seconds")
            if converted["duration"] / converted["step"] > 100000:
                raise ValueError(
                    "Analysis exceeds the 100,000 sample limit; reduce duration or increase step"
                )
            if not 1 <= converted["footprint_width"] <= 2000:
                raise ValueError("Footprint width must be between 1 and 2000 km")
            for group in ["targets", "stations"]:
                if len({s["name"].strip() for s in values[group]}) != len(values[group]):
                    raise ValueError("Site names must be unique within each group")
                for site in values[group]:
                    if not site["name"].strip():
                        raise ValueError("Site names cannot be blank")
                    angle(site["latitude"], -90, 90)
                    angle(site["longitude"], -180, 180)
    except PintError as exc:
        raise ValueError(f"Incompatible or unknown input units: {exc}") from None
    return values
