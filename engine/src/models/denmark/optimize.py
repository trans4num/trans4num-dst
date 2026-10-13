import time
import math

from shared_datamodel.simulation import OptimizationSettings

from models.denmark.model import build_model, prepare_model
from models.denmark.prepare import is_feasible
from optimize import Solution, SolutionType, relative_gap
from optimize.allocation import allocate_region
from optimize.greedy import improve_seed
from optimize.optimize import optimize_region


def _allocation_solution(candidate):
    gap = relative_gap(candidate.objective, candidate.bound)
    return Solution(
        success=True,
        result=[(key, choice.rotation.name) for key, choice in candidate.selection.items()],
        description="Optimal independent allocation" if candidate.optimal else f"Regional allocation within {gap * 100:.6f}% of optimal",
        type=SolutionType.OPTIMAL if candidate.optimal else SolutionType.FEASIBLE,
        objective=candidate.objective,
        bound=candidate.bound,
        method="regional-allocation",
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


def solve_region(fields, original_metrics, job_model, max_time=120, gap_limit=0.05, debug=False,
                 settings=None):
    settings = settings or OptimizationSettings(max_time_seconds=max_time, relative_gap=gap_limit, debug=debug)
    start = time.perf_counter()
    model, problem = prepare_model(fields, original_metrics, job_model)
    preparation_seconds = time.perf_counter() - start

    def finish(result, build_seconds=0):
        result.preparation_seconds = preparation_seconds
        result.model_build_seconds = build_seconds
        print(f"Optimization: {result.method}, {result.termination_reason}, "
              f"prepare={preparation_seconds:.3f}s, build={build_seconds:.3f}s, solve={result.solve_seconds:.3f}s")
        return result

    start = time.perf_counter()
    candidate = allocate_region(problem) if settings.use_fast_path else None
    allocation_seconds = time.perf_counter() - start
    if candidate is not None and relative_gap(candidate.objective, candidate.bound) <= settings.relative_gap:
        result = _allocation_solution(candidate)
        result.solve_seconds = allocation_seconds
        return finish(result)

    # A fresh Lambda invocation has no previous job's selections. Construct
    # checked seeds from the current allocation or current source baseline.
    start = time.perf_counter()
    seeds = []
    if candidate is not None:
        seeds.append(_allocation_solution(candidate))
    independent_bound = math.fsum(min(choice.cost for choice in choices) for choices in problem.choices.values())
    selection = _selection_from_names(problem, {key: entry.rotation.name for key, entry in fields.items()})
    if selection is not None:
        seeds.append(Solution(True, [(key, choice.rotation.name) for key, choice in selection.items()],
            "Feasible source baseline", SolutionType.FEASIBLE,
            objective=math.fsum(choice.cost for choice in selection.values()),
            bound=independent_bound, method="feasible-fallback"))
    seed = min(seeds, key=lambda solution: solution.objective) if seeds else None
    if seed is not None:
        initial = _selection_from_names(problem, dict(seed.result))
        improved = improve_seed(problem, initial)
        if improved is not None:
            value = math.fsum(choice.cost for choice in improved.values())
            if value < seed.objective:
                seed = Solution(True, [(key, choice.rotation.name) for key, choice in improved.items()],
                    "Greedy feasible starting solution", SolutionType.FEASIBLE,
                    objective=value, bound=seed.bound, method="greedy-fallback")
    preparation_seconds += time.perf_counter() - start
    start = time.perf_counter()
    hint = seed.result if seed else None
    model, x = build_model(model, problem, hint)
    build_seconds = time.perf_counter() - start
    result = optimize_region(model, x, max_time=settings.max_time_seconds, debug=settings.debug,
                             gap_limit=settings.relative_gap, workers=settings.workers)
    if seed is not None and result.termination_reason not in ("model_invalid", "infeasible"):
        if not result.success or (result.objective is not None and seed.objective < result.objective):
            seed.solve_seconds = result.solve_seconds + allocation_seconds
            seed.termination_reason = "time_limit_fallback" if not result.success else "best_feasible_fallback"
            if result.bound is not None:
                seed.bound = max(seed.bound, min(result.bound, seed.objective))
            return finish(seed, build_seconds)
        if result.bound is not None:
            result.bound = max(result.bound, min(seed.bound, result.objective))
    result.solve_seconds += allocation_seconds
    return finish(result, build_seconds)
