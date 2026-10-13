from dataclasses import dataclass
from enum import Enum

from shared_datamodel.simulation import OptimizationResult


class SolutionType(Enum):
    OPTIMAL = "optimal"
    FEASIBLE = "feasible"
    MISSING = "MISSING"


@dataclass
class Solution:
    success: bool
    result: None | list
    description: str
    type: SolutionType
    objective: float | None = None
    bound: float | None = None
    method: str = "cp-sat"
    termination_reason: str = "unknown"
    preparation_seconds: float = 0
    model_build_seconds: float = 0
    solve_seconds: float = 0

    def quality(self, settings, load_seconds=0) -> OptimizationResult:
        return OptimizationResult(
            method=self.method,
            status=self.type.value.lower(),
            termination_reason=self.termination_reason,
            objective=self.objective,
            best_bound=self.bound,
            relative_gap=relative_gap(self.objective, self.bound) if self.objective is not None and self.bound is not None else None,
            max_time_seconds=settings.max_time_seconds,
            requested_relative_gap=settings.relative_gap,
            workers=settings.workers,
            preparation_seconds=self.preparation_seconds,
            model_build_seconds=self.model_build_seconds,
            solve_seconds=self.solve_seconds,
            load_seconds=load_seconds,
        )


def relative_gap(objective: float, bound: float) -> float:
    """CP-SAT's normalized gap, defined for signed and zero objectives."""
    return max(0.0, objective - bound) / max(1.0, abs(objective))
