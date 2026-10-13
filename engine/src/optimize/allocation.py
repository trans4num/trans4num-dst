"""A certified relaxation and whole-field repair for one regional constraint.

The general CP-SAT solver remains the fallback. This module only recognizes
plain, additive constraints; grouped/custom constraints never enter this path.
"""
import math
import operator
from dataclasses import dataclass

from shared_datamodel.simulation import SimulationGoalType
from models.denmark.constraints.accumulated_change import AccumulatedChangeConstraint
from models.denmark.prepare import Choice, PreparedProblem, is_feasible


@dataclass
class Allocation:
    selection: dict[str, Choice]
    objective: float
    bound: float
    optimal: bool


def allocate_region(problem: PreparedProblem) -> Allocation | None:
    if problem.goal_type not in (SimulationGoalType.MAX_ECONOMY, SimulationGoalType.MIN_NLOAD):
        return None
    if len(problem.constraints) > 1 or not problem.fields:
        return None
    if problem.constraints:
        constraint = problem.constraints[0]
        if type(constraint) is not AccumulatedChangeConstraint or constraint.operator not in (operator.le, operator.ge):
            return None

    selection = {key: min(choices, key=lambda p: p.cost) for key, choices in problem.choices.items()}
    if is_feasible(problem, selection):
        value = math.fsum(choice.cost for choice in selection.values())
        return Allocation(selection, value, value, True)
    if not problem.constraints:
        return None

    # Normalize either inequality to resource >= target, preserving the integer
    # coefficients/rounding of the CP-SAT model, including negative resources.
    direction = 1 if constraint.operator == operator.ge else -1
    target = direction * int(constraint.max_change * constraint.scale)
    points = {key: [(direction * choice.coefficients[0], choice.cost, index)
                    for index, choice in enumerate(choices)]
              for key, choices in problem.choices.items()}
    if sum(max(point[0] for point in row) for row in points.values()) < target:
        return None

    hulls = {}
    segments = []
    for key, row in points.items():
        by_resource = {}
        for point in row:
            if point[0] not in by_resource or point[1] < by_resource[point[0]][1]:
                by_resource[point[0]] = point
        ordered = sorted(by_resource.values())
        initial = min(ordered, key=lambda p: (p[1], -p[0]))
        hull = []
        for point in ordered:
            if point[0] < initial[0]:
                continue
            while len(hull) >= 2:
                a, b = hull[-2:]
                if (point[1] - b[1]) * (b[0] - a[0]) <= (b[1] - a[1]) * (point[0] - b[0]):
                    hull.pop()
                else:
                    break
            hull.append(point)
        hulls[key] = hull
        for index, (a, b) in enumerate(zip(hull, hull[1:])):
            segments.append(((b[1] - a[1]) / (b[0] - a[0]), key, index))
    segments.sort()

    selected = {key: 0 for key in hulls}
    remaining = target - sum(hull[0][0] for hull in hulls.values())
    multiplier = 0.0
    fractional_key = None
    for slope, key, index in segments:
        if remaining <= 0:
            break
        # Strictly increasing slopes along each field's hull ensure precedence.
        if selected[key] != index:
            return None
        a, b = hulls[key][index:index + 2]
        gain = b[0] - a[0]
        used = min(remaining, gain)
        multiplier = slope
        selected[key] = index + 1
        if used < gain:
            fractional_key = key
        remaining -= used
    if remaining > 0:
        return None

    selected_points = {key: hulls[key][index] for key, index in selected.items()}
    if fractional_key is not None:
        fixed_resource = sum(point[0] for key, point in selected_points.items() if key != fractional_key)
        eligible = [point for point in points[fractional_key] if fixed_resource + point[0] >= target]
        if not eligible:
            return None
        selected_points[fractional_key] = min(eligible, key=lambda p: p[1])
    selection = {key: problem.choices[key][point[2]] for key, point in selected_points.items()}
    if not is_feasible(problem, selection):
        return None
    value = math.fsum(choice.cost for choice in selection.values())

    # Independent Lagrangian lower bound over ALL retained options. This also
    # checks the hull construction: an integral relaxation optimum must match it.
    terms = [min(cost - multiplier * resource for resource, cost, _ in row) for row in points.values()]
    dual = math.fsum(terms) + multiplier * target
    tolerance = 1e-12 * max(1, math.fsum(abs(term) for term in terms), abs(multiplier * target), abs(value))
    if not math.isfinite(dual) or dual > value + tolerance:
        return None
    optimal = fractional_key is None and abs(value - dual) <= tolerance
    bound = value if optimal else min(value, dual - tolerance)
    return Allocation(selection, value, bound, optimal)
