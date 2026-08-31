from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import field_validator
from shared_datamodel.schema import BaseSchema


class Variable(Enum):
    CROP = "crop"
    ECONOMY = "economy"
    NLOAD = "nload"
    NATURE = "nature"


class SimulationStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PROCESSING = "processing"


class SimulationGoalType(Enum):
    MAX_ECONOMY = "maximizeEconomy"
    MAX_ECON_PER_NLOAD = "maximizeEconomyNLoad"
    MIN_NLOAD = "minimizeNLoad"


class ModelConstraint(BaseSchema):
    name: str
    enabled: bool
    value: float
    range: tuple[float, float]
    unit: str


class BarChartData(BaseSchema):
    name: str
    values: dict[str, float]


class BarChart(BaseSchema):
    chartName: str
    unit: str
    chartData: list[BarChartData]


class SimulationGoal(BaseSchema):
    name: str
    description: str
    type: SimulationGoalType
    configuration: List[ModelConstraint]


class Model(BaseSchema):
    goal: SimulationGoal
    constraints: List[ModelConstraint]


class Chart(BaseSchema):
    name: str
    values: dict[str, float]


class SimulationBase(BaseSchema):
    name: str
    region_id: UUID
    model: Optional[Model] = None


class SummaryEntry(BaseSchema):
    name: str
    value: float
    unit: str


class Simulation(SimulationBase):
    id: UUID
    created: datetime
    status: SimulationStatus
    deleted: bool = False
    summary: list[SummaryEntry]
    charts: list[Chart]
    barCharts: list[BarChart] = []

    @field_validator("summary", mode="before")
    @classmethod
    def normalize_legacy_summary(cls, value):
        if isinstance(value, dict):
            return [
                {"name": name, "value": metric, "unit": ""}
                for name, metric in value.items()
            ]
        return value
