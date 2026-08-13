import gzip
import json
import os
from io import StringIO
from uuid import UUID

import boto3
import pandas as pd
from osgeo import gdal, ogr

from shared_datamodel.simulation import (
    Simulation,
    SimulationBase,
)
from models.denmark.things import Col
from store import IStore, resolve_input_columns


class Store(IStore):
    def __init__(self) -> None:
        self.bucket_name = os.getenv("TRANS4NUM_STORAGE_BUCKET")
        if not self.bucket_name:
            raise RuntimeError(
                "TRANS4NUM_STORAGE_BUCKET must be set when using the S3 store"
            )
        self.s3 = boto3.client("s3")

    def region_exists(self, region_id: UUID) -> bool:
        key = f"simulations/{region_id}".rstrip("/")
        resp = self.s3.list_objects_v2(
            Bucket=self.bucket_name, Prefix=key, Delimiter="/", MaxKeys=1
        )
        return "CommonPrefixes" in resp

    def list_simulations(self, region_id: UUID) -> list[UUID]:
        key = f"simulations/{region_id}/"
        resp = self.s3.list_objects_v2(
            Bucket=self.bucket_name, Prefix=key, Delimiter="/"
        )
        prefixes = resp["CommonPrefixes"]
        uuids = []
        for prefix in prefixes:
            try:
                name = prefix["Prefix"].split("/")[-2]
                uuids.append(UUID(name))
            except ValueError:
                continue

        return uuids

    def simulation_exists(self, region_id: UUID, simulation_id: UUID):
        key = f"simulations/{region_id}/{simulation_id}".rstrip("/")
        resp = self.s3.list_objects_v2(
            Bucket=self.bucket_name, Prefix=key, Delimiter="/", MaxKeys=1
        )
        return "CommonPrefixes" in resp

    def read_meta(self, region_id: UUID, simulation_id: UUID) -> SimulationBase:
        meta_path = f"simulations/{region_id}/{simulation_id}/meta.json"
        meta_data = self.s3.get_object(Bucket=self.bucket_name, Key=meta_path)
        text = meta_data["Body"].read().decode()
        return SimulationBase.model_validate_json(text)

    def read_fields_csv(self, region_id: UUID, cols: list[Col]) -> pd.DataFrame:
        csv_path = f"data/regions/{region_id}/fields.csv"
        csv_data = self.s3.get_object(Bucket=self.bucket_name, Key=csv_path)
        text = csv_data["Body"].read().decode()
        input_names = resolve_input_columns(
            set(pd.read_csv(StringIO(text), nrows=0).columns), cols
        )
        df = pd.read_csv(
            StringIO(text),
            dtype={input_names[c.name_in_input]: c.dtype for c in cols},
            usecols=list(input_names.values()),
        )
        return df.rename(columns={v: k for k, v in input_names.items() if v != k})

    def read_fields_shapefile(self, region_id: UUID) -> gdal.Dataset:
        # Yes the final path name here is hardcoded, but it works for now
        shapefile_zip_path = f"/vsizip/vsis3/{self.bucket_name}/data/regions/{region_id}/fields.zip/Marker_2023_n61489.shp"

        driver = ogr.GetDriverByName("ESRI Shapefile")
        dataSource = driver.Open(shapefile_zip_path, 0)
        return dataSource

    def write_geometries_if_missing(self, region_id: UUID, featurecollection_str: str):
        key = f"simulations/{region_id}/fields.geojson.gz"
        try:
            self.s3.head_object(Bucket=self.bucket_name, Key=key)
        except:
            # If we can not find the object, we create it.
            json_bytes = featurecollection_str.encode("utf-8")
            gzipped_data = gzip.compress(json_bytes)

            self.s3.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=gzipped_data,
                ContentEncoding="gzip",
                ContentType="application/json",
            )

    def write_debug_geometries(
        self, region_id: UUID, simulation_id: UUID, featurecollection_str: str
    ):
        key = f"simulations/{region_id}/{simulation_id}/debug.geojson.gz"
        json_bytes = json.dumps(featurecollection_str).encode("utf-8")
        gzipped_data = gzip.compress(json_bytes)

        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=gzipped_data,
            ContentEncoding="gzip",
            ContentType="application/json",
        )

    def write_variables(self, region_id: UUID, simulation_id: UUID, json_str: str):
        key = f"simulations/{region_id}/{simulation_id}/variables.json"
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=json_str.encode("utf-8"),
            ContentType="application/json",
        )

    def write_meta(self, region_id: UUID, simulation_id: UUID, simulation: Simulation):
        key = f"simulations/{region_id}/{simulation_id}/meta.json"
        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=simulation.model_dump_json(indent=2),
            ContentType="application/json",
        )

    def update_meta_to_failed(self, region_id: UUID, simulation_id: UUID):
        meta_path = f"simulations/{region_id}/{simulation_id}/meta.json"
        meta_data = self.s3.get_object(Bucket=self.bucket_name, Key=meta_path)
        text = meta_data["Body"].read().decode()
        meta = json.loads(text)
        meta["status"] = "failed"

        self.s3.put_object(
            Bucket=self.bucket_name,
            Key=meta_path,
            Body=json.dumps(meta, indent=2).encode("utf-8"),
            ContentType="application/json",
        )
