"""Dinkelbach optimization of regional N-load / economy (the inverse E/N).

Selections and hard constraints are shared with the additive solver. Bounds
reported here are in ratio units, never in the units of an inner objective.
"""
import math
import operator
import time
from dataclasses import replace

from shared_datamodel.simulation import SimulationGoalType
from models.denmark.constraints.accumulated_change import AccumulatedChangeConstraint
from models.denmark.prepare import PreparedProblem, is_feasible
from models.denmark.transitions import Transition, f
from optimize import Solution, SolutionType


MINIMUM_ECONOMY = 1e-6  # DKK; only used if positivity is not guaranteed by the options.


def enforce_positive_economy(model, problem):
    if not problem.choices:
        return
    minimum = math.fsum(min(choice.economy for choice in choices) for choices in problem.choices.values())
    if minimum > 0:
        problem.minimum_economy = minimum * (1 - 1e-12)
        return
    # Conservative floor coefficients guarantee that even negative individual
    # revenues cannot make an accepted regional denominator zero or negative.
    constraint = AccumulatedChangeConstraint(model, 1, operator.ge,
        lambda rotation, field: math.floor(f(rotation, Transition.ECONOMY, field.spatial_indicator) / MINIMUM_ECONOMY), 1)
    problem.constraints.append(constraint)
    problem.choices = {key: [replace(choice, coefficients=choice.coefficients + (
        math.floor(choice.economy / MINIMUM_ECONOMY),)) for choice in choices]
        for key, choices in problem.choices.items()}
    problem.minimum_economy = MINIMUM_ECONOMY


def ratio_gap(value, bound):
    return max(0.0, value - bound) / value if value > 0 else 0.0


def _selection(problem, names):
    if set(names) != set(problem.fields):
        return None
    result = {}
    for key, choices in problem.choices.items():
        choice = next((choice for choice in choices if choice.rotation.name == names[key]), None)
        if choice is None:
            return None
        result[key] = choice
    return result


def _ratio(selection):
    economy = math.fsum(choice.economy for choice in selection.values())
    nload = math.fsum(choice.nload for choice in selection.values())
    return (nload / economy, economy, nload) if economy > 0 else None


def optimize_fractional(problem, settings, solve_linear):
    best, best_value = None, None
    lower_bound = 0.0
    method, reason = "fractional", "iteration_limit"
    search_seconds = build_seconds = preparation_seconds = 0.0
    iterations = 0
    optimal = False
    if problem.fields:
        baseline = _selection(problem, {key: entry.rotation.name for key, entry in problem.fields.items()})
        if baseline is not None and is_feasible(problem, baseline) and _ratio(baseline) is not None:
            best, best_value = baseline, _ratio(baseline)[0]
    maximum_economy = math.fsum(max(choice.economy for choice in choices) for choices in problem.choices.values())
    if not problem.fields or maximum_economy <= 0:
        reason = "infeasible"
    else:
        minimum_nload = math.fsum(min(choice.nload for choice in choices) for choices in problem.choices.values())
        lower_bound = minimum_nload / (maximum_economy * (1 + 1e-12))
        force_general = False
        for iteration in range(settings.max_fractional_iterations):
            if best_value == 0:
                optimal, reason = True, "optimal"
                break
            remaining = settings.max_time_seconds - search_seconds
            if remaining <= 0:
                reason = "time_limit"
                break
            parameter = best_value if best_value is not None else 0.0
            start = time.perf_counter()
            priced = PreparedProblem(problem.fields, {
                key: [replace(choice, cost=choice.nload - parameter * choice.economy) for choice in choices]
                for key, choices in problem.choices.items()
            }, problem.constraints, SimulationGoalType.MIN_NLOAD)
            preparation_seconds += time.perf_counter() - start
            # An inner linear gap is not a ratio gap. Accept allocation bounds
            # for translation below; CP-SAT searches exactly within the shared
            # remaining budget. A stalled allocation can use the general solver.
            inner_settings = settings.model_copy(update={"max_time_seconds": remaining, "relative_gap": 0.0,
                "use_fast_path": settings.use_fast_path and not force_general})
            inner = solve_linear(priced, inner_settings,
                starting_names={key: choice.rotation.name for key, choice in best.items()} if best else None,
                defer_allocation_gap=True)
            # Do not retain the previous iteration's full set of choices while
            # allocating the next one.
            del priced
            iterations = iteration + 1
            search_seconds += inner.solve_seconds
            build_seconds += inner.model_build_seconds
            preparation_seconds += inner.preparation_seconds
            method = "fractional-" + inner.method
            if not inner.success:
                reason = inner.termination_reason
                if reason in ("infeasible", "model_invalid"):
                    best, best_value = None, None
                break
            selected = _selection(problem, dict(inner.result))
            totals = _ratio(selected) if selected is not None else None
            if totals is None:
                reason = "nonpositive_economy"
                break
            value, economy, nload = totals
            previous_value = best_value
            if best_value is None or value < best_value:
                best, best_value = selected, value

            # For phi = N - parameter*E, phi >= b implies N/E >=
            # parameter + b/E_min when b < 0, or + b/E_max when b >= 0.
            # The linear solver's bound remains valid with approximate solves.
            tolerance = 1e-10 * max(1.0, abs(nload), abs(parameter * economy),
                                    abs(inner.bound or 0.0))
            if inner.bound is not None:
                bound = inner.bound - tolerance
                denominator = problem.minimum_economy if bound < 0 else maximum_economy * (1 + 1e-12)
                lower_bound = max(lower_bound, parameter + bound / denominator, 0.0)
            lower_bound = min(lower_bound, best_value)
            if best_value == 0 or (inner.type == SolutionType.OPTIMAL and
                                  abs(nload - parameter * economy) <= tolerance):
                optimal, reason = True, "optimal"
                lower_bound = best_value
                break
            if settings.relative_gap > 0 and ratio_gap(best_value, lower_bound) <= settings.relative_gap:
                reason = "ratio_gap"
                break
            if inner.termination_reason.startswith("memory_limit"):
                reason = "memory_limit"
                break
            if previous_value is not None and previous_value - best_value <= max(1e-15, abs(previous_value) * 1e-12):
                if inner.method in ("regional-allocation", "checked-regional-relaxation") and not force_general:
                    force_general = True
                else:
                    reason = "time_limit" if search_seconds >= settings.max_time_seconds else "no_progress"
                    break

    success = best is not None
    gap = ratio_gap(best_value, lower_bound) if success else None
    return Solution(
        success=success,
        result=[(key, choice.rotation.name) for key, choice in best.items()] if success else None,
        description=("Optimal regional economy per N-load" if optimal else
                     f"Regional ratio solution; optimality gap {gap * 100:.6f}%") if success else
                     "No feasible selection with positive regional economy found",
        type=SolutionType.OPTIMAL if optimal else SolutionType.FEASIBLE if success else SolutionType.MISSING,
        objective=best_value,
        bound=lower_bound if success else None,
        method=method,
        termination_reason=reason,
        preparation_seconds=preparation_seconds,
        model_build_seconds=build_seconds,
        solve_seconds=search_seconds,
        objective_name="regional_nload_per_economy",
        objective_unit="kg N / DKK",
        iterations=iterations,
        gap_override=gap,
    )
