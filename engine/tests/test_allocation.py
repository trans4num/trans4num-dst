import itertools
import operator
import random
import unittest
from dataclasses import replace
from ortools.sat.python import cp_model
from unittest.mock import patch

from models.denmark.constraints.accumulated_change import AccumulatedChangeConstraint
from models.denmark.constraints.grouped_accumulated_change import GroupedAccumulatedChangeConstraint
from models.denmark.optimize import solve_region
from models.denmark.prepare import Choice, PreparedProblem, is_feasible
from models.denmark.things import Crop, CropRotation, Field, Soil, SpatialIndicator
from optimize import Solution, SolutionType
from optimize.allocation import allocate_region
from shared_datamodel.models import get_models
from shared_datamodel.simulation import SimulationGoalType
from models.denmark.metrics import get_metrics


def make_problem(rows, comparison=operator.ge, target=0):
    fields, choices = {}, {}
    for i, row in enumerate(rows):
        key = f"f-{i}"
        rotations = [CropRotation(f"choice-{j}", [Crop.GRASS]) for j in range(len(row))]
        fields[key] = Field(key, rotations[0], SpatialIndicator(Soil.SAND, 30, 1, 0, 0, "farm"), rotations)
        choices[key] = [Choice(rotation, cost, (resource,)) for rotation, (resource, cost) in zip(rotations, row)]
    constraint = AccumulatedChangeConstraint(None, 1, comparison, None, target)
    return PreparedProblem(fields, choices, [constraint], SimulationGoalType.MIN_NLOAD)


class AllocationTests(unittest.TestCase):
    def test_bounds_and_feasibility_against_exhaustive_integer_optima(self):
        randomizer = random.Random(17)
        for _ in range(100):
            rows = [[(randomizer.randint(-20, 40), randomizer.uniform(-50, 50)) for _ in range(4)] for _ in range(3)]
            comparison = randomizer.choice([operator.ge, operator.le])
            target = randomizer.randint(-40, 80)
            problem = make_problem(rows, comparison, target)
            feasible_costs = [sum(choice.cost for choice in selection.values())
                             for options in itertools.product(*problem.choices.values())
                             if is_feasible(problem, selection := dict(zip(problem.fields, options)))]
            result = allocate_region(problem)
            if not feasible_costs:
                self.assertIsNone(result)
                continue
            self.assertIsNotNone(result)
            self.assertTrue(is_feasible(problem, result.selection))
            optimum = min(feasible_costs)
            self.assertLessEqual(result.bound, optimum + 1e-7)
            self.assertGreaterEqual(result.objective, optimum - 1e-7)
            if result.optimal:
                self.assertAlmostEqual(result.objective, optimum)

    def test_whole_field_repair_with_large_integer_coefficients(self):
        problem = make_problem([[(0, 0), (10**15, 3)], [(0, 0), (10**15, 4)]], target=10**15 + 1)
        result = allocate_region(problem)
        self.assertTrue(is_feasible(problem, result.selection))
        self.assertEqual(result.objective, 7)
        self.assertLessEqual(result.bound, 3.000001)

    def test_general_constraint_types_and_mixed_goal_opt_out(self):
        problem = make_problem([[(0, 0), (10, 1)]], target=5)
        constraint = problem.constraints[0]
        for constraints in ([constraint, constraint], [GroupedAccumulatedChangeConstraint(
            None, 1, operator.ge, None, lambda field: "farm", lambda field: 1)]):
            problem.constraints = constraints
            self.assertIsNone(allocate_region(problem))
        class FutureConstraint(AccumulatedChangeConstraint):
            pass
        problem.constraints = [FutureConstraint(None, 1, operator.ge, None, 5)]
        self.assertIsNone(allocate_region(problem))
        problem.constraints = [constraint]
        problem.goal_type = SimulationGoalType.MAX_ECON_PER_NLOAD
        self.assertIsNone(allocate_region(problem))

    def test_unchecked_relaxation_routes_to_general_solver(self):
        # Each relaxed problem violates the other resource cap: at most one A
        # and one B can be selected, so the full solution needs an original.
        problem = make_problem([[(0, 10), (1, 0), (0, 1)]] * 3)
        model = cp_model.CpModel()
        problem.constraints = [AccumulatedChangeConstraint(model, 1, operator.le, None, 1),
                               AccumulatedChangeConstraint(model, 1, operator.le, None, 1)]
        problem.choices = {key: [replace(choice, coefficients=(int(j == 1), int(j == 2)))
                                for j, choice in enumerate(choices)] for key, choices in problem.choices.items()}
        job = get_models(None)[0].model_copy(deep=True)
        problem.goal_type = job.goal.type
        expected = Solution(True, [], "general solver", SolutionType.FEASIBLE)
        with patch("models.denmark.optimize.prepare_model", return_value=(model, problem)), patch("models.denmark.optimize.optimize_region", return_value=expected) as solve:
            self.assertIs(solve_region(problem.fields, get_metrics(problem.fields), job), expected)
            solve.assert_called_once()


if __name__ == "__main__":
    unittest.main()
