from dataclasses import dataclass
import math

from models.denmark.things import Field
from models.denmark.transitions import Transition, f
from dataclasses import field as dataclass_field


@dataclass
class Metrics:
    total_emission: float
    total_revenue: float
    org_revenue: dict[str, float]
    total_area: float
    field_revenue: dict[str, float] = dataclass_field(default_factory=dict)
    field_emission: dict[str, float] = dataclass_field(default_factory=dict)


def get_metrics(fields: dict[str, Field]) -> Metrics:
    revenues = {}
    emissions = {}
    org_revenue = {}
    for field in fields.values():
        emission = f(field.rotation, Transition.LEACHING, field.spatial_indicator)
        econ = f(field.rotation, Transition.ECONOMY, field.spatial_indicator)
        emissions[field.field_id] = emission
        revenues[field.field_id] = econ
        org = field.spatial_indicator.org_id
        if org not in org_revenue:
            org_revenue[org] = []
        org_revenue[org].append(econ)

    return Metrics(
        total_emission=math.fsum(emissions.values()),
        total_revenue=math.fsum(revenues.values()),
        org_revenue={org: math.fsum(values) for org, values in org_revenue.items()},
        total_area=math.fsum(field.spatial_indicator.area for field in fields.values()),
        field_revenue=revenues,
        field_emission=emissions,
    )
