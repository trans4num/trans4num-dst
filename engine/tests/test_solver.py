import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from ortools.sat.python import cp_model
from pydantic import ValidationError
from shared_datamodel.models import get_models
from shared_datamodel.simulation import OptimizationSettings, SimulationBase
from models.denmark.metrics import get_metrics
from models.denmark.optimize import solve_region
from models.denmark.rotations import rotations
from models.denmark.things import CropRotation, Field, Soil, SpatialIndicator
from optimize import Solution, SolutionType, relative_gap
from optimize.optimize import optimize_region
from optimize.settings import settings_for_job
from optimize.greedy import improve_seed
from models.denmark.prepare import Choice, PreparedProblem, is_feasible
from models.denmark.constraints.accumulated_change import AccumulatedChangeConstraint
from models.denmark.constraints.grouped_accumulated_change import GroupedAccumulatedChangeConstraint
from shared_datamodel.simulation import SimulationGoalType
import operator


class SolverTests(unittest.TestCase):
    def test_gap_is_defined_for_negative_and_zero_objectives(self):
        self.assertEqual(relative_gap(-100, -110), .1)
        self.assertEqual(relative_gap(0, 0), 0)
        self.assertEqual(relative_gap(0, -2), 2)

    def test_native_gap_status_is_not_mislabeled_as_proven_optimal(self):
        solver = Mock()
        solver.ObjectiveValue.return_value = -100
        solver.BestObjectiveBound.return_value = -102
        solver.BooleanValue.return_value = True
        with patch("optimize.optimize.solve_model", return_value=(solver, cp_model.OPTIMAL)):
            result = optimize_region(None, {("f-1", "choice"): None}, gap_limit=.05)
        self.assertEqual(result.type, SolutionType.FEASIBLE)
        self.assertEqual(result.termination_reason, "gap_limit")
        self.assertEqual(result.quality(OptimizationSettings()).relative_gap, .02)

    def test_environment_and_request_settings_are_validated(self):
        with patch.dict("os.environ", {"TRANS4NUM_OPTIMIZER_MAX_TIME_SECONDS": "15",
                                      "TRANS4NUM_OPTIMIZER_RELATIVE_GAP": "0.01",
                                      "TRANS4NUM_OPTIMIZER_FAST_PATH": "false"}):
            config = settings_for_job()
            self.assertEqual(config.max_time_seconds, 15)
            self.assertEqual(config.relative_gap, .01)
            self.assertFalse(config.use_fast_path)
            override = OptimizationSettings(max_time_seconds=60)
            self.assertIs(settings_for_job(override), override)
        for data in ({"maxTimeSeconds": 0}, {"relativeGap": -1}, {"workers": -1}, {"maxTimeSeconds": float("inf")},
                     {"maxFractionalIterations": 0}):
            with self.assertRaises(ValidationError):
                OptimizationSettings.model_validate(data)
        job = SimulationBase.model_validate({"name": "request", "regionId": str(uuid4()),
                                             "optimizationSettings": {"maxTimeSeconds": 15}})
        self.assertEqual(job.optimization_settings.max_time_seconds, 15)

    def test_cold_baseline_seed_survives_timeout_and_respects_change_constraint(self):
        region = uuid4()
        original = CropRotation("original", rotations[0].indices)
        entry = Field("f-1", original, SpatialIndicator(Soil.SAND, 30, 1, 0, 0, "farm"), rotations)
        fields = {entry.field_id: entry}
        job = get_models(region)[0].model_copy(deep=True)
        next(c for c in job.constraints if c.name == "Fields Change").enabled = True
        next(c for c in job.constraints if c.name == "Fields Change").value = 0
        missing = Solution(False, None, "timeout", SolutionType.MISSING, termination_reason="no_solution")
        with patch("models.denmark.optimize.optimize_region", return_value=missing) as solver:
            result = solve_region(fields, get_metrics(fields), job)
        self.assertTrue(result.success)
        self.assertEqual(result.result, [("f-1", "original")])
        self.assertEqual(result.termination_reason, "time_limit_fallback")
        model, variables = solver.call_args.args[:2]
        hints = dict(zip(model.Proto().solution_hint.vars, model.Proto().solution_hint.values))
        self.assertEqual(hints[variables["f-1", "original"].Index()], 1)
        for key, variable in variables.items():
            if key != ("f-1", "original"):
                self.assertEqual(hints[variable.Index()], 0)

    def test_general_solver_honors_exact_request_and_fast_path_opt_out(self):
        region = uuid4()
        entry = Field("f-1", CropRotation("original", rotations[0].indices),
                      SpatialIndicator(Soil.SAND, 30, 1, 0, 0, "farm"), rotations)
        fields = {entry.field_id: entry}
        settings = OptimizationSettings(use_fast_path=False, relative_gap=0, workers=1, max_time_seconds=5)
        with patch("models.denmark.optimize.allocate_region") as allocation:
            result = solve_region(fields, get_metrics(fields), get_models(region)[0], settings=settings)
            allocation.assert_not_called()
        self.assertTrue(result.success)
        self.assertEqual(result.method, "cp-sat")
        self.assertEqual(result.type, SolutionType.OPTIMAL)
        self.assertEqual(result.objective, result.bound)

    def test_greedy_seed_improves_cost_without_breaking_regional_or_farmer_caps(self):
        original = CropRotation("original", rotations[0].indices)
        changed = rotations[1]
        fields = {f"f-{i}": Field(f"f-{i}", original, SpatialIndicator(Soil.SAND, 30, 1, 0, 0, "farm"), rotations)
                  for i in range(3)}
        constraints = [AccumulatedChangeConstraint(None, 1, operator.le, None, 2),
                       GroupedAccumulatedChangeConstraint(None, 1, operator.le, None,
                           lambda field: field.spatial_indicator.org_id, lambda field: 1)]
        choices = {key: [Choice(original, 10, (0, 0)), Choice(changed, i, (1, 1))]
                   for i, key in enumerate(fields)}
        problem = PreparedProblem(fields, choices, constraints, SimulationGoalType.MIN_NLOAD)
        initial = {key: row[0] for key, row in choices.items()}
        improved = improve_seed(problem, initial)
        self.assertTrue(is_feasible(problem, improved))
        self.assertEqual(sum(choice.cost for choice in improved.values()), 20)
        self.assertEqual(sum(choice.rotation.name != "original" for choice in improved.values()), 1)


if __name__ == "__main__":
    unittest.main()
