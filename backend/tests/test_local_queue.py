import unittest
from threading import Event, Thread
from unittest.mock import Mock, patch
from uuid import uuid4

from src.job_queue.local import EngineJobQueue
from datetime import datetime, timezone
from shared_datamodel.simulation import Simulation, SimulationStatus


class LocalQueueTests(unittest.TestCase):
    def test_transport_failure_marks_pending_job_failed_but_preserves_completed_results(self):
        region, simulation_id = uuid4(), uuid4()
        for status in (SimulationStatus.PROCESSING, SimulationStatus.SUCCESS):
            store = Mock()
            store.list_simulations.return_value = [Simulation(
                id=simulation_id, region_id=region, name="test", status=status,
                created=datetime.now(timezone.utc), summary=[], charts=[],
            )]
            queue = EngineJobQueue("http://localhost:8080/invoke", store=store)
            with patch("src.job_queue.local.urlopen", side_effect=OSError("connection lost")), self.assertLogs("src.job_queue.local", level="ERROR"):
                queue._invoke_engine({"Records": []}, region, simulation_id)
            if status == SimulationStatus.PROCESSING:
                updated = store.update_simulation.call_args.args[0]
                self.assertEqual(updated.status, SimulationStatus.FAILED)
                self.assertIn("connection lost", updated.error_message)
            else:
                store.update_simulation.assert_not_called()

    def test_next_invocation_waits_for_previous_response_body(self):
        first_read, release_first, second_entered = Event(), Event(), Event()
        calls = []

        class Response:
            status = 200
            headers = {}

            def __init__(self, first):
                self.first = first

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def read(self):
                if self.first:
                    first_read.set()
                    release_first.wait(5)
                return b"null"

        def invoke(request, timeout):
            calls.append(request)
            if len(calls) == 2:
                second_entered.set()
            return Response(len(calls) == 1)

        queue = EngineJobQueue("http://localhost:8080/invoke")
        args = ({"Records": []}, uuid4(), uuid4())
        threads = [Thread(target=queue._invoke_engine, args=args) for _ in range(2)]
        with patch("src.job_queue.local.urlopen", side_effect=invoke):
            try:
                threads[0].start()
                self.assertTrue(first_read.wait(2))
                threads[1].start()
                self.assertFalse(second_entered.wait(.1))
            finally:
                release_first.set()
                for thread in threads:
                    if thread.ident is not None:
                        thread.join(2)
            self.assertTrue(second_entered.is_set())
            self.assertEqual(len(calls), 2)
            self.assertTrue(all(not thread.is_alive() for thread in threads))


if __name__ == "__main__":
    unittest.main()
