from uuid import UUID

from geojson_pydantic import FeatureCollection
from src.store import IStore

loaded_data = {}


def get_named_fields(region: UUID, store: IStore) -> FeatureCollection | None:
    if region in loaded_data:
        return loaded_data[region]

    data = store.get_fields(region)

    loaded_data[region] = data
    return loaded_data[region]
