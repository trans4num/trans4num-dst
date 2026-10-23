import itertools
import math
import operator
import random
import unittest
from unittest.mock import Mock, patch

from ortools.sat.python import cp_model
from shared_datamodel.models import get_models
from shared_datamodel.simulation import OptimizationSettings, SimulationGoalType
from models.denmark.constraints.accumulated_change import AccumulatedChangeConstraint
from models.denmark.constraints.grouped_accumulated_change import GroupedAccumulatedChangeConstraint
from models.denmark.metrics import get_metrics
from models.denmark.optimize import PreparedSolver, solve_region
from models.denmark.prepare import Choice, PreparedProblem, is_feasible, prepare_problem
from models.denmark.things import Crop, CropRotation, Field, Soil, SpatialIndicator
from optimize import Solution, SolutionType
from optimize.fractional import enforce_positive_economy, optimize_fractional


def make_problem(rows, limits=()):
    model = cp_model.CpModel()
    fields, choices = {}, {}
    for i, row in enumerate(rows):
        key = f"f-{i}"
        rotations = [CropRotation(f"choice-{j}", [Crop.GRASS]) for j in range(len(row))]
        fields[key] = Field(key, rotations[0], SpatialIndicator(Soil.SAND, 30, 1, 0, 0, f"farm-{i % 2}"), rotations)
        choices[key] = [Choice(rotation, 0, tuple(coefficients), economy, nload)
                        for rotation, (economy, nload, coefficients) in zip(rotations, row)]
    constraints = [AccumulatedChangeConstraint(model, 1, comparison, None, limit) for comparison, limit in limits]
    problem = PreparedProblem(fields, choices, constraints, SimulationGoalType.MAX_ECON_PER_NLOAD)
    enforce_positive_economy(model, problem)
    return model, problem


def ratio(selection):
    economy = sum(choice.economy for choice in selection.values())
    return sum(choice.nload for choice in selection.values()) / economy if economy > 0 else math.inf


