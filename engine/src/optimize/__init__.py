from dataclasses import dataclass
from enum import Enum


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


def relative_gap(objective: float, bound: float) -> float:
    """CP-SAT's normalized gap, defined for signed and zero objectives."""
    return max(0.0, objective - bound) / max(1.0, abs(objective))
