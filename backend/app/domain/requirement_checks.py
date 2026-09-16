"""Typed criteria and a closed registry of preliminary analysis outputs."""

from typing import Literal

from pydantic import model_validator

from app.domain.engineering_inputs import Quantity
from app.domain.models import Strict
from app.engineering_tools.calculations import q

METRICS = {
    "access.contact": {"label": "Network geometric contact within analysis horizon", "unit": "s"},
    "access.observed_fraction": {
        "label": "Fraction of configured target points observed within horizon",
        "unit": "dimensionless",
    },
    "access.largest_target_gap": {
        "label": "Largest target gap within sampled horizon (edge-censored)",
        "unit": "s",
    },
    "mass.total": {"label": "Allocated spacecraft mass", "unit": "kg"},
    "power.average_load": {"label": "Average electrical load", "unit": "W"},
    "power.margin": {"label": "Orbit energy margin", "unit": "Wh"},
    "power.battery_margin": {"label": "Eclipse battery margin", "unit": "Wh"},
    "data.daily": {"label": "Daily generated data", "unit": "bit"},
    "link.capacity": {"label": "Daily downlink capacity", "unit": "bit"},
    "orbit.period": {"label": "Orbital period", "unit": "s"},
    "orbit.eclipse": {"label": "Maximum eclipse duration", "unit": "s"},
}


class Criterion(Strict):
    metric: str
    operator: Literal["<=", ">="]
    threshold: Quantity

    @model_validator(mode="after")
    def compatible(self):
        if self.metric not in METRICS:
            raise ValueError("Unsupported requirement metric")
        try:
            q(self.threshold.model_dump(), METRICS[self.metric]["unit"])
        except Exception as exc:
            raise ValueError(
                "Threshold must use units compatible with the selected metric"
            ) from exc
        return self
