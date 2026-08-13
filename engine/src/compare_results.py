import json
from os import listdir, path

simulations = []
status_quo = None

for region in listdir("simulations"):
    region_path = path.join("simulations", region)
    for simulation_id in listdir(region_path):
        print(region, simulation_id)
        simulation_path = path.join(
            region_path,
            simulation_id,
        )

        if not path.isdir(simulation_path):
            continue

        with open(path.join(simulation_path, "meta.json"), "r") as f:
            simulation = json.load(f)
        with open(path.join(simulation_path, "variables.json"), "r") as f:
            fields = json.load(f)

        entry = {"meta": simulation, "fields": fields}

        if simulation["name"] == "Status Quo":
            if status_quo is not None:
                raise Exception("Multiple status quo exists. That should never happen")
            status_quo = entry
        else:
            simulations.append(entry)

if len(simulations) == 0:
    raise Exception("No simulations exists")

if status_quo is None:
    raise Exception("No status quo exists")


crop_set_status_quo = {}

for field in status_quo["fields"]:
    crop = field["crop"]
    if crop not in crop_set_status_quo:
        crop_set_status_quo[crop] = 0
    crop_set_status_quo[crop] += 1

for simulation in simulations:
    print("")
    print("####")
    print(simulation["meta"]["name"])
    print("####")

    print(simulation["meta"]["goalType"])
    print(simulation["meta"]["constraints"])
    if set(simulation["meta"]["summary"].keys()) != set(
        status_quo["meta"]["summary"].keys()
    ):
        raise Exception("Keys in summary is not matching")

    for key, status_quo_value in status_quo["meta"]["summary"].items():
        simulation_value = simulation["meta"]["summary"][key]
        print(key, simulation_value / status_quo_value)

    crop_set = {}
    for field in simulation["fields"]:
        crop = field["crop"]
        if crop not in crop_set:
            crop_set[crop] = 0
        crop_set[crop] += 1

    print("")
    print("Crops")
    for crop, old_count in crop_set_status_quo.items():
        new_count = crop_set[crop] if crop in crop_set else 1
        print(crop, new_count / old_count)
