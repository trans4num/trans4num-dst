"""Shared coefficients for model building and specialized optimization methods."""
import math
import operator
from dataclasses import dataclass

from shared_datamodel.simulation import SimulationGoalType
from models.denmark.constraints.accumulated_change import AccumulatedChangeConstraint
from models.denmark.constraints.grouped_accumulated_change import GroupedAccumulatedChangeConstraint
from models.denmark.things import CropRotation, Field
from models.denmark.transitions import Transition, f


@dataclass(frozen=True)
class Choice:
    rotation: CropRotation
    cost: float
    coefficients: tuple[int, ...]


@dataclass
class PreparedProblem:
    fields: dict[str, Field]
    choices: dict[str, list[Choice]]
    constraints: list
    goal_type: SimulationGoalType


def prepare_problem(fields, constraints, ignore_constraints, goal_type, prune=True):
    choices = {}
    # Custom constraint types are not assumed to support dominance pruning.
    can_prune = prune and all(
        type(c) in (AccumulatedChangeConstraint, GroupedAccumulatedChangeConstraint)
        and c.operator in (operator.le, operator.ge)
        for c in constraints
    )
    for key, entry in fields.items():
        allowed = all(c.allow(entry) for c in ignore_constraints)
        candidates = []
        rotations = {}
        for rotation in entry.choices + [entry.rotation]:
            existing = rotations.get(rotation.name)
            if existing is not None and existing.indices != rotation.indices:
                raise ValueError(f"Different rotations share the name {rotation.name!r} on {key}")
            rotations[rotation.name] = rotation
        # The existing rotation remains a valid option, even for frozen fields.
        rotations[entry.rotation.name] = entry.rotation
        for rotation in rotations.values():
            if not allowed and rotation.name != entry.rotation.name:
                continue
            if goal_type == SimulationGoalType.MIN_NLOAD:
                cost = f(rotation, Transition.LEACHING, entry.spatial_indicator)
            elif goal_type == SimulationGoalType.MAX_ECONOMY:
                cost = -f(rotation, Transition.ECONOMY, entry.spatial_indicator)
            elif goal_type == SimulationGoalType.MAX_ECON_PER_NLOAD:
                cost = f(rotation, Transition.LEACHING, entry.spatial_indicator) / f(
                    rotation, Transition.ECONOMY, entry.spatial_indicator
                )
            else:
                raise ValueError(f"Unknown goal type: {goal_type}")
            if not math.isfinite(cost):
                raise ValueError(f"Non-finite objective for {key}: {rotation.name}")
            candidates.append(Choice(rotation, cost, tuple(c.coefficient(rotation, entry) for c in constraints)))
        if can_prune:
            directions = [1 if c.operator == operator.le else -1 for c in constraints]
            vectors = [(p.cost,) + tuple(d * v for d, v in zip(directions, p.coefficients)) for p in candidates]
            # Compare every active constraint, including per-farmer constraints,
            # using the same integer coefficients as the general solver.
            candidates = [p for i, p in enumerate(candidates) if p.rotation.name == entry.rotation.name or not any(
                all(a <= b for a, b in zip(other, vectors[i]))
                and any(a < b for a, b in zip(other, vectors[i]))
                for j, other in enumerate(vectors) if i != j
            )]
        choices[key] = candidates
    return PreparedProblem(fields, choices, constraints, goal_type)


def is_feasible(problem: PreparedProblem, selection: dict[str, Choice]) -> bool:
    if set(selection) != set(problem.fields):
        return False
    for index, constraint in enumerate(problem.constraints):
        totals = {}
        for key, choice in selection.items():
            if choice not in problem.choices[key]:
                return False
            field = problem.fields[key]
            if type(constraint) is GroupedAccumulatedChangeConstraint:
                group = constraint.grouper(field)
                limit = int(constraint.get_max_change(field) * constraint.scale)
            elif type(constraint) is AccumulatedChangeConstraint:
                group = None
                limit = int(constraint.max_change * constraint.scale)
            else:
                return False
            value, group_limit = totals.get(group, (0, limit))
            totals[group] = (value + choice.coefficients[index], group_limit)
        if not all(constraint.operator(value, limit) for value, limit in totals.values()):
            return False
    return all(choice in problem.choices[key] for key, choice in selection.items())
