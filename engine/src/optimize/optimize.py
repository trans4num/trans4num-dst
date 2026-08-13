from ortools.sat.cp_model_pb2 import CpSolverStatus
from ortools.sat.python import cp_model

# from optimize.initialize import setup_model
from utils import print_runtime

from . import Solution, SolutionType
from .calbacks import SolutionPrinterWithLimit


@print_runtime
def solve_model(
    model: cp_model.CpModel,
    max_time: int,
    debug: bool,
) -> tuple[cp_model.CpSolver, CpSolverStatus]:
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max_time
    solver.parameters.log_search_progress = debug
    solution_printer = SolutionPrinterWithLimit(5)
    status = solver.Solve(model, solution_printer)
    return solver, status


def optimize_region(
    model: cp_model.CpModel,
    x: dict,
    max_time: int = 120,
    debug: bool = False,
) -> Solution:
    solver, status = solve_model(model, max_time, debug)

    if status == cp_model.MODEL_INVALID:
        return Solution(
            success=False,
            result=None,
            description="The model is invalid.",
            type=SolutionType.MISSING,
        )

    if status == cp_model.UNKNOWN:
        return Solution(
            success=False,
            result=None,
            description="No solution found.",
            type=SolutionType.MISSING,
        )

    if status == cp_model.INFEASIBLE:
        return Solution(
            success=False,
            result=None,
            description="No feasible solution exists.",
            type=SolutionType.MISSING,
        )

    slices = []
    for idx, xij in x.items():
        selected = solver.BooleanValue(xij)
        if selected:
            slices.append(idx)

    selected = slices

    if status == cp_model.OPTIMAL:
        return Solution(
            success=True,
            result=selected,
            description="Optimal solution",
            type=SolutionType.OPTIMAL,
        )
    if status == cp_model.FEASIBLE:
        bound = solver.BestObjectiveBound()
        objective = solver.ObjectiveValue()

        pct_deviation = (objective - bound) / bound * 100

        return Solution(
            success=True,
            result=selected,
            description=f"Only found a feasible solution. Solution is guarenteed within {pct_deviation:.2f} % of the optimal solution",
            type=SolutionType.FEASIBLE,
        )

    return Solution(
        success=False,
        result=None,
        description="We do not know why this failed.",
        type=SolutionType.MISSING,
    )
