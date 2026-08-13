from uuid import UUID

from src.job_queue import IEngineJobQueue


class EngineJobQueue(IEngineJobQueue):
    def __init__(self) -> None:
        pass

    def enqueue_simulation(self, region_id: UUID, simulation_id: UUID) -> None:
        print(f"Fake Enqueuing simulation {simulation_id} for region {region_id}")
