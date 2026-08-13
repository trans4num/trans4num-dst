from abc import ABC, abstractmethod
from uuid import UUID

from geojson_pydantic import FeatureCollection
from geojson_pydantic.geometries import Polygon
from shared_datamodel.schema import BaseSchema
from shared_datamodel.simulation import Simulation


class Region(BaseSchema):
    id: UUID
    name: str
    area: Polygon


class IStore(ABC):
    @abstractmethod
    def list_regions(self) -> list[UUID]:
        pass

    @abstractmethod
    def read_region(self, region: UUID) -> Region:
        pass

    @abstractmethod
    def list_simulations(self, region: UUID) -> list[Simulation]:
        pass

    @abstractmethod
    def create_simulation(self, simulation: Simulation) -> None:
        pass

    @abstractmethod
    def get_fields(self, region: UUID) -> FeatureCollection | None:
        pass

    @abstractmethod
    def get_variables(self, simulation_id: UUID) -> dict | None:
        pass


def Store(store_type: str) -> IStore:
    if store_type == "s3":
        from src.store.s3 import Store as S3Store

        return S3Store()
    elif store_type == "local":
        from src.store.local import Store as LocalStore

        return LocalStore()
    raise Exception("Unknown STORE_TYPE environment variable.")
