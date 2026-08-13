from abc import ABC, abstractmethod
from uuid import UUID


class IEngineJobQueue(ABC):
    @abstractmethod
    def enqueue_simulation(self, region_id: UUID, simulation_id: UUID) -> None:
        pass


def JobQueue(
    engine_job_queue_type: str | None,
    engine_job_queue_url: str | None,
) -> IEngineJobQueue:
    if engine_job_queue_type is None:
        engine_job_queue_type = "sqs" if engine_job_queue_url else "fake"

    if engine_job_queue_type == "fake":
        from src.job_queue.fake import EngineJobQueue as FakeJobQueue

        return FakeJobQueue()

    if engine_job_queue_type == "local":
        if not engine_job_queue_url:
            raise ValueError("A local engine invoke URL is required")
        from src.job_queue.local import EngineJobQueue as LocalJobQueue

        return LocalJobQueue(engine_job_queue_url)

    if engine_job_queue_type == "sqs":
        if not engine_job_queue_url:
            raise ValueError("An SQS queue URL is required")
        from src.job_queue.sqs import EngineJobQueue as SQSJobQueue

        return SQSJobQueue(engine_job_queue_url)

    raise ValueError(f"Unknown engine job queue type: {engine_job_queue_type}")
