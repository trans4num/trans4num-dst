import itertools
import json
import operator
import random
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from uuid import uuid4

from shared_datamodel.models import get_models
from shared_datamodel.simulation import OptimizationSettings, SimulationBase, SimulationGoalType
from models.denmark.constraints.accumulated_change import AccumulatedChangeConstraint
from models.denmark.constraints.grouped_accumulated_change import GroupedAccumulatedChangeConstraint
from models.denmark.constraints.scaling import coefficient, limit
from models.denmark.metrics import get_metrics
from models.denmark.model import prepare_model
from models.denmark.optimize import PreparedSolver, solve_region
from models.denmark.prepare import Choice, PreparedProblem, InfeasibleConstraints, is_feasible, propagate_constraints
from models.denmark.rotations import rotations
from optimize import SolutionType
from optimize.greedy import repair_seed
from optimize.allocation import allocate_checked_relaxation
from store.local import write_json_atomic
from test_preparation import sample_fields
import handler


class EngineSanityTests(unittest.TestCase):
    def test_zero_change_baseline_is_feasible_for_all_goals(self):
        fields = sample_fields()
        for template in get_models(None):
            job = template.model_copy(deep=True)
            for constraint in job.constraints:
                if constraint.name in ("Fields Change", "Single Farmer Impact", "Area Change"):
                    constraint.enabled, constraint.value = True, 0
            model, problem = prepare_model(fields, get_metrics(fields), job)
            baseline = {key: next(c for c in choices if c.rotation.name == fields[key].rotation.name)
                        for key, choices in problem.choices.items()}
            self.assertTrue(is_feasible(problem, baseline))
            self.assertTrue(all(len(choices) == 1 for choices in problem.choices.values()))
            result = solve_region(fields, get_metrics(fields), job, settings=OptimizationSettings(relative_gap=0))
            self.assertTrue(result.success)
            self.assertEqual(result.type, SolutionType.OPTIMAL)

    def test_scaling_preserves_opposite_deltas_and_strict_count_limits(self):
        self.assertEqual(coefficient(.05, 1000000), -coefficient(-.05, 1000000))
        self.assertEqual(limit(2.27, 100, operator.le), 227)
        self.assertEqual(limit(-1.2, 1, operator.ge), -1)
        self.assertEqual(limit(10.8, 1, operator.le), 10)

    def test_fixed_fields_do_not_create_boolean_search_variables(self):
        fields = sample_fields()
        metrics = get_metrics(fields)
        job = get_models(None)[0].model_copy(deep=True)
        constraint = next(c for c in job.constraints if c.name == "Fields Change")
        constraint.enabled, constraint.value = True, 0
        model, problem = prepare_model(fields, metrics, job)
        result = PreparedSolver(model).solve(problem, OptimizationSettings(use_fast_path=False, workers=1))
        self.assertTrue(result.success)
        self.assertEqual(result.type, SolutionType.OPTIMAL)
        self.assertAlmostEqual(result.objective, -metrics.total_revenue)
        self.assertLessEqual(len(model.Proto().variables), 1)
        self.assertEqual(len(result.result), len(fields))

    def test_propagation_preserves_every_feasible_assignment(self):
        randomizer = random.Random(70)
        fields = sample_fields()
        for _ in range(60):
            choices = {key: [Choice(r, j, tuple(randomizer.randint(-5, 5) for _ in range(3)))
                             for j, r in enumerate(rotations[:3])] for key in fields}
            caps = {"farm-0": randomizer.randint(-5, 5), "farm-1": randomizer.randint(-5, 5)}
            constraints = [AccumulatedChangeConstraint(None, 1, operator.le, None, randomizer.randint(-6, 8)),
                           AccumulatedChangeConstraint(None, 1, operator.ge, None, randomizer.randint(-6, 8)),
                           GroupedAccumulatedChangeConstraint(None, 1, operator.ge, None,
                               lambda field: field.spatial_indicator.org_id,
                               lambda field: caps[field.spatial_indicator.org_id])]
            original = PreparedProblem(fields, choices, constraints, SimulationGoalType.MIN_NLOAD)
            def feasible(problem):
                return {tuple(c.rotation.name for c in options) for options in itertools.product(*problem.choices.values())
                        if is_feasible(problem, dict(zip(problem.fields, options)))}
            expected = feasible(original)
            reduced = PreparedProblem(fields, {key: row[:] for key, row in choices.items()}, constraints, original.goal_type)
            try:
                propagate_constraints(reduced)
            except InfeasibleConstraints:
                self.assertFalse(expected)
            else:
                self.assertEqual(feasible(reduced), expected)

    def test_repair_reaches_reduction_target_without_exceeding_change_limit(self):
        fields = sample_fields()
        constraints = [AccumulatedChangeConstraint(None, 1, operator.le, None, -2),
                       AccumulatedChangeConstraint(None, 1, operator.le, None, 1)]
        choices = {key: [Choice(field.rotation, 0, (0, 0)), Choice(rotations[-1], 10 + i, (-2, 1))]
                   for i, (key, field) in enumerate(fields.items())}
        problem = PreparedProblem(fields, choices, constraints, SimulationGoalType.MAX_ECONOMY)
        initial = {key: row[0] for key, row in choices.items()}
        self.assertFalse(is_feasible(problem, initial))
        repaired = repair_seed(problem, initial)
        self.assertTrue(is_feasible(problem, repaired))
        self.assertEqual(sum(c.coefficients[1] for c in repaired.values()), 1)

    def test_checked_relaxation_bounds_cover_exhaustive_full_optimum(self):
        randomizer = random.Random(123)
        fields = sample_fields()
        accepted = 0
        for _ in range(80):
            choices = {key: [Choice(r, randomizer.randint(0, 20), tuple(randomizer.randint(0, 3) for _ in range(2)))
                             for r in rotations[:3]] for key in fields}
            constraints = [AccumulatedChangeConstraint(None, 1, operator.le, None, 4),
                           GroupedAccumulatedChangeConstraint(None, 1, operator.le, None,
                               lambda field: field.spatial_indicator.org_id, lambda field: 3)]
            problem = PreparedProblem(fields, choices, constraints, SimulationGoalType.MIN_NLOAD)
            candidate = allocate_checked_relaxation(problem)
            if candidate is None:
                continue
            accepted += 1
            self.assertTrue(is_feasible(problem, candidate.selection))
            optimum = min(sum(choice.cost for choice in options) for options in itertools.product(*choices.values())
                          if is_feasible(problem, dict(zip(fields, options))))
            self.assertLessEqual(candidate.bound, optimum + 1e-8)
            self.assertGreaterEqual(candidate.objective, optimum - 1e-8)
        self.assertGreater(accepted, 0)

    def test_impossible_target_is_reported_without_a_solver_search(self):
        fields = sample_fields()
        job = get_models(None)[0].model_copy(deep=True)
        job.goal.configuration[0].value = -1
        next(c for c in job.constraints if c.name == "Fields Change").enabled = True
        next(c for c in job.constraints if c.name == "Fields Change").value = 0
        with patch("models.denmark.optimize.optimize_region") as solve:
            result = solve_region(fields, get_metrics(fields), job)
        solve.assert_not_called()
        self.assertFalse(result.success)
        self.assertEqual(result.termination_reason, "infeasible")
        self.assertIn("N-Load Change", result.description)

    def test_local_metadata_replacement_never_exposes_partial_json(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root) / "meta.json"
            target.write_text(json.dumps({"state": "processing"}))
            original_dump = json.dump
            observed = []
            def dump(value, file, **kwargs):
                observed.append(json.loads(target.read_text()))
                return original_dump(value, file, **kwargs)
            with patch("store.local.json.dump", side_effect=dump):
                write_json_atomic(str(target), {"state": "success"})
            self.assertEqual(observed, [{"state": "processing"}])
            self.assertEqual(json.loads(target.read_text()), {"state": "success"})


