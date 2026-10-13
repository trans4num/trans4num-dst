import unittest
from threading import Event, Thread
from unittest.mock import patch
from uuid import uuid4

from src.job_queue.local import EngineJobQueue


class LocalQueueTests(unittest.TestCase):
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
