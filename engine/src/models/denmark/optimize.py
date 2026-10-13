import time

from models.denmark.model import build_model, prepare_model
from optimize import Solution, SolutionType, relative_gap
from optimize.allocation import allocate_region
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
    )


def solve_region(fields, original_metrics, job_model, max_time=120, gap_limit=0.05, debug=False):
    start = time.perf_counter()
    model, problem = prepare_model(fields, original_metrics, job_model)
    candidate = allocate_region(problem)
    if candidate is not None and relative_gap(candidate.objective, candidate.bound) <= gap_limit:
        print(f"Regional fast path: {time.perf_counter() - start:.3f} seconds")
        return _allocation_solution(candidate)
    hint = [(key, choice.rotation.name) for key, choice in candidate.selection.items()] if candidate else None
    model, x = build_model(model, problem, hint)
    result = optimize_region(model, x, max_time=max_time, debug=debug)
    if candidate is not None and (not result.success or (
        result.objective is not None and candidate.objective < result.objective
    )):
        return _allocation_solution(candidate)
    return result
