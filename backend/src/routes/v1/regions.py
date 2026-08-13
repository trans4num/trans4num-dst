from typing import List
from uuid import UUID

from fastapi import APIRouter
from shared_datamodel.models import get_models
from shared_datamodel.schema import BaseSchema
from shared_datamodel.simulation import Model

from src.store import IStore, Region


class RegionResponse(BaseSchema):
    regions: List[Region]


class ModelsResponse(BaseSchema):
    models: List[Model]


def get_router(store: IStore) -> APIRouter:
    router = APIRouter(prefix="/regions", tags=["regions"])

    @router.get("")
    async def get_regions() -> RegionResponse:
        """Get a list of all available testsite regions."""
        regions = []
        for region_name in store.list_regions():
            regions.append(store.read_region(region_name))

        return RegionResponse(regions=regions)

    @router.get("/{region}/models")
    async def get_region_models(region: UUID) -> ModelsResponse:
        """Get a list of all available testsite regions."""
        return ModelsResponse(models=get_models(region))

    return router
