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
    economy: float | None = None
    nload: float | None = None


@dataclass
class PreparedProblem:
    fields: dict[str, Field]
    choices: dict[str, list[Choice]]
    constraints: list
    goal_type: SimulationGoalType
    minimum_economy: float | None = None


class InfeasibleConstraints(ValueError):
    pass


def constraint_rows(problem):
    """Known additive scopes; custom constraint implementations opt out."""
    for index, constraint in enumerate(problem.constraints):
        if type(constraint) not in (AccumulatedChangeConstraint, GroupedAccumulatedChangeConstraint):
            continue
        groups, limits = {}, {}
        for key, field in problem.fields.items():
            group = constraint.grouper(field) if type(constraint) is GroupedAccumulatedChangeConstraint else None
            groups.setdefault(group, []).append(key)
            limits.setdefault(group, constraint.limit(field))
        for group, keys in groups.items():
            yield index, constraint, group, keys, limits[group]


def propagate_constraints(problem, max_passes=8):
    """Remove options that cannot satisfy even one additive row.

    This is necessary-condition propagation, not a claim that the surviving
    model is feasible. CP-SAT still checks all rows, including custom ones.
    """
    for _ in range(max_passes):
        changed = False
        for index, constraint, group, keys, limit in constraint_rows(problem):
            if constraint.operator not in (operator.le, operator.ge):
                continue
            mins = {key: min(choice.coefficients[index] for choice in problem.choices[key]) for key in keys}
            maxs = {key: max(choice.coefficients[index] for choice in problem.choices[key]) for key in keys}
            minimum, maximum = sum(mins.values()), sum(maxs.values())
            if (constraint.operator == operator.le and minimum > limit) or (
                    constraint.operator == operator.ge and maximum < limit):
                label = getattr(constraint, "name", f"Constraint {index + 1}")
                scope = f" for {group}" if group is not None else ""
                raise InfeasibleConstraints(
                    f"{label}{scope} cannot be satisfied: attainable range "
                    f"[{minimum / constraint.scale:.6g}, {maximum / constraint.scale:.6g}], "
                    f"required {'at most' if constraint.operator == operator.le else 'at least'} {limit / constraint.scale:.6g}"
                )
            for key in keys:
                choices = problem.choices[key]
                kept = [choice for choice in choices if (
                    minimum - mins[key] + choice.coefficients[index] <= limit
                    if constraint.operator == operator.le else
                    maximum - maxs[key] + choice.coefficients[index] >= limit
                )]
                if len(kept) != len(choices):
                    problem.choices[key] = kept
                    changed = True
        if not changed:
            break
    return problem


def prepare_problem(fields, constraints, ignore_constraints, goal_type, prune=True):
    choices = {}
    # Custom constraint types are not assumed to support dominance pruning.
    can_prune = prune and all(
        type(c) in (AccumulatedChangeConstraint, GroupedAccumulatedChangeConstraint)
        and c.operator in (operator.le, operator.ge)
        for c in constraints
    )
    for key, entry in fields.items():
        frozen = any(getattr(c, "freeze_field", None) is not None and c.freeze_field(entry) for c in constraints)
        allowed = not frozen and all(c.allow(entry) for c in ignore_constraints)
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
            economy = nload = None
            if goal_type == SimulationGoalType.MIN_NLOAD:
                cost = f(rotation, Transition.LEACHING, entry.spatial_indicator)
            elif goal_type == SimulationGoalType.MAX_ECONOMY:
                cost = -f(rotation, Transition.ECONOMY, entry.spatial_indicator)
            elif goal_type == SimulationGoalType.MAX_ECON_PER_NLOAD:
                economy = f(rotation, Transition.ECONOMY, entry.spatial_indicator)
                nload = f(rotation, Transition.LEACHING, entry.spatial_indicator)
                if not math.isfinite(economy) or not math.isfinite(nload) or nload < 0:
                    raise ValueError(f"Regional ratio requires finite economy and nonnegative N-load: {key}")
                # The ratio is formed from REGIONAL totals in the fractional
                # pipeline. No field-level ratio is ever used as a cost.
                cost = 0.0
            else:
                raise ValueError(f"Unknown goal type: {goal_type}")
            if not math.isfinite(cost):
                raise ValueError(f"Non-finite objective for {key}: {rotation.name}")
            candidates.append(Choice(rotation, cost, tuple(c.coefficient(rotation, entry) for c in constraints), economy, nload))
        if can_prune:
            directions = [1 if c.operator == operator.le else -1 for c in constraints]
            vectors = [((-p.economy, p.nload) if goal_type == SimulationGoalType.MAX_ECON_PER_NLOAD else (p.cost,))
                       + tuple(d * v for d, v in zip(directions, p.coefficients)) for p in candidates]
            # Compare every active constraint, including per-farmer constraints,
            # using the same integer coefficients as the general solver.
            candidates = [p for i, p in enumerate(candidates) if p.rotation.name == entry.rotation.name or not any(
                all(a <= b for a, b in zip(other, vectors[i]))
                and any(a < b for a, b in zip(other, vectors[i]))
                for j, other in enumerate(vectors) if i != j
            )]
        choices[key] = candidates
    return propagate_constraints(PreparedProblem(fields, choices, constraints, goal_type))


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
                limit = constraint.limit(field)
            elif type(constraint) is AccumulatedChangeConstraint:
                group = None
                limit = constraint.limit()
            else:
                return False
            value, group_limit = totals.get(group, (0, limit))
            totals[group] = (value + choice.coefficients[index], group_limit)
        if not all(constraint.operator(value, limit) for value, limit in totals.values()):
            return False
    return all(choice in problem.choices[key] for key, choice in selection.items())
