import json
from uuid import UUID

import boto3

from src.job_queue import IEngineJobQueue


class EngineJobQueue(IEngineJobQueue):
    def __init__(self, queue_url: str) -> None:
        self.queue_url = queue_url
        self.sqs = boto3.client("sqs", region_name="eu-central-1")

    def enqueue_simulation(self, region_id: UUID, simulation_id: UUID) -> None:
        self.sqs.send_message(
            QueueUrl=self.queue_url,
            MessageBody=json.dumps(
                {
                    "region": str(region_id),
                    "simulation": str(simulation_id),
                }
            ),
        )
