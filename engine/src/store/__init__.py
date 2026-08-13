from abc import ABC, abstractmethod
from os import environ
from uuid import UUID

import pandas as pd
from models.denmark.things import Col
from osgeo import gdal
from shared_datamodel.simulation import (
    Simulation,
    SimulationBase,
)


def resolve_input_columns(
    source_columns: set[str], cols: list[Col]
) -> dict[str, str]:
    aliases = {
        "retention": "RedTot",
        "IMK_areal": "area",
    }
    return {
        col.name_in_input: (
            col.name_in_input
            if col.name_in_input in source_columns
            else aliases.get(col.name_in_input, col.name_in_input)
        )
        for col in cols
    }


class IStore(ABC):
    @abstractmethod
    def region_exists(self, region_id: UUID) -> bool:
        pass

    @abstractmethod
    def list_simulations(self, region_id: UUID) -> list[UUID]:
        pass

    @abstractmethod
    def simulation_exists(self, region_id: UUID, simulation_id: UUID) -> bool:
        pass

    @abstractmethod
    def read_meta(self, region_id: UUID, simulation_id: UUID) -> SimulationBase:
        pass

    @abstractmethod
    def read_fields_csv(self, region_id: UUID, cols: list[Col]) -> pd.DataFrame:
        pass

    @abstractmethod
    def read_fields_shapefile(self, region_id: UUID) -> gdal.Dataset:
        pass

    @abstractmethod
    def write_geometries_if_missing(self, region_id: UUID, featurecollection_str: str):
        pass

    @abstractmethod
    def write_debug_geometries(
        self, region_id: UUID, simulation_id: UUID, featurecollection_str: str
    ):
        pass

    @abstractmethod
    def write_variables(self, region_id: UUID, simulation_id: UUID, json_str: str):
        pass

    @abstractmethod
    def write_meta(self, region_id: UUID, simulation_id: UUID, simulation: Simulation):
        pass

    @abstractmethod
    def update_meta_to_failed(self, region_id: UUID, simulation_id: UUID):
        pass


_store: IStore | None = None


def get_store(store_type: str) -> IStore:
    global _store
    if _store is not None:
        return _store
    if store_type == "s3":
        from store.s3 import Store as S3Store

        _store = S3Store()
        return _store
    elif store_type == "local":
        from store.local import Store as LocalStore

        _store = LocalStore()
        return _store
    else:
        raise Exception("Unknown STORE_TYPE environment variable.")
