import operator

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

    for constraint in job_model.constraints + job_model.goal.configuration:
        # Ignore all constraints which are not enabled
        if not constraint.enabled:
            continue

        if constraint.name == "Single Farmer Impact":
            print("Adding single farmer impact constraint")
            constraint_func = GroupedAccumulatedChangeConstraint(
                cp_model,
                10,
                operator.ge,
                lambda choice, field: f(
                    choice, Transition.ECONOMY, field.spatial_indicator
                ),
                lambda field: field.spatial_indicator.org_id,
                # This default value of val is INSANELY important.
                # The problem is that the scope in python is not what you expect.
                # This means that if you use `val` in the lambda, it will always
                # use the last value of `constraint.value` in the loop.
                # By using a default value, we ensure that the lambda captures
                # the value of `constraint.value` at the time of creation.
                get_max_change=lambda field, val=constraint.value: (
                    original_metrics.org_revenue[field.spatial_indicator.org_id]
                    * ((100 - val) / 100)
                ),
            )
            result.append(constraint_func)

        # Add constraints which accumulate changes over the entire model.
        elif constraint.name == "Area Change":
            print("Adding area change constraint")
            constraint_func = AccumulatedChangeConstraint(
                cp_model,
                100,
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
                lambda choice, field: f(
                    choice, Transition.LEACHING, field.spatial_indicator
                ),
                max_change=original_metrics.total_emission
                * ((100 + constraint.value) / 100),
            )
            result.append(constraint_func)
        elif constraint.name == "Economy Change":
            print("Adding economy change constraint")
            constraint_func = AccumulatedChangeConstraint(
                cp_model,
                10,
                operator.ge,
                lambda choice, field: f(
                    choice, Transition.ECONOMY, field.spatial_indicator
                ),
                max_change=original_metrics.total_revenue
                * ((100 + constraint.value) / 100),
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

    return result
