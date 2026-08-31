import gzip
import json
import os
from uuid import UUID

import boto3
from geojson_pydantic import FeatureCollection
from shared_datamodel.simulation import Simulation

from src.store import IStore, Region


class Store(IStore):
    def __init__(self) -> None:
        self.bucket_name = os.getenv("TRANS4NUM_STORAGE_BUCKET")
        if not self.bucket_name:
            raise RuntimeError(
                "TRANS4NUM_STORAGE_BUCKET must be set when using the S3 store"
            )
        self.s3 = boto3.client("s3")

    def list_regions(self) -> list[UUID]:
        key = "regions/"
        resp = self.s3.list_objects_v2(
            Bucket=self.bucket_name, Prefix=key, Delimiter="/"
        )
        prefixes = resp["CommonPrefixes"]
        uuids = []
        for prefix in prefixes:
            try:
                region_id = prefix["Prefix"].split("/")[-2]
                uuids.append(UUID(region_id))
            except ValueError:
                continue

        return uuids

    def read_region(self, region: UUID) -> Region:
        area_path = f"regions/{region}/area.json"
        area_data = self.s3.get_object(Bucket=self.bucket_name, Key=area_path)
        area_text = area_data["Body"].read().decode()
        area = json.loads(area_text)

        meta_path = f"regions/{region}/meta.json"
        meta_data = self.s3.get_object(Bucket=self.bucket_name, Key=meta_path)
        meta_text = meta_data["Body"].read().decode()
        meta = json.loads(meta_text)
        return Region(id=region, name=meta["name"], area=area)

    def list_simulations(self, region: UUID) -> list[Simulation]:
        key = f"simulations/{region}/"
        resp = self.s3.list_objects_v2(
            Bucket=self.bucket_name, Prefix=key, Delimiter="/"
        )
        simulations = []

        if "CommonPrefixes" not in resp:
            return simulations

        prefixes = resp["CommonPrefixes"]
        for prefix in prefixes:
            simulation_path = f"{prefix['Prefix']}meta.json"
            meta_data = self.s3.get_object(Bucket=self.bucket_name, Key=simulation_path)
            meta_text = meta_data["Body"].read().decode()
            meta = json.loads(meta_text)
            s = Simulation.model_validate(meta)
            simulations.append(s)

        return simulations

    def create_simulation(self, simulation: Simulation) -> None:
        key = f"simulations/{simulation.region_id}/{simulation.id}/meta.json"
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=simulation.model_dump_json(indent=2),
            ContentType="application/json",
        )

    def update_simulation(self, simulation: Simulation) -> None:
        key = f"simulations/{simulation.region_id}/{simulation.id}/meta.json"
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=simulation.model_dump_json(indent=2),
            ContentType="application/json",
        )

    def delete_simulation(self, simulation_id: UUID) -> None:
        keys = []
        paginator = self.s3.get_paginator("list_objects_v2")
        for region in self.list_regions():
            prefix = f"simulations/{region}/{simulation_id}/"
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
                keys.extend(
                    obj["Key"] for obj in page.get("Contents", [])
                )

        for start in range(0, len(keys), 1000):
            self.s3.delete_objects(
                Bucket=self.bucket_name,
                Delete={"Objects": [{"Key": key} for key in keys[start : start + 1000]]},
            )

    def get_fields(self, region: UUID) -> FeatureCollection | None:
        fields_path = f"simulations/{region}/fields.geojson.gz"
        try:
            fields_data = self.s3.get_object(Bucket=self.bucket_name, Key=fields_path)
            with gzip.GzipFile(fileobj=fields_data["Body"]) as f:
                text = f.read().decode("utf-8")
                data = json.loads(text)
                return FeatureCollection.model_validate(data)
        except self.s3.exceptions.NoSuchKey:
            return None

    def get_variables(self, simulation_id: UUID) -> dict | None:
        # TODO: This is very inefficient, we should store a mapping from simulation_id to region
        for region in self.list_regions():
            file_path = f"simulations/{region}/{simulation_id}/variables.json"
            try:
                self.s3.head_object(Bucket=self.bucket_name, Key=file_path)
                variables_data = self.s3.get_object(
                    Bucket=self.bucket_name, Key=file_path
                )
                variables_text = variables_data["Body"].read().decode()
                return json.loads(variables_text)
            except self.s3.exceptions.ClientError:
                continue