class HandlerTests(unittest.TestCase):
    def test_sqs_batch_processes_all_records_including_status_quo(self):
        region, first, second = uuid4(), uuid4(), uuid4()
        event = {"Records": [{"body": json.dumps(body)} for body in [
            {"region": str(region), "simulation": str(first)},
            {"region": str(region), "create_status_quo": True},
            {"region": str(region), "simulation": str(second)},
        ]]}
        with patch("handler.get_store", return_value=Mock()), patch("handler._run_simulation") as run, patch("handler._run_status_quo") as status_quo:
            handler.handler(event, None)
        self.assertEqual([call.kwargs["simulation_id"] for call in run.call_args_list], [first, second])
        status_quo.assert_called_once()

    def test_failed_record_records_trace_and_error_and_does_not_skip_next(self):
        region, first, second = uuid4(), uuid4(), uuid4()
        store = Mock()
        store.read_meta.side_effect = [ValueError("bad metadata"), SimulationBase(name="second", region_id=region)]
        event = {"Records": [{"body": json.dumps({"region": str(region), "simulation": str(id)})} for id in (first, second)]}
        with patch("handler.get_store", return_value=store), patch("handler.run") as run, self.assertLogs("handler", level="ERROR") as logs:
            handler.handler(event, None)
        run.assert_called_once()
        store.update_meta_to_failed.assert_called_once_with(region_id=region, simulation_id=first, error_message="bad metadata")
        self.assertIn("Traceback", "\n".join(logs.output))

    def test_empty_batch_is_valid(self):
        with patch("handler.get_store", return_value=Mock()), patch("handler.run") as run:
            handler.handler({"Records": []}, None)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
