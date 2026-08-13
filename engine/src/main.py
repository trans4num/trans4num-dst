from uuid import UUID, uuid4

from models.denmark.load import load_fields
from models.denmark.metrics import get_metrics
from models.denmark.model import setup_model
from models.denmark.output import create_output
from models.denmark.rotations import rotations
from models.denmark.things import Field
from optimize.optimize import optimize_region
from shared_datamodel.simulation import (
    SimulationBase,
)
from store import IStore


def run(store: IStore, job: SimulationBase, simulation_id: UUID | None = None):
    if simulation_id is None:
        simulation_id = uuid4()
    # Status Quo is created only when the region does not have one yet.
    if job.model is None:
        if job.name != "Status Quo":
            raise Exception("Job model must be set for non-status quo jobs.")
        if store.region_exists(job.region_id):
            for simulation_id in store.list_simulations(job.region_id):
                if not store.simulation_exists(job.region_id, simulation_id):
                    continue
                meta = store.read_meta(job.region_id, simulation_id)
                if meta.name == "Status Quo":
                    print("Status Quo already exists, skipping creation.")
                    return

    print("Load the data")
    fields = load_fields(store, job.region_id)
    print("Got fields")

    original_fields = fields.copy()
    original_metrics = get_metrics(fields)

    if job.model:
        print("Set up model")
        model, x = setup_model(
            fields=fields,
            original_metrics=original_metrics,
            job_model=job.model,
        )
        result = optimize_region(model, x)
        if not result.success or result.result is None:
            print(result)
            raise Exception("Optimization failed, cannot create output.")
            return
        print(result.description)
        # Based on the optimization change the crops
        selected = {r[0]: r[1] for r in result.result}

        rotation_dict = {rotation.name: rotation for rotation in rotations}
        next_fields = {}
        for field_id, field in fields.items():
            next_fields[field_id] = Field(
                field_id=field.field_id,
                spatial_indicator=field.spatial_indicator,
                rotation=rotation_dict[selected[field_id]]
                if field_id in selected and selected[field_id] in rotation_dict
                else field.rotation,
                choices=field.choices,
            )
        fields = next_fields
        # Recalculate the metrics based on the new crops
        metrics = get_metrics(fields)
    else:
        metrics = original_metrics
    # Save our output
    create_output(
        store=store,
        fields=fields,
        metrics=metrics,
        original_metrics=original_metrics,
        job=job,
        original_fields=original_fields,
        simulation_id=simulation_id,
    )
