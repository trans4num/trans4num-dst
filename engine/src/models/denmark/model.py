from ortools.sat.python import cp_model

from shared_datamodel.simulation import Model
from models.denmark.constraints.get_constraints import get_accumulated_constraints, get_ignore_choice_constraints
from models.denmark.metrics import Metrics
from models.denmark.prepare import PreparedProblem, prepare_problem
from models.denmark.things import Field
from utils import print_runtime


def prepare_model(fields, original_metrics, job_model):
    model = cp_model.CpModel()
    constraints = get_accumulated_constraints(job_model, model, original_metrics, fields)
    return model, prepare_problem(fields, constraints, get_ignore_choice_constraints(job_model), job_model.goal.type)


def build_model(model: cp_model.CpModel, problem: PreparedProblem, hint=None):
    hint_set = set(hint) if hint is not None else None
    x = {}
    costs = []
    for key, choices in problem.choices.items():
        variables = []
        for choice in choices:
            variable = model.NewBoolVar(f"x_{key}_{choice.rotation.name}")
            x[key, choice.rotation.name] = variable
            variables.append(variable)
            if hint_set is not None:
                model.AddHint(variable, (key, choice.rotation.name) in hint_set)
            for constraint, coefficient in zip(problem.constraints, choice.coefficients):
                constraint.add_coefficient(problem.fields[key], coefficient, variable)
            costs.append(choice.cost * variable)
        model.AddExactlyOne(variables)
    for constraint in problem.constraints:
        constraint.constraint()
    model.Minimize(sum(costs))
    return model, x


@print_runtime
def setup_model(fields: dict[str, Field], original_metrics: Metrics, job_model: Model, hint=None):
    model, problem = prepare_model(fields, original_metrics, job_model)
    return build_model(model, problem, hint)
