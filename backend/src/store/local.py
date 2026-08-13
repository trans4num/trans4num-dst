import gzip
import json
from os import listdir, makedirs, path
from uuid import UUID

from shared_datamodel.simulation import Simulation
from geojson_pydantic import FeatureCollection

from src.store import IStore, Region


class Store(IStore):
    def list_regions(self) -> list[UUID]:
        names = listdir("src/data/regions")

        uuids = []
        for name in names:
            try:
                uuids.append(UUID(name))
            except ValueError:
                continue

        return uuids

    def read_region(self, region: UUID) -> Region:
        with open(f"src/data/regions/{region}/area.json", "r") as f:
            area = json.load(f)
        with open(f"src/data/regions/{region}/meta.json", "r") as f:
            meta = json.load(f)
        return Region(id=region, name=meta["name"], area=area)

    def list_simulations(self, region: UUID) -> list[Simulation]:
        region_path = f"src/data/simulations/{region}"
        simulations = []
        if not path.isdir(region_path):
            return simulations

        for simulation_path in [
            path.join(region_path, s) for s in listdir(f"{region_path}/")
        ]:
            if not path.isdir(simulation_path):
                continue
            with open(path.join(simulation_path, "meta.json"), "r") as f:
                s = json.load(f)
                s = Simulation.model_validate(s)
                simulations.append(s)

        return simulations

    def create_simulation(self, simulation: Simulation) -> None:
        makedirs(
            f"src/data/simulations/{simulation.region_id}/{simulation.id}",
            exist_ok=True,
        )
        # Save the simulation metadata

        with open(
            f"src/data/simulations/{simulation.region_id}/{simulation.id}/meta.json",
            "w",
        ) as f:
            f.write(simulation.model_dump_json(indent=2))

    def get_fields(self, region: UUID) -> FeatureCollection | None:
        region_path = f"src/data/simulations/{region}/fields.geojson.gz"

        if not path.exists(region_path):
            return None

        with gzip.open(region_path, "r") as f:
            data = json.loads(f.read().decode("utf-8"))
            data = FeatureCollection.model_validate(data)
            return data

    def get_variables(self, simulation_id: UUID) -> dict | None:
        for region in self.list_regions():
            file_path = f"src/data/simulations/{region}/{simulation_id}/variables.json"
            if path.exists(file_path):
                with open(file_path, "r") as f:
                    return json.load(f)
