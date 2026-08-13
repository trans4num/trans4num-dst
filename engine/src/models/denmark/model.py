from dataclasses import dataclass, field

from ortools.sat.python import cp_model

from shared_datamodel.simulation import Model, SimulationGoalType
from models.denmark.constraints.get_constraints import (
    get_accumulated_constraints,
    get_ignore_choice_constraints,
)
from models.denmark.metrics import Metrics
from models.denmark.things import CropRotation, Field
from models.denmark.transitions import Transition, f
from utils import print_runtime


@dataclass
class RotationSetEntry:
    original_count: int = 0
    terms: list = field(default_factory=lambda: [])


@print_runtime
def setup_model(
    fields: dict[str, Field],
    original_metrics: Metrics,
    job_model: Model,
    hint: list[tuple[int, int]] | None = None,
) -> tuple[cp_model.CpModel, dict]:
    model = cp_model.CpModel()

    hint_set = None
    if hint is not None:
        hint_set = set(hint)

    # X contains the boolean variables that "hot" encodes selections.
    x = {}

    cost_terms = []

    ignore_choice_constraints = get_ignore_choice_constraints(job_model)
    accumulated_constraints = get_accumulated_constraints(
        job_model, model, original_metrics, fields
    )

    for field_entry in fields.values():
        try:
            possible_field_choices: list[CropRotation] = []
            for choice in field_entry.choices + [field_entry.rotation]:
                # Do not even add a choice to the model when valueconstraint is not met.
                if choice.name != field_entry.rotation.name:
                    should_ignore_choice = False
                    for choice_constraint in ignore_choice_constraints:
                        if not choice_constraint.allow(field_entry):
                            should_ignore_choice = True
                            break
                    if should_ignore_choice:
                        continue

                # We need this to constraint to one of the possible choices.
                possible_field_choices.append(choice)

                # Set up the boolean decision variable for this choice.
                xij = model.NewBoolVar(f"x_{field_entry.field_id}_{choice.name}")
                x[field_entry.field_id, choice.name] = xij

                # Add hints to the model if provided.
                if hint_set is not None:
                    if (field_entry.field_id, choice.name) in hint_set:
                        model.AddHint(xij, True)
                    else:
                        model.AddHint(xij, False)

                # Add al the accumulating terms to the constraints
                for constraint in accumulated_constraints:
                    constraint.add_term(choice, field_entry, xij)

                # Finally create the terms for our cost function
                # We could probably optimize a bit here, since the eimission and econ terms also exists as constraints.
                emission = f(choice, Transition.LEACHING, field_entry.spatial_indicator)
                econ = f(choice, Transition.ECONOMY, field_entry.spatial_indicator)
                emission_term = emission * xij
                econ_term = econ * xij

                goal_type = getattr(job_model.goal, "type")
                if goal_type == SimulationGoalType.MIN_NLOAD:
                    cost_terms.append(emission_term)
                elif goal_type == SimulationGoalType.MAX_ECONOMY:
                    cost_terms.append(-econ_term)
                elif goal_type == SimulationGoalType.MAX_ECON_PER_NLOAD:
                    cost_terms.append((emission / econ) * xij)
                else:
                    raise ValueError(f"Unknown goal type: {goal_type}")

            # This add the constraint that we must select a field exactly once.
            model.Add(
                sum(
                    [
                        x[field_entry.field_id, choice.name]
                        for choice in possible_field_choices
                    ]
                )
                == 1
            )
        except:
            print(field_entry.field_id, econ, emission)
            raise Exception("STOP")

    # Finally add the constraints to the model
    for constraint in accumulated_constraints:
        constraint.constraint()

    model.Minimize(sum(cost_terms))
    return model, x
