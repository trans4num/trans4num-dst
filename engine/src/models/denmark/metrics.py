from dataclasses import dataclass

from models.denmark.things import Field
from models.denmark.transitions import Transition, f
from nbalance.calculate import n_balance_for_field


@dataclass
class Metrics:
    total_emission: float
    total_revenue: float
    org_revenue: dict[str, int]
    total_area: float


def get_metrics(fields: dict[str, Field]) -> Metrics:
    total_revenue = 0
    total_emision = 0
    total_area = 0
    org_revenue = {}
    for field in fields.values():
        emission = f(field.rotation, Transition.LEACHING, field.spatial_indicator)
        econ = f(field.rotation, Transition.ECONOMY, field.spatial_indicator)
        total_emision += emission
        total_revenue += econ
        total_area += field.spatial_indicator.area
        org = field.spatial_indicator.org_id
        if org not in org_revenue:
            org_revenue[org] = 0
        org_revenue[org] += econ

    return Metrics(
        total_emission=total_emision,
        total_revenue=total_revenue,
        org_revenue=org_revenue,
        total_area=total_area,
    )
