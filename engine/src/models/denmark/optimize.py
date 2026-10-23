import time
import math

from shared_datamodel.simulation import OptimizationSettings, SimulationGoalType

from models.denmark.model import build_model, prepare_model, set_hint, set_objective
from models.denmark.prepare import is_feasible, InfeasibleConstraints
from optimize import Solution, SolutionType, relative_gap
from optimize.allocation import allocate_checked_relaxation
from optimize.greedy import improve_seed, repair_seed
from optimize.optimize import optimize_region
from optimize.fractional import optimize_fractional


def _allocation_solution(candidate):
    gap = relative_gap(candidate.objective, candidate.bound)
    return Solution(
        success=True,
        result=[(key, choice.rotation.name) for key, choice in candidate.selection.items()],
        description="Optimal independent allocation" if candidate.optimal else f"Regional allocation within {gap * 100:.6f}% of optimal",
        type=SolutionType.OPTIMAL if candidate.optimal else SolutionType.FEASIBLE,
        objective=candidate.objective,
        bound=candidate.bound,
        method=candidate.method,
        termination_reason="optimal" if candidate.optimal else "allocation_gap",
    )


def _selection_from_names(problem, names):
    if set(names) != set(problem.fields):
        return None
    selection = {}
    for key, choices in problem.choices.items():
        choice = next((choice for choice in choices if choice.rotation.name == names[key]), None)
        if choice is None:
            return None
        selection[key] = choice
    return selection if is_feasible(problem, selection) else None


class PreparedSolver:
    """Solve additive objectives on one prepared constraint/variable matrix."""

    def __init__(self, model):
        self.model = model
        self.x = None

    def solve(self, problem, settings, starting_names=None, defer_allocation_gap=False):
        start = time.perf_counter()
        candidate = allocate_checked_relaxation(problem) if settings.use_fast_path else None
        allocation_seconds = time.perf_counter() - start
        if candidate is not None and (defer_allocation_gap or
                relative_gap(candidate.objective, candidate.bound) <= settings.relative_gap):
            result = _allocation_solution(candidate)
            result.solve_seconds = allocation_seconds
            return result

        # Each job constructs its own feasible seeds. Fractional iterations can
        # also reuse a checked selection from the preceding step of THIS job.
        start = time.perf_counter()
        seeds = [_allocation_solution(candidate)] if candidate is not None else []
        independent_bound = math.fsum(min(choice.cost for choice in choices) for choices in problem.choices.values())
        names_to_try = [{key: entry.rotation.name for key, entry in problem.fields.items()}]
        if starting_names is not None:
            names_to_try.append(starting_names)
        for names in names_to_try:
            selection = _selection_from_names(problem, names)
            if selection is not None:
                seeds.append(Solution(True, [(key, choice.rotation.name) for key, choice in selection.items()],
                    "Feasible starting selection", SolutionType.FEASIBLE,
                    objective=math.fsum(choice.cost for choice in selection.values()),
                    bound=independent_bound, method="feasible-fallback"))
        if not seeds:
            initial = {key: next((choice for choice in choices if choice.rotation.name == problem.fields[key].rotation.name),
                                min(choices, key=lambda choice: choice.cost))
                       for key, choices in problem.choices.items()}
            repaired = repair_seed(problem, initial)
            if repaired is not None:
                seeds.append(Solution(True, [(key, choice.rotation.name) for key, choice in repaired.items()],
                    "Repaired feasible starting selection", SolutionType.FEASIBLE,
                    objective=math.fsum(choice.cost for choice in repaired.values()),
                    bound=independent_bound, method="repaired-fallback"))
        seed = min(seeds, key=lambda solution: solution.objective) if seeds else None
        if seed is not None:
            improved = improve_seed(problem, _selection_from_names(problem, dict(seed.result)))
            if improved is not None:
                value = math.fsum(choice.cost for choice in improved.values())
                if value < seed.objective:
                    seed = Solution(True, [(key, choice.rotation.name) for key, choice in improved.items()],
                        "Greedy feasible starting solution", SolutionType.FEASIBLE,
                        objective=value, bound=seed.bound, method="greedy-fallback")
        preparation_seconds = time.perf_counter() - start
        start = time.perf_counter()
        hint = seed.result if seed else None
        if self.x is None:
            self.model, self.x = build_model(self.model, problem, hint)
        else:
            set_objective(self.model, problem, self.x)
            set_hint(self.model, self.x, hint)
        build_seconds = time.perf_counter() - start
        result = optimize_region(self.model, self.x, max_time=settings.max_time_seconds, debug=settings.debug,
                                 gap_limit=settings.relative_gap, workers=settings.workers,
                                 max_memory_mb=settings.max_memory_mb,
                                 use_linear_relaxation=settings.use_linear_relaxation)
        if seed is not None and result.termination_reason not in ("model_invalid", "infeasible"):
            if not result.success or (result.objective is not None and seed.objective < result.objective):
                seed.solve_seconds = result.solve_seconds
                seed.termination_reason = ("memory_limit_fallback" if result.termination_reason.startswith("memory_limit")
                                           else "time_limit_fallback" if not result.success else "best_feasible_fallback")
                if result.bound is not None:
                    seed.bound = max(seed.bound, min(result.bound, seed.objective))
                result = seed
            elif result.bound is not None:
                result.bound = max(result.bound, min(seed.bound, result.objective))
        result.solve_seconds += allocation_seconds
        result.preparation_seconds = preparation_seconds
        result.model_build_seconds = build_seconds
        return result


def solve_region(fields, original_metrics, job_model, max_time=720, gap_limit=0.05, debug=False,
                 settings=None):
    settings = settings or OptimizationSettings(max_time_seconds=max_time, relative_gap=gap_limit, debug=debug)
    start = time.perf_counter()
    try:
        model, problem = prepare_model(fields, original_metrics, job_model)
    except InfeasibleConstraints as error:
        return Solution(False, None, str(error), SolutionType.MISSING,
                        method="constraint-check", termination_reason="infeasible",
                        preparation_seconds=time.perf_counter() - start, iterations=0)
    preparation_seconds = time.perf_counter() - start
    solver = PreparedSolver(model)
    result = optimize_fractional(problem, settings, solver.solve) if (
        problem.goal_type == SimulationGoalType.MAX_ECON_PER_NLOAD
    ) else solver.solve(problem, settings)
    result.preparation_seconds += preparation_seconds
    print(f"Optimization: {result.method}, {result.termination_reason}, "
          f"prepare={result.preparation_seconds:.3f}s, build={result.model_build_seconds:.3f}s, solve={result.solve_seconds:.3f}s")
    return result
