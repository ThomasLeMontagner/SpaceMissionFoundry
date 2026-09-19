from pydantic import Field, model_validator

from app.domain.engineering_inputs import Quantity
from app.domain.models import Strict
from app.engineering_tools.calculations import q


class DataContract(Strict):
    source_endpoint: str = Field(min_length=1, max_length=120)
    sink_endpoint: str = Field(min_length=1, max_length=120)
    source_protocol: str | None = Field(default=None, max_length=120)
    sink_protocol: str | None = Field(default=None, max_length=120)
    source_rate: Quantity | None = None
    sink_capacity: Quantity | None = None

    @model_validator(mode="after")
    def units(self):
        for value in (self.source_rate, self.sink_capacity):
            if value is not None:
                try:
                    q(value.model_dump(), "bit/s")
                except Exception as exc:
                    raise ValueError(
                        "Data interface rates must use compatible nonnegative bit/s units"
                    ) from exc
        return self
