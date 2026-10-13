import time

from ortools.sat.python import cp_model

from utils import print_runtime
from . import Solution, SolutionType, relative_gap


@print_runtime
def solve_model(model, max_time, debug, gap_limit=0.05, workers=8):
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max_time
    solver.parameters.relative_gap_limit = gap_limit
    solver.parameters.num_search_workers = workers
    solver.parameters.log_search_progress = debug
    # Native gap termination observes bound improvements even when no new
    # incumbent arrives, unlike stopping in a solution callback.
    status = solver.Solve(model)
    return solver, status


def optimize_region(model, x, max_time=120, debug=False, gap_limit=0.05, workers=8):
    start = time.perf_counter()
    solver, status = solve_model(model, max_time, debug, gap_limit, workers)
    seconds = time.perf_counter() - start
    failures = {
        cp_model.MODEL_INVALID: ("The model is invalid.", "model_invalid"),
        cp_model.UNKNOWN: ("The search budget expired before a feasible solution was found; this does not prove infeasibility.", "time_limit_no_solution"),
        cp_model.INFEASIBLE: ("No feasible solution exists.", "infeasible"),
    }
    if status in failures:
        description, reason = failures[status]
        if status == cp_model.MODEL_INVALID:
            detail = model.Validate() or solver.ResponseProto().solution_info
            if detail:
                description += " " + detail
        return Solution(False, None, description, SolutionType.MISSING,
                        termination_reason=reason, solve_seconds=seconds)
    objective, bound = solver.ObjectiveValue(), solver.BestObjectiveBound()
    # CP-SAT can report OPTIMAL after reaching a nonzero relative-gap limit.
    # Do not present that as a proof that the incumbent equals the optimum.
    proven = status == cp_model.OPTIMAL and abs(objective - bound) <= 1e-7
    gap = relative_gap(objective, bound)
    reason = "optimal" if proven else "gap_limit" if gap_limit > 0 and gap <= gap_limit else "time_limit"
    return Solution(
        success=True,
        result=[key for key, variable in x.items() if variable is True or solver.BooleanValue(variable)],
        description="Optimal solution" if proven else f"Feasible solution; normalized optimality gap {gap * 100:.6f}%",
        type=SolutionType.OPTIMAL if proven else SolutionType.FEASIBLE,
        objective=objective,
        bound=bound,
        termination_reason=reason,
        solve_seconds=seconds,
    )
