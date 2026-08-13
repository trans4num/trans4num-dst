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
