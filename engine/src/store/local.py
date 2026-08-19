import gzip
import json
from os import listdir, makedirs, path
from uuid import UUID

import pandas as pd
from osgeo import gdal, ogr

from shared_datamodel.simulation import (
    Simulation,
    SimulationBase,
)
from models.denmark.things import Col
from store import IStore, resolve_input_columns


class Store(IStore):
    def region_exists(self, region_id: UUID) -> bool:
        return path.exists(f"simulations/{region_id}")

    def list_simulations(self, region_id: UUID) -> list[UUID]:
        names = listdir(f"simulations/{region_id}")

        uuids = []
        for name in names:
            try:
                uuids.append(UUID(name))
            except ValueError:
                continue

        return uuids

    def simulation_exists(self, region_id: UUID, simulation_id: UUID):
        return path.exists(f"simulations/{region_id}/{simulation_id}")

    def read_meta(self, region_id: UUID, simulation_id: UUID) -> SimulationBase:
        meta_path = f"simulations/{region_id}/{simulation_id}/meta.json"
        with open(meta_path, "r") as f:
            meta = SimulationBase.model_validate_json(f.read())
            return meta

    def read_fields_csv(self, region_id: UUID, cols: list[Col]) -> pd.DataFrame:
        fields_path = "data/Fields2023_DataDST_May2025.csv"
        source_columns = set(pd.read_csv(fields_path, nrows=0).columns)
        input_names = resolve_input_columns(source_columns, cols)
        df = pd.read_csv(
            fields_path,
            dtype={input_names[c.name_in_input]: c.dtype for c in cols},
            usecols=list(input_names.values()),
        )
        return df.rename(columns={v: k for k, v in input_names.items() if v != k})

    def read_fields_shapefile(self, region_id: UUID) -> gdal.Dataset:
        fake_geometry_file = "data/fake-fields.geojson"
        if path.exists(fake_geometry_file) and not path.exists(
            "data/Marker_2023_n61489.zip"
        ):
            return ogr.Open(fake_geometry_file)

        field_geometries_file = (
            "/vsizip/data/Marker_2023_n61489.zip/Marker_2023_n61489.shp"
        )
        driver = ogr.GetDriverByName("ESRI Shapefile")
        dataSource = driver.Open(field_geometries_file, 0)
        return dataSource

    def write_geometries_if_missing(self, region_id: UUID, featurecollection_str: str):
        if not path.exists("simulations"):
            makedirs("simulations")
        if not path.exists(f"simulations/{region_id}"):
            makedirs(f"simulations/{region_id}")

        if path.exists(f"simulations/{region_id}/fields.geojson.gz"):
            return

        with gzip.open(f"simulations/{region_id}/fields.geojson.gz", "w") as f:
            f.write(featurecollection_str.encode("utf-8"))

    def write_debug_geometries(
        self, region_id: UUID, simulation_id: UUID, featurecollection_str: str
    ):
        if not path.exists("simulations"):
            makedirs("simulations")
        if not path.exists(f"simulations/{region_id}"):
            makedirs(f"simulations/{region_id}")
        if not path.exists(f"simulations/{region_id}/{simulation_id}"):
            makedirs(f"simulations/{region_id}/{simulation_id}")
        with gzip.open(
            f"simulations/{region_id}/{simulation_id}/debug.geojson.gz", "w"
        ) as f:
            f.write(featurecollection_str.encode("utf-8"))

    def write_variables(self, region_id: UUID, simulation_id: UUID, json_str: str):
        if not path.exists("simulations"):
            makedirs("simulations")
        if not path.exists(f"simulations/{region_id}"):
            makedirs(f"simulations/{region_id}")
        if not path.exists(f"simulations/{region_id}/{simulation_id}"):
            makedirs(f"simulations/{region_id}/{simulation_id}")
        with open(f"simulations/{region_id}/{simulation_id}/variables.json", "w") as f:
            f.write(json_str)

    def write_meta(self, region_id: UUID, simulation_id: UUID, simulation: Simulation):
        if not path.exists("simulations"):
            makedirs("simulations")
        if not path.exists(f"simulations/{region_id}"):
            makedirs(f"simulations/{region_id}")
        if not path.exists(f"simulations/{region_id}/{simulation_id}"):
            makedirs(f"simulations/{region_id}/{simulation_id}")
        with open(f"simulations/{region_id}/{simulation_id}/meta.json", "w") as f:
            f.write(simulation.model_dump_json(indent=2))

    def update_meta_to_failed(self, region_id: UUID, simulation_id: UUID):
        meta_path = f"simulations/{region_id}/{simulation_id}/meta.json"
        with open(meta_path, "r") as f:
            meta = json.load(f)

        meta["status"] = "failed"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
