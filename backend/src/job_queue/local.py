import json
import logging
from threading import Lock, Thread
from urllib.request import Request, urlopen
from uuid import UUID

from src.job_queue import IEngineJobQueue
from shared_datamodel.simulation import SimulationStatus

logger = logging.getLogger(__name__)


class EngineJobQueue(IEngineJobQueue):
    def __init__(self, invoke_url: str, store=None) -> None:
        if not invoke_url:
            raise ValueError("A local engine invoke URL is required")
        self.invoke_url = invoke_url
        # One local emulator represents one Lambda execution environment.
        self._invoke_lock = Lock()
        self.store = store

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
            with self._invoke_lock, urlopen(request, timeout=60 * 60) as response:
                if response.status >= 300 or response.headers.get(
                    "X-Amz-Function-Error"
                ):
                    raise RuntimeError(
                        f"Local engine invocation failed with HTTP {response.status}"
                    )
                response.read()
                logger.info(
                    "Local simulation %s completed engine invocation", simulation_id
                )
        except Exception as error:
            logger.exception(
                "Local engine invocation failed for simulation %s in region %s",
                simulation_id,
                region_id,
            )
            if self.store is not None:
                try:
                    simulation = next((s for s in self.store.list_simulations(region_id) if s.id == simulation_id), None)
                    # A transport failure after successful output must not
                    # overwrite a completed result or a more useful engine error.
                    if simulation is not None and simulation.status == SimulationStatus.PROCESSING:
                        self.store.update_simulation(simulation.model_copy(update={
                            "status": SimulationStatus.FAILED,
                            "error_message": f"Local engine invocation failed: {error}",
                        }))
                except Exception:
                    logger.exception("Could not persist local invocation failure for %s", simulation_id)
