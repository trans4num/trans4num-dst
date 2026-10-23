from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import Field, field_validator
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


class OptimizationSettings(BaseSchema):
    max_time_seconds: float = Field(default=720, gt=0, allow_inf_nan=False)
    relative_gap: float = Field(default=0.05, ge=0, le=1, allow_inf_nan=False)
    workers: int = Field(default=4, ge=0)
    max_memory_mb: int = Field(default=8192, gt=0)
    use_linear_relaxation: bool = True
    use_fast_path: bool = True
    debug: bool = False
    max_fractional_iterations: int = Field(default=64, ge=1)


class OptimizationResult(BaseSchema):
    method: str
    status: Literal["optimal", "feasible", "missing"]
    termination_reason: str
    objective: float | None = None
    best_bound: float | None = None
    relative_gap: float | None = None
    objective_name: str | None = None
    objective_unit: str | None = None
    iterations: int = 1
    max_time_seconds: float
    requested_relative_gap: float
    workers: int
    preparation_seconds: float = 0
    model_build_seconds: float = 0
    solve_seconds: float = 0
    load_seconds: float = 0
    output_seconds: float = 0


class SimulationBase(BaseSchema):
    name: str
    region_id: UUID
    model: Optional[Model] = None
    optimization_settings: OptimizationSettings | None = None


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
    optimization: OptimizationResult | None = None
    error_message: str | None = None

    @field_validator("summary", mode="before")
    @classmethod
    def normalize_legacy_summary(cls, value):
        if isinstance(value, dict):
            return [
                {"name": name, "value": metric, "unit": ""}
                for name, metric in value.items()
            ]
        return value
