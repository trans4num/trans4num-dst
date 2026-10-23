import operator
from threading import Event
import unittest
from unittest.mock import Mock, patch

from ortools.sat.python import cp_model

from models.denmark.constraints.accumulated_change import AccumulatedChangeConstraint
from models.denmark.optimize import PreparedSolver
from models.denmark.prepare import Choice, PreparedProblem, is_feasible
from models.denmark.things import Crop, CropRotation, Field, Soil, SpatialIndicator
from optimize.memory import MemoryGuard, resident_memory_mb
from optimize.optimize import optimize_region, solve_model
from shared_datamodel.simulation import OptimizationSettings, SimulationGoalType


class MemoryTests(unittest.TestCase):
    def test_current_rss_includes_native_process_memory(self):
        self.assertGreater(resident_memory_mb(), 0)

    def test_memory_watchdog_stops_without_waiting_for_a_new_incumbent(self):
        stopped = Event()
        solver = Mock()
        solver.StopSearch.side_effect = stopped.set
        with patch("optimize.memory.resident_memory_mb", return_value=20):
            with MemoryGuard(solver, 10) as guard:
                self.assertTrue(stopped.wait(2))
        self.assertTrue(guard.exceeded)
        self.assertFalse(guard.thread.is_alive())

    def test_guard_is_cleaned_up_when_search_raises(self):
        guard = MemoryGuard(Mock(), 8192)
        with self.assertRaisesRegex(ValueError, "invalid"):
            with guard:
                raise ValueError("invalid")
        self.assertFalse(guard.thread.is_alive())

    def test_memory_stop_is_not_reported_as_infeasibility(self):
        model = cp_model.CpModel()
        variable = model.NewBoolVar("")
        with patch("optimize.memory.resident_memory_mb", return_value=20):
            result = optimize_region(model, {("field", "rotation"): variable}, max_memory_mb=10)
        self.assertFalse(result.success)
        self.assertEqual(result.termination_reason, "memory_limit_no_solution")
        self.assertIn("does not prove infeasibility", result.description)

    def test_memory_stop_returns_only_a_constraint_checked_fallback(self):
        model = cp_model.CpModel()
        original = CropRotation("original", [Crop.GRASS])
        alternative = CropRotation("alternative", [Crop.MAIZE])
        field = Field("f-1", original, SpatialIndicator(Soil.SAND, 30, 1, 0, 0, "farm"),
                      [original, alternative])
        constraint = AccumulatedChangeConstraint(model, 1, operator.le, None, 0)
        problem = PreparedProblem({field.field_id: field}, {
            field.field_id: [Choice(original, 10, (0,)), Choice(alternative, 0, (1,))],
        }, [constraint], SimulationGoalType.MIN_NLOAD)
        with patch("optimize.memory.resident_memory_mb", return_value=20):
            result = PreparedSolver(model).solve(problem,
                OptimizationSettings(use_fast_path=False, max_memory_mb=10))
        self.assertTrue(result.success)
        self.assertEqual(result.termination_reason, "memory_limit_fallback")
        self.assertEqual(result.result, [(field.field_id, original.name)])
        self.assertTrue(is_feasible(problem, {field.field_id: problem.choices[field.field_id][0]}))
        self.assertLessEqual(result.bound, result.objective)

    def test_feasible_solver_result_survives_memory_stop(self):
        solver = Mock(memory_limit_reached=True)
        solver.ObjectiveValue.return_value = 10
        solver.BestObjectiveBound.return_value = 0
        solver.BooleanValue.return_value = True
        with patch("optimize.optimize.solve_model", return_value=(solver, cp_model.FEASIBLE)):
            result = optimize_region(None, {("field", "rotation"): None})
        self.assertTrue(result.success)
        self.assertEqual(result.termination_reason, "memory_limit")
        self.assertEqual(result.result, [("field", "rotation")])

    def test_linear_relaxation_is_configurable(self):
        for enabled in (False, True):
            model = cp_model.CpModel()
            variable = model.NewBoolVar("")
            model.Minimize(variable)
            solver, status = solve_model(model, 5, False, workers=1,
                                          use_linear_relaxation=enabled)
            self.assertEqual(status, cp_model.OPTIMAL)
            self.assertEqual(solver.parameters.linearization_level, int(enabled))
            self.assertEqual(solver.ObjectiveValue(), 0)


if __name__ == "__main__":
    unittest.main()
