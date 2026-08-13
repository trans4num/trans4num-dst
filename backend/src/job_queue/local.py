import json
import logging
from threading import Thread
from urllib.request import Request, urlopen
from uuid import UUID

from src.job_queue import IEngineJobQueue

logger = logging.getLogger(__name__)


class EngineJobQueue(IEngineJobQueue):
    def __init__(self, invoke_url: str) -> None:
        if not invoke_url:
            raise ValueError("A local engine invoke URL is required")
        self.invoke_url = invoke_url

    def enqueue_simulation(self, region_id: UUID, simulation_id: UUID) -> None:
        event = {
            "Records": [
                {
                    "body": json.dumps(
                        {
                            "region": str(region_id),
                            "simulation": str(simulation_id),
                        }
                    )
                }
            ]
        }
        Thread(
            target=self._invoke_engine,
            args=(event, region_id, simulation_id),
            daemon=True,
        ).start()

    def _invoke_engine(self, event: dict, region_id: UUID, simulation_id: UUID) -> None:
        logger.info(
            "Submitting local simulation %s for region %s to %s",
            simulation_id,
            region_id,
            self.invoke_url,
        )
        request = Request(
            self.invoke_url,
            data=json.dumps(event).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=60 * 60) as response:
                if response.status >= 300 or response.headers.get(
                    "X-Amz-Function-Error"
                ):
                    raise RuntimeError(
                        f"Local engine invocation failed with HTTP {response.status}"
                    )
                logger.info(
                    "Local simulation %s completed engine invocation", simulation_id
                )
        except Exception:
            logger.exception(
                "Local engine invocation failed for simulation %s in region %s",
                simulation_id,
                region_id,
            )
