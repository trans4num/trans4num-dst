#!/usr/bin/env python3
"""Generate deterministic, synthetic local data for development."""

import argparse
import csv
import json
import math
import random
from pathlib import Path
from typing import Iterable


DEFAULT_REGION_ID = "8b7127be-5cf8-4c2f-838e-b483724bcc58"
FIELD_COUNT = 2000
SEED = 20260819

# A coarse, synthetic approximation of the Limfjorden area. It is only used
# when a local region area has not already been supplied.
FALLBACK_AREA = {
    "type": "Polygon",
    "coordinates": [
        [
            [8.80, 56.40],
            [9.00, 56.15],
            [9.40, 56.12],
            [10.12, 56.53],
            [9.45, 56.88],
            [9.00, 56.84],
            [8.80, 56.50],
            [8.80, 56.40],
        ]
    ],
}

ROTATIONS = [
    [10, 10, 5, 3, 8, 7, 6],
    [10, 10, 10, 6, 2, 2, 2],
    [10, 10, 10, 10, 5, 1, 8],
    [10, 11, 5, 3, 1, 8, 6],
    [6, 9, 1, 6, 6, 9, 3],
    [10, 11, 5, 1, 6, 5, 1],
    [10, 10, 10, 6, 2, 2, 6],
    [10, 10, 10, 10, 6, 1, 6],
    [11, 11, 6, 3, 8, 1, 6],
    [11, 11, 11, 6, 5, 4, 6],
    [11, 11, 6, 3, 4, 1, 6],
    [12, 12, 12, 12, 12, 12, 12],
]


def point_in_polygon(point: tuple[float, float], ring: list[list[float]]) -> bool:
    x, y = point
    inside = False
    previous_x, previous_y = ring[-1]
    for current_x, current_y in ring:
        crosses = (current_y > y) != (previous_y > y)
        if crosses:
            intersection_x = (previous_x - current_x) * (y - current_y) / (
                previous_y - current_y
            ) + current_x
            if x < intersection_x:
                inside = not inside
        previous_x, previous_y = current_x, current_y
    return inside


def square_inside(
    min_x: float,
    min_y: float,
    max_x: float,
    max_y: float,
    ring: list[list[float]],
) -> bool:
    return all(
        point_in_polygon(point, ring)
        for point in (
            (min_x, min_y),
            (min_x, max_y),
            (max_x, min_y),
            (max_x, max_y),
        )
    )


def bounds(ring: list[list[float]]) -> tuple[float, float, float, float]:
    longitudes = [point[0] for point in ring]
    latitudes = [point[1] for point in ring]
    return min(longitudes), min(latitudes), max(longitudes), max(latitudes)


def grid_squares(ring: list[list[float]], count: int) -> list[tuple[float, float, float, float]]:
    min_x, min_y, max_x, max_y = bounds(ring)
    width = max_x - min_x
    height = max_y - min_y
    aspect = width / height

    for scale in range(1, 12):
        columns = math.ceil(math.sqrt(count * aspect) * scale)
        rows = math.ceil(columns / aspect)
        cell_width = width / columns
        cell_height = height / rows
        candidates = []
        for row in range(rows):
            for column in range(columns):
                cell_min_x = min_x + column * cell_width
                cell_min_y = min_y + row * cell_height
                cell_max_x = cell_min_x + cell_width
                cell_max_y = cell_min_y + cell_height
                if square_inside(cell_min_x, cell_min_y, cell_max_x, cell_max_y, ring):
                    candidates.append((cell_min_x, cell_min_y, cell_max_x, cell_max_y))

        if len(candidates) >= count:
            step = len(candidates) / count
            return [candidates[min(int(index * step), len(candidates) - 1)] for index in range(count)]

    raise RuntimeError("The region polygon is too small to place 2,000 fake fields")


def haversine_km(first: tuple[float, float], second: tuple[float, float]) -> float:
    longitude_1, latitude_1 = map(math.radians, first)
    longitude_2, latitude_2 = map(math.radians, second)
    delta_longitude = longitude_2 - longitude_1
    delta_latitude = latitude_2 - latitude_1
    value = (
        math.sin(delta_latitude / 2) ** 2
        + math.cos(latitude_1) * math.cos(latitude_2) * math.sin(delta_longitude / 2) ** 2
    )
    return 6371 * 2 * math.asin(math.sqrt(value))


def load_or_create_area(area_path: Path) -> dict:
    if area_path.exists():
        return json.loads(area_path.read_text())
    return FALLBACK_AREA


def write_region(root: Path, region_id: str, area: dict) -> None:
    region_path = root / "backend" / "src" / "data" / "regions" / region_id
    region_path.mkdir(parents=True, exist_ok=True)
    (region_path / "area.json").write_text(json.dumps(area, indent=2) + "\n")
    meta_path = region_path / "meta.json"
    if not meta_path.exists():
        meta_path.write_text(json.dumps({"name": "Fake Limfjorden"}, indent=2) + "\n")


def write_fields(root: Path, squares: Iterable[tuple[float, float, float, float]]) -> None:
    data_path = root / "engine" / "data"
    data_path.mkdir(parents=True, exist_ok=True)
    csv_path = data_path / "Fields2023_DataDST_May2025.csv"
    geometry_path = data_path / "fake-fields.geojson"
    center = (9.46, 56.50)
    randomizer = random.Random(SEED)
    crop_columns = [f"AgCropNr{year}" for year in range(17, 24)]
    columns = crop_columns + [
        "CVR",
        "IMK_ID",
        "Soil_ID",
        "RedTot",
        "IMK_areal",
        "BiogasNetM",
        "PctHnvOve5",
    ]
    features = []

    with csv_path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=columns)
        writer.writeheader()
        for index, (min_x, min_y, max_x, max_y) in enumerate(squares, start=1):
            field_center = ((min_x + max_x) / 2, (min_y + max_y) / 2)
            rotation = ROTATIONS[(index - 1) % len(ROTATIONS)]
            writer.writerow(
                {
                    **{column: crop for column, crop in zip(crop_columns, rotation)},
                    "CVR": 90000000 + (index - 1) // 20,
                    "IMK_ID": index,
                    "Soil_ID": 10 if index % 3 else 20,
                    "RedTot": round(randomizer.uniform(35, 90), 2),
                    "IMK_areal": round(randomizer.uniform(0.5, 4.0), 4),
                    "BiogasNetM": round(haversine_km(center, field_center), 2),
                    "PctHnvOve5": round(randomizer.uniform(0, 45), 2),
                }
            )
            features.append(
                {
                    "type": "Feature",
                    "id": f"f-{index}",
                    "properties": {"IMK_ID": index},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [min_x, min_y],
                                [min_x, max_y],
                                [max_x, max_y],
                                [max_x, min_y],
                                [min_x, min_y],
                            ]
                        ],
                    },
                }
            )

    geometry_path.write_text(
        json.dumps(
            {"type": "FeatureCollection", "name": "fake-fields", "features": features}
        )
        + "\n"
    )
    (data_path / ".trans4num-fake-data").write_text("Generated by trans4num.\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--region-id", default=DEFAULT_REGION_ID)
    args = parser.parse_args()

    root = args.root.resolve()
    area_path = root / "backend" / "src" / "data" / "regions" / args.region_id / "area.json"
    area = load_or_create_area(area_path)
    ring = area["coordinates"][0]
    write_region(root, args.region_id, area)
    write_fields(root, grid_squares(ring, FIELD_COUNT))
    print(f"Generated {FIELD_COUNT} fake fields for region {args.region_id}.")


if __name__ == "__main__":
    main()
