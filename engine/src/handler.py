import argparse
import json
from os import getenv
from uuid import UUID

from main import run
from shared_datamodel.simulation import SimulationBase
from store import IStore, get_store


def _run_simulation(region_id: UUID, simulation_id: UUID, store: IStore) -> None:
    job = store.read_meta(
        region_id=region_id,
        simulation_id=simulation_id,
    )

    try:
        run(store, job, simulation_id=simulation_id)
    except Exception:
        print("Failed, now update that it failed")
        store.update_meta_to_failed(region_id=region_id, simulation_id=simulation_id)


def _run_status_quo(region_id: UUID, store: IStore) -> None:
    job = SimulationBase(
        name="Status Quo",
        region_id=region_id,
        model=None,
    )
    run(store, job, simulation_id=None)


def handler(event, context):
    # The store defaults to S3.
    store = get_store(store_type=getenv("STORE_TYPE", "s3"))

    records = event["Records"]
    for record in records:
        body = json.loads(record["body"])

    region = body["region"]
    region_id = UUID(region)
    create_status_quo = body.get("create_status_quo", False)
    if create_status_quo:
        _run_status_quo(region_id=region_id, store=store)
        return

    simulation = body["simulation"]
    simulation_id = UUID(simulation)
    _run_simulation(region_id=region_id, simulation_id=simulation_id, store=store)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Invoke the engine locally using shared storage metadata."
    )
    parser.add_argument("simulation", nargs="?", help="Simulation UUID.")
    parser.add_argument(
        "--region",
        default="8b7127be-5cf8-4c2f-838e-b483724bcc58",
        help="Region UUID (defaults to the demo region).",
    )
    parser.add_argument(
        "--create-status-quo",
        action="store_true",
        help="Create status quo for the region (no simulation UUID required).",
    )
    parser.add_argument(
        "--store-type",
        default="s3",
        help="Store type to use (defaults to s3).",
    )
    args = parser.parse_args()
    if not args.create_status_quo and args.simulation is None:
        parser.error("simulation is required unless --create-status-quo is set")

    payload = {
        "region": args.region,
        "create_status_quo": args.create_status_quo,
    }
    if args.simulation is not None:
        payload["simulation"] = args.simulation
    event = {"Records": [{"body": json.dumps(payload)}]}
    handler(event, context=None)
