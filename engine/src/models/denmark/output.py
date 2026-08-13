import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from uuid import UUID

from models.denmark.metrics import Metrics
from models.denmark.things import Field
from models.denmark.transitions import Transition
from models.denmark.transitions import f as the_function
from nbalance.calculate import NBalance, n_balance_for_field
from osgeo import gdal, osr
from shared_datamodel.simulation import (
    BarChart,
    BarChartData,
    Chart,
    Simulation,
    SimulationBase,
    SimulationStatus,
    SummaryEntry,
)
from store import IStore

gdal.UseExceptions()


@dataclass
class ResultEntry:
    field_id: str
    economy: float
    leaching: float
    nature_value: float
    crop: str


def create_output(
    store: IStore,
    fields: dict[str, Field],
    job: SimulationBase,
    metrics: Metrics,
    original_metrics: Metrics,
    original_fields: dict[str, Field],
    simulation_id: UUID,
):
    field_ids: set[str] = set()

    total_fields = len(fields)
    unchanged_fields = 0
    unchanged_area = 0

    res: list[ResultEntry] = []
    for field in fields.values():
        field_id = str(field.field_id)
        field_ids.add(field_id)

        original_field_id = original_fields[field.field_id].field_id
        if not field.field_id == original_field_id:
            raise Exception(
                f"We are not comparing the same fields {field.field_id, original_field_id}"
            )

        if field.rotation.name == original_fields[field.field_id].rotation.name:
            unchanged_fields += 1
            unchanged_area += field.spatial_indicator.area

        emission = the_function(
            field.rotation, Transition.LEACHING, field.spatial_indicator
        )
        econ = the_function(field.rotation, Transition.ECONOMY, field.spatial_indicator)

        res.append(
            ResultEntry(
                field_id=field.field_id,
                economy=round(econ / field.spatial_indicator.area, 2),
                leaching=round(emission / field.spatial_indicator.area, 2),
                nature_value=field.spatial_indicator.nature_value_mean,
                crop=field.rotation.name,
            )
        )

    field_consistency = (unchanged_fields / total_fields) * 100
    area_consistency = (unchanged_area / metrics.total_area) * 100

    print("Generating fields geojson")
    features = []
    data_src = store.read_fields_shapefile(job.region_id)
    layer = data_src.GetLayer()
    source_srs = layer.GetSpatialRef()
    target_srs = osr.SpatialReference()
    target_srs.ImportFromEPSG(4326)
    transform = osr.CoordinateTransformation(source_srs, target_srs)

    for feature in layer:
        field_id = f"f-{feature.GetField('IMK_ID')}"

        if field_id in field_ids:
            geom = feature.GetGeometryRef()
            geom = geom.Simplify(10.0)
            geom.Transform(transform)
            features.append(
                {
                    "type": "Feature",
                    "properties": {},
                    "id": str(field_id),
                    "geometry": json.loads(geom.ExportToJson(["XY_COORD_PRECISION=5"])),
                }
            )

    print("Features", len(features))

    store.write_geometries_if_missing(
        region_id=job.region_id,
        featurecollection_str=json.dumps(
            {
                "type": "FeatureCollection",
                "name": str(job.region_id),
                "features": features,
            }
        ),
    )

    res_dict = {str(r.field_id): asdict(r) for r in res}
    store.write_debug_geometries(
        region_id=job.region_id,
        simulation_id=simulation_id,
        featurecollection_str=json.dumps(
            {
                "type": "FeatureCollection",
                "name": str(job.region_id),
                "features": [{**f, "properties": res_dict[f["id"]]} for f in features],
            }
        ),
    )

    store.write_variables(
        region_id=job.region_id,
        simulation_id=simulation_id,
        json_str=json.dumps([asdict(r) for r in res]),
    )

    # Crop Chart
    crop_area = {}
    for field in fields.values():
        for crop in field.rotation.indices:
            if str(crop) not in crop_area:
                crop_area[str(crop)] = 0
            crop_area[str(crop)] += field.spatial_indicator.area / len(
                field.rotation.indices
            )

    crop_chart = Chart(
        name="Crops In Rotation",
        values=crop_area,
    )

    # Rotation Chart
    rotation_area = {}
    for field in fields.values():
        rotation_name = field.rotation.name
        if rotation_name not in rotation_area:
            rotation_area[rotation_name] = 0
        rotation_area[rotation_name] += field.spatial_indicator.area
    rotation_chart = Chart(
        name="Rotations",
        values=rotation_area,
    )

    # NBalance Bar Chart
    n_balance_for_fields = [n_balance_for_field(field) for field in fields.values()]
    summed_n_values = NBalance.sum(n_balance_for_fields)
    n_balance_per_ha = summed_n_values.scaled(1 / metrics.total_area)
    barCharts = [
        BarChart(
            chartName="N-Balance",
            unit="kg N/ha",
            chartData=[
                BarChartData(
                    name="Input",
                    values={
                        "Manure": n_balance_per_ha.in_manure,
                        "Fertilizer": n_balance_per_ha.in_fertilizer,
                        "Other": n_balance_per_ha.in_other,
                        "Fixated": n_balance_per_ha.fixated,
                    },
                ),
                BarChartData(
                    name="Output",
                    values={
                        "Harvested": n_balance_per_ha.harvested,
                        "Losses": n_balance_per_ha.out_losses,
                    },
                ),
                BarChartData(
                    name="Balance",
                    values={
                        "Input": n_balance_per_ha.in_total,
                        "Output": n_balance_per_ha.out_total,
                        "Balance": n_balance_per_ha.balance,
                    },
                ),
            ],
        ),
    ]
    store.write_meta(
        region_id=job.region_id,
        simulation_id=simulation_id,
        simulation=Simulation(
            name=job.name,
            region_id=job.region_id,
            model=job.model,
            id=simulation_id,
            created=datetime.now(timezone.utc),
            status=SimulationStatus.SUCCESS,
            charts=[crop_chart, rotation_chart],
            barCharts=barCharts,
            summary=[
                SummaryEntry(
                    name="economy", value=round(metrics.total_revenue, 2), unit="DKK"
                ),
                SummaryEntry(
                    name="nature",
                    value=round(sum([e.nature_value for e in res]) / len(res), 2),
                    unit="",
                ),
                SummaryEntry(
                    name="consistency", value=round(area_consistency, 2), unit="%"
                ),
                SummaryEntry(
                    name="fieldConsistency", value=round(field_consistency, 2), unit="%"
                ),
                SummaryEntry(
                    name="farmEconomy",
                    value=most_affected_farm(metrics, original_metrics),
                    unit="%",
                ),
                SummaryEntry(
                    name="nload", value=round(metrics.total_emission, 2), unit="kg N"
                ),
                SummaryEntry(
                    name="nloadPerEcon",
                    value=round(metrics.total_emission / metrics.total_revenue, 6),
                    unit="kg N / DKK",
                ),
            ],
        ),
    )


def most_affected_farm(metrics: Metrics, original_metrics: Metrics):
    worst_ratio = math.inf
    for org_id, new_org_revenue in metrics.org_revenue.items():
        old_org_revenue = original_metrics.org_revenue[org_id]
        ratio = new_org_revenue / old_org_revenue
        worst_ratio = min(worst_ratio, ratio)
    return worst_ratio * 100
