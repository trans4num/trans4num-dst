from ortools.sat.python import cp_model


class SolutionPrinterWithLimit(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, limit: int):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__solution_limit = limit

    def on_solution_callback(self) -> None:
        print("Found a solution")
        bound = self.BestObjectiveBound()
        objective = self.ObjectiveValue()
        pct_deviation = (objective - bound) / bound * 100
        print("It was off by", pct_deviation, "%")

        if abs(pct_deviation) < self.__solution_limit:
            print("Stop search")
            self.StopSearch()
