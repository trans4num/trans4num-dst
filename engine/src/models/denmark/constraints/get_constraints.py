import operator
import math

from ortools.sat.python import cp_model

from shared_datamodel.simulation import Model
from models.denmark.constraints.accumulated_change import (
    AccumulatedChangeConstraint,
)
from models.denmark.constraints.allow_value import AllowValueConstraint
from models.denmark.constraints.grouped_accumulated_change import (
    GroupedAccumulatedChangeConstraint,
)
from models.denmark.metrics import Metrics
from models.denmark.rotations import rotation_difference
from models.denmark.things import Field
from models.denmark.transitions import Transition, f


def get_ignore_choice_constraints(job_model: Model) -> list[AllowValueConstraint]:
    result = []

    for constraint in job_model.constraints + job_model.goal.configuration:
        # Ignore all constraints which are not enabled
        if not constraint.enabled:
            continue

        if constraint.name == "Distance to Biogas":
            print("Adding biogas constraint")
            constraint_func = AllowValueConstraint(
                constraint.value * 1000, lambda f: f.spatial_indicator.dist_to_biora
            )
            result.append(constraint_func)
        elif constraint.name == "Nature Value":
            print("Adding nature value constraint")
            constraint_func = AllowValueConstraint(
                constraint.value, lambda f: f.spatial_indicator.nature_value_mean
            )
            result.append(constraint_func)

    return result


def get_accumulated_constraints(
    job_model: Model,
    cp_model: cp_model.CpModel,
    original_metrics: Metrics,
    fields: dict[str, Field],
) -> list[AccumulatedChangeConstraint | GroupedAccumulatedChangeConstraint]:
    result = []

    periods = {len(field.rotation.indices) for field in fields.values()}
    periods.update(len(choice.indices) for field in fields.values() for choice in field.choices)
    if 0 in periods:
        raise ValueError("Crop rotations must not be empty")
    # Represent ordinary crop-period averages and four-decimal hectare areas
    # accurately without making the integer model grow without bound.
    economy_scale = min(1_000_000, 10_000 * math.lcm(*periods))
    originals = {}
    def baseline(transition):
        if transition not in originals:
            values = original_metrics.field_revenue if transition == Transition.ECONOMY else original_metrics.field_emission
            originals[transition] = values or {
                field.field_id: f(field.rotation, transition, field.spatial_indicator) for field in fields.values()
            }
        return originals[transition]

    def change_loader(transition):
        values = baseline(transition)
        return lambda choice, field: f(choice, transition, field.spatial_indicator) - values[field.field_id]

    for constraint in job_model.constraints + job_model.goal.configuration:
        # Ignore all constraints which are not enabled
        if not constraint.enabled:
            continue

        if constraint.name == "Single Farmer Impact":
            print("Adding single farmer impact constraint")
            constraint_func = GroupedAccumulatedChangeConstraint(
                cp_model,
                economy_scale,
                operator.ge,
                change_loader(Transition.ECONOMY),
                lambda field: field.spatial_indicator.org_id,
                # This default value of val is INSANELY important.
                # The problem is that the scope in python is not what you expect.
                # This means that if you use `val` in the lambda, it will always
                # use the last value of `constraint.value` in the loop.
                # By using a default value, we ensure that the lambda captures
                # the value of `constraint.value` at the time of creation.
                get_max_change=lambda field, val=constraint.value: (
                    original_metrics.org_revenue[field.spatial_indicator.org_id]
                    * (-val / 100)
                ),
            )
            result.append(constraint_func)

        # Add constraints which accumulate changes over the entire model.
        elif constraint.name == "Area Change":
            print("Adding area change constraint")
            constraint_func = AccumulatedChangeConstraint(
                cp_model,
                1_000_000,
                operator.le,
                lambda choice, field: 0
                if choice.name == field.rotation.name
                else field.spatial_indicator.area,
                max_change=sum(
                    [field.spatial_indicator.area for field in fields.values()]
                )
                * (constraint.value / 100),
            )
            result.append(constraint_func)
        elif constraint.name == "Fields Change":
            print("Adding fields change constraint")
            constraint_func = AccumulatedChangeConstraint(
                cp_model,
                1,
                operator.le,
                lambda choice, field: 0 if choice.name == field.rotation.name else 1,
                max_change=len(fields) * (constraint.value / 100),
            )
            result.append(constraint_func)
        elif constraint.name == "N-Load Change":
            print("Adding N-Load change constraint")
            constraint_func = AccumulatedChangeConstraint(
                cp_model,
                1_000_000,
                operator.le,
                change_loader(Transition.LEACHING),
                max_change=original_metrics.total_emission
                * (constraint.value / 100),
            )
            result.append(constraint_func)
        elif constraint.name == "Economy Change":
            print("Adding economy change constraint")
            constraint_func = AccumulatedChangeConstraint(
                cp_model,
                economy_scale,
                operator.ge,
                change_loader(Transition.ECONOMY),
                max_change=original_metrics.total_revenue
                * (constraint.value / 100),
            )
            result.append(constraint_func)
        elif constraint.name == "Percentage of farm type change":
            print("Adding farm type change constraint")
            constraint_func = AccumulatedChangeConstraint(
                cp_model,
                1,
                operator.le,
                lambda choice, field: 0
                if rotation_difference(field.rotation.indices, choice.indices) <= 3
                else 1,
                max_change=len(fields) * (constraint.value / 100),
            )
            result.append(constraint_func)

        elif constraint.name not in ("Distance to Biogas", "Nature Value"):
            raise ValueError(f"Unsupported enabled constraint: {constraint.name}")

        if constraint.name not in ("Distance to Biogas", "Nature Value"):
            constraint_func.name = constraint.name
            if constraint.name == "Fields Change" and constraint_func.limit() == 0:
                constraint_func.freeze_field = lambda field: True
            elif constraint.name == "Area Change" and constraint_func.limit() == 0:
                constraint_func.freeze_field = lambda field: field.spatial_indicator.area > 0

    return result