class FractionalTests(unittest.TestCase):
    def test_regional_ratio_differs_from_field_ratio_and_preparation_keeps_tradeoffs(self):
        rows = [[(1000, 100, ())], [(1, .0001, ()), (1000, 1, ())]]
        model, problem = make_problem(rows)
        field_wise = {key: min(choices, key=lambda c: c.nload / c.economy) for key, choices in problem.choices.items()}
        self.assertEqual(field_wise["f-1"].rotation.name, "choice-0")
        result = optimize_fractional(problem, OptimizationSettings(relative_gap=0), PreparedSolver(model).solve)
        self.assertEqual(dict(result.result)["f-1"], "choice-1")
        self.assertAlmostEqual(result.objective, 101 / 2000)
        self.assertLess(result.objective, ratio(field_wise))
        self.assertEqual(result.type, SolutionType.OPTIMAL)
        self.assertGreaterEqual(result.iterations, 2)

        values = {(key, c.rotation.name): (c.economy, c.nload) for key, choices in problem.choices.items() for c in choices}
        def metric(rotation, transition, indicator):
            key = "f-0" if indicator.org_id == "farm-0" else "f-1"
            return values[key, rotation.name][0 if transition.name == "ECONOMY" else 1]
        with patch("models.denmark.prepare.f", side_effect=metric):
            prepared = prepare_problem(problem.fields, [], [], SimulationGoalType.MAX_ECON_PER_NLOAD)
            self.assertEqual(len(prepared.choices["f-1"]), 2)
            # Exercise the production dispatch, not only the fractional helper.
            dispatched = solve_region(problem.fields, get_metrics(problem.fields), get_models(None)[1],
                                      settings=OptimizationSettings(relative_gap=0))
        self.assertAlmostEqual(dispatched.objective, 101 / 2000)

    def test_exact_ratio_and_bounds_against_exhaustive_optima(self):
        randomizer = random.Random(31)
        for constrained in (False, True):
            for _ in range(30):
                rows = [[(randomizer.randint(1, 100), randomizer.randint(0, 60), (j, 2 * j) if constrained else ())
                         for j in range(3)] for _ in range(3)]
                model, problem = make_problem(rows, [(operator.le, 3), (operator.le, 6)] if constrained else ())
                feasible = [selection for options in itertools.product(*problem.choices.values())
                            if is_feasible(problem, selection := dict(zip(problem.fields, options)))]
                optimum = min(ratio(selection) for selection in feasible)
                result = optimize_fractional(problem, OptimizationSettings(relative_gap=0, workers=1, max_time_seconds=5),
                                             PreparedSolver(model).solve)
                self.assertTrue(result.success)
                self.assertAlmostEqual(result.objective, optimum, places=9)
                self.assertLessEqual(result.bound, optimum + 1e-9)
                selected = {key: next(c for c in problem.choices[key] if c.rotation.name == name) for key, name in result.result}
                self.assertTrue(is_feasible(problem, selected))

    def test_fractional_solver_reuses_one_general_constraint_matrix(self):
        model, problem = make_problem([[(1000, 100, (0,))], [(1, .0001, (0,)), (1000, 1, (1,))]], [(operator.le, 1)])
        problem.constraints.append(GroupedAccumulatedChangeConstraint(model, 1, operator.le, None,
            lambda field: field.spatial_indicator.org_id, lambda field: 1))
        problem.choices = {key: [Choice(c.rotation, c.cost, c.coefficients + (c.coefficients[0],), c.economy, c.nload)
                                for c in choices] for key, choices in problem.choices.items()}
        solver = PreparedSolver(model)
        with patch("models.denmark.optimize.build_model", wraps=__import__("models.denmark.model", fromlist=["build_model"]).build_model) as build:
            result = optimize_fractional(problem, OptimizationSettings(relative_gap=0, use_fast_path=False, workers=1), solver.solve)
        self.assertTrue(result.success)
        self.assertGreaterEqual(result.iterations, 2)
        self.assertEqual(build.call_count, 1)
        self.assertAlmostEqual(result.objective, 101 / 2000)

    def test_zero_individual_economy_and_zero_regional_load(self):
        for rows, expected in (([[(0, 2, ())], [(10, 1, ())]], .3),
                               ([[(0, 0, ()), (5, 1, ())]], .2),
                               ([[(10, 0, ())], [(5, 0, ())]], 0)):
            model, problem = make_problem(rows)
            result = optimize_fractional(problem, OptimizationSettings(relative_gap=0), PreparedSolver(model).solve)
            self.assertTrue(result.success)
            self.assertTrue(math.isfinite(result.objective))
            self.assertAlmostEqual(result.objective, expected)
            self.assertEqual(result.type, SolutionType.OPTIMAL)

    def test_positive_regional_domain_allows_negative_individual_economy(self):
        model, problem = make_problem([[(-2, 0, ()), (1, 1, ())], [(1, 1, ())]])
        result = optimize_fractional(problem, OptimizationSettings(relative_gap=0, workers=1), PreparedSolver(model).solve)
        self.assertTrue(result.success)
        self.assertEqual(dict(result.result)["f-0"], "choice-1")
        self.assertAlmostEqual(result.objective, 1)
        model, problem = make_problem([[(-1, 0, ())]])
        self.assertFalse(optimize_fractional(problem, OptimizationSettings(), PreparedSolver(model).solve).success)

    def test_shared_search_budget_and_ratio_gap_use_ratio_units(self):
        model, problem = make_problem([[(1000, 100, ())], [(1, .0001, ()), (1000, 1, ())]])
        budgets = []
        def partial(priced, settings, **kwargs):
            budgets.append(settings.max_time_seconds)
            selected = {"f-0": priced.choices["f-0"][0], "f-1": priced.choices["f-1"][1]}
            value = sum(c.cost for c in selected.values())
            return Solution(True, [(key, c.rotation.name) for key, c in selected.items()], "partial", SolutionType.FEASIBLE,
                            objective=value, bound=value - 5, solve_seconds=min(.6, settings.max_time_seconds))
        result = optimize_fractional(problem, OptimizationSettings(max_time_seconds=1, relative_gap=0), partial)
        self.assertEqual(len(budgets), 2)
        self.assertAlmostEqual(budgets[1], .4)
        self.assertAlmostEqual(result.solve_seconds, 1)
        self.assertEqual(result.termination_reason, "time_limit")
        self.assertEqual(result.type, SolutionType.FEASIBLE)
        quality = result.quality(OptimizationSettings())
        self.assertAlmostEqual(quality.relative_gap, (result.objective - result.bound) / result.objective)
        self.assertEqual(quality.objective_name, "regional_nload_per_economy")
        self.assertEqual(quality.objective_unit, "kg N / DKK")

    def test_iteration_limit_returns_checked_candidate_with_bound(self):
        model, problem = make_problem([[(1000, 100, ())], [(1, .0001, ()), (1000, 1, ())]])
        result = optimize_fractional(problem, OptimizationSettings(relative_gap=0, max_fractional_iterations=1), PreparedSolver(model).solve)
        self.assertTrue(result.success)
        self.assertEqual(result.iterations, 1)
        self.assertEqual(result.termination_reason, "iteration_limit")
        self.assertEqual(result.type, SolutionType.FEASIBLE)
        self.assertLessEqual(result.bound, result.objective)

    def test_memory_stop_does_not_restart_search_in_the_next_iteration(self):
        _, problem = make_problem([[(1000, 100, ())], [(1, .0001, ()), (1000, 1, ())]])
        def limited(priced, settings, **kwargs):
            selected = {key: choices[-1] for key, choices in priced.choices.items()}
            return Solution(True, [(key, c.rotation.name) for key, c in selected.items()],
                "Memory-limited feasible selection", SolutionType.FEASIBLE,
                objective=sum(c.cost for c in selected.values()), bound=-1000,
                termination_reason="memory_limit_fallback")
        solve = Mock(side_effect=limited)
        result = optimize_fractional(problem, OptimizationSettings(relative_gap=0), solve)
        self.assertEqual(solve.call_count, 1)
        self.assertTrue(result.success)
        self.assertEqual(result.termination_reason, "memory_limit")
        self.assertAlmostEqual(result.objective, 101 / 2000)
        self.assertLessEqual(result.bound, result.objective)


if __name__ == "__main__":
    unittest.main()
