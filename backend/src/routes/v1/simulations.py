from datetime import datetime, timezone
from typing import List
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, Response
from shared_datamodel.schema import BaseSchema
from shared_datamodel.simulation import Simulation, SimulationBase, SimulationStatus

from src.job_queue import IEngineJobQueue
from src.store import IStore


class SimulationResponse(BaseSchema):
    status_quo: Simulation
    simulations: List[Simulation]


class SimulationUpdate(BaseSchema):
    deleted: bool


def get_router(store: IStore, queue: IEngineJobQueue) -> APIRouter:
    router = APIRouter(prefix="/simulations", tags=["simulations"])

    def find_simulation(simulation_id: UUID) -> Simulation | None:
        for region in store.list_regions():
            simulation = next(
                (s for s in store.list_simulations(region) if s.id == simulation_id),
                None,
            )
            if simulation is not None:
                return simulation
        return None

    @router.get("")
    async def get_simulation(
        region: UUID = Query(
            description="The id of the region for which to fetch simulations.",
        ),
    ) -> SimulationResponse:
        """Get a list of all available simulations for the region."""

        simulations = store.list_simulations(region)
        if len(simulations) == 0:
            raise HTTPException(
                status_code=404, detail="No simulations found for region"
            )
        status_quo = next((s for s in simulations if s.name == "Status Quo"), None)
        if status_quo is None:
            raise HTTPException(
                status_code=404, detail="Status Quo not found for region"
            )
        non_status_quo_simulations = [s for s in simulations if s.name != "Status Quo"]
        return SimulationResponse(
            simulations=non_status_quo_simulations, status_quo=status_quo
        )

    @router.post("")
    async def create_simulation(
        body: SimulationBase,
    ):
        """Create a new simulation."""

        simulation = Simulation(
            id=uuid4(),
            name=body.name,
            region_id=body.region_id,
            model=body.model,
            summary=[],
            charts=[],
            barCharts=[],
            status=SimulationStatus.PROCESSING,
            created=datetime.now(timezone.utc),
        )

        try:
            store.create_simulation(simulation)
            queue.enqueue_simulation(
                region_id=simulation.region_id,
                simulation_id=simulation.id,
            )
        except Exception as e:
            if str(e) == "Region does not exist":
                raise HTTPException(status_code=404, detail="Region does not exist")
            raise

        return {"message": "Simulation created", "id": simulation.id}

    @router.patch("/{simulation_id}")
    async def update_simulation(simulation_id: UUID, body: SimulationUpdate):
        """Soft-delete or restore a simulation."""
        simulation = find_simulation(simulation_id)
        if simulation is None:
            raise HTTPException(status_code=404, detail="Simulation not found")

        updated_simulation = simulation.model_copy(
            update={"deleted": body.deleted}
        )
        store.update_simulation(updated_simulation)
        return updated_simulation

    @router.delete("/{simulation_id}", status_code=204)
    async def delete_simulation(simulation_id: UUID) -> Response:
        """Permanently delete a simulation."""
        if find_simulation(simulation_id) is None:
            raise HTTPException(status_code=404, detail="Simulation not found")

        store.delete_simulation(simulation_id)
        return Response(status_code=204)

    return router
