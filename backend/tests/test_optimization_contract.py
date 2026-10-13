import unittest
from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from shared_datamodel.models import get_models
from shared_datamodel.simulation import OptimizationResult, Simulation
from src.routes.v1.simulations import get_router


class OptimizationContractTests(unittest.TestCase):
    def setUp(self):
        self.store, self.queue = Mock(), Mock()
        app = FastAPI()
        app.include_router(get_router(self.store, self.queue))
        self.client = TestClient(app)
        self.region = uuid4()

    def test_request_settings_are_saved_and_invalid_budgets_rejected(self):
        request = {"name": "Preview", "regionId": str(self.region),
                   "model": get_models(self.region)[0].model_dump(mode="json"),
                   "optimizationSettings": {"maxTimeSeconds": 15, "relativeGap": .01, "useFastPath": False,
                                            "maxFractionalIterations": 5}}
        response = self.client.post("/simulations", json=request)
        self.assertEqual(response.status_code, 200)
        saved = self.store.create_simulation.call_args.args[0]
        self.assertEqual(saved.optimization_settings.max_time_seconds, 15)
        self.assertEqual(saved.optimization_settings.relative_gap, .01)
        self.assertFalse(saved.optimization_settings.use_fast_path)
        self.assertEqual(saved.optimization_settings.max_fractional_iterations, 5)
        request["optimizationSettings"]["maxTimeSeconds"] = 0
        self.assertEqual(self.client.post("/simulations", json=request).status_code, 422)
        self.assertEqual(self.queue.enqueue_simulation.call_count, 1)

    def test_quality_round_trips_with_camel_case_and_legacy_results(self):
        legacy = {"id": str(uuid4()), "name": "Status Quo", "regionId": str(self.region),
                  "created": datetime.now(timezone.utc).isoformat(), "status": "success",
                  "summary": {"economy": 100}, "charts": []}
        status_quo = Simulation.model_validate(legacy)
        quality = OptimizationResult(method="fractional-cp-sat", status="feasible", termination_reason="time_limit",
                                     objective=.001, best_bound=.00098, relative_gap=.02,
                                     max_time_seconds=15, requested_relative_gap=.01, workers=8,
                                     objective_name="regional_nload_per_economy", objective_unit="kg N / DKK", iterations=3)
        alternative = status_quo.model_copy(update={"id": uuid4(), "name": "Preview", "optimization": quality})
        self.store.list_simulations.return_value = [status_quo, alternative]
        response = self.client.get(f"/simulations?region={self.region}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsNone(data["statusQuo"]["optimization"])
        self.assertEqual(data["simulations"][0]["optimization"]["bestBound"], .00098)
        self.assertEqual(data["simulations"][0]["optimization"]["terminationReason"], "time_limit")
        self.assertEqual(data["simulations"][0]["optimization"]["objectiveName"], "regional_nload_per_economy")
        self.assertEqual(data["simulations"][0]["optimization"]["iterations"], 3)


if __name__ == "__main__":
    unittest.main()
