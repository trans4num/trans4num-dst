import itertools
import json
import operator
import os
import random
import tempfile
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4
import pandas as pd

from models.denmark.constraints.accumulated_change import AccumulatedChangeConstraint
from models.denmark.constraints.grouped_accumulated_change import GroupedAccumulatedChangeConstraint
from models.denmark.load import load_fields
from models.denmark.prepare import is_feasible, prepare_problem
from models.denmark.rotations import rotations
from models.denmark.things import Crop, CropRotation, Field, Soil, SpatialIndicator
from models.denmark.transitions import Transition, f, get_transition, rotation_coefficients
from shared_datamodel.simulation import SimulationBase, SimulationGoalType
from store.local import Store


def sample_fields():
    return {f"f-{i}": Field(f"f-{i}", CropRotation("original", rotation.indices),
                           SpatialIndicator(soil, 30 + i * 10, 1.1 + i, 0, 0, f"farm-{i % 2}"), rotations)
            for i, (soil, rotation) in enumerate(zip([Soil.SAND, Soil.CLAY, Soil.SAND], rotations))}


class PreparationTests(unittest.TestCase):
    def test_cached_coefficients_preserve_original_arithmetic(self):
        randomizer = random.Random(42)
        for _ in range(100):
            rotation = randomizer.choice(rotations)
            indicator = SpatialIndicator(randomizer.choice(list(Soil)), randomizer.uniform(-5, 105),
                                         randomizer.uniform(.001, 50), 0, 0, "farm")
            for transition in Transition:
                expected = sum(get_transition(rotation.indices[i - 1], crop, indicator.soil,
                                              indicator.retention, indicator.area, transition)
                               for i, crop in enumerate(rotation.indices)) / len(rotation.indices)
                self.assertEqual(f(rotation, transition, indicator), expected)

    def test_pruning_preserves_optimum_with_regional_and_farmer_limits(self):
        fields = sample_fields()
        for goal in (SimulationGoalType.MAX_ECONOMY, SimulationGoalType.MIN_NLOAD, SimulationGoalType.MAX_ECON_PER_NLOAD):
            for farmer_limit in (False, True):
                constraints = [AccumulatedChangeConstraint(None, 100, operator.le,
                    lambda choice, entry: 0 if choice.name == entry.rotation.name else entry.spatial_indicator.area,
                    max_change=4)]
                if farmer_limit:
                    constraints.append(GroupedAccumulatedChangeConstraint(None, 10, operator.ge,
                        lambda choice, entry: f(choice, Transition.ECONOMY, entry.spatial_indicator),
                        lambda entry: entry.spatial_indicator.org_id, lambda entry: 10000))
                full = prepare_problem(fields, constraints, [], goal, prune=False)
                reduced = prepare_problem(fields, constraints, [], goal)
                def optimum(problem):
                    values = []
                    for choices in itertools.product(*problem.choices.values()):
                        selection = dict(zip(problem.fields, choices))
                        if is_feasible(problem, selection):
                            values.append(sum(choice.nload for choice in choices) / sum(choice.economy for choice in choices)
                                          if goal == SimulationGoalType.MAX_ECON_PER_NLOAD else sum(choice.cost for choice in choices))
                    return min(values) if values else None
                self.assertEqual(optimum(full), optimum(reduced))

    def test_custom_constraint_does_not_enable_pruning(self):
        class CustomConstraint(AccumulatedChangeConstraint):
            pass
        constraint = CustomConstraint(None, 1, operator.le, lambda choice, entry: 0, 1)
        fields = sample_fields()
        problem = prepare_problem(fields, [constraint], [], SimulationGoalType.MAX_ECONOMY)
        self.assertTrue(all(len(choices) == 13 for choices in problem.choices.values()))

    def test_source_fields_are_read_again_for_each_job(self):
        store = Mock()
        row = {"CVR": 1, "IMK_ID": 1, "Soil_ID": 10, "retention": 30,
               "IMK_areal": 1, "BiogasNetM": 0, "PctHnvOve5": 0,
               **{f"AgCropNr{year}": 10 for year in range(17, 24)}}
        store.read_fields_csv.side_effect = [pd.DataFrame([row]), pd.DataFrame([{**row, "IMK_ID": 2}])]
        region = uuid4()
        self.assertEqual(set(load_fields(store, region)), {"f-1"})
        self.assertEqual(set(load_fields(store, region)), {"f-2"})
        self.assertEqual(store.read_fields_csv.call_count, 2)

    def test_coefficients_are_reused_within_job_and_cleared_at_next_job(self):
        from main import run
        rotation_coefficients.cache_clear()
        sentinel = CropRotation("sentinel", [Crop.GRASS])
        indicator = SpatialIndicator(Soil.SAND, 30, 1, 0, 0, "farm")
        f(sentinel, Transition.LEACHING, indicator)
        f(sentinel, Transition.LEACHING, indicator)
        self.assertEqual(rotation_coefficients.cache_info().hits, 1)
        store = Mock()
        store.region_exists.return_value = False
        with patch("main.load_fields", return_value=sample_fields()), patch("main.create_output"):
            run(store, SimulationBase(name="Status Quo", region_id=uuid4()))
        misses = rotation_coefficients.cache_info().misses
        f(sentinel, Transition.LEACHING, indicator)
        self.assertEqual(rotation_coefficients.cache_info().misses, misses + 1)

    def test_geometry_cache_invalidates_for_new_source_or_field_set(self):
        previous = os.getcwd()
        with tempfile.TemporaryDirectory() as root:
            try:
                os.chdir(root)
                os.mkdir("data")
                with open("data/fake-fields.geojson", "w") as file:
                    file.write("source")
                store = Store()
                region = uuid4()
                geometry = {"type": "FeatureCollection", "features": []}
                store.cache_geometries(region, {"f-1"}, json.dumps(geometry))
                self.assertEqual(store.read_cached_geometries(region, {"f-1"}), geometry)
                self.assertIsNone(store.read_cached_geometries(region, {"f-2"}))
                with open("data/fake-fields.geojson", "a") as file:
                    file.write("changed")
                self.assertIsNone(store.read_cached_geometries(region, {"f-1"}))
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    unittest.main()
