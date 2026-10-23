from ortools.sat.python import cp_model
import math

from shared_datamodel.simulation import Model, SimulationGoalType
from models.denmark.constraints.get_constraints import get_accumulated_constraints, get_ignore_choice_constraints
from models.denmark.metrics import Metrics
from models.denmark.prepare import PreparedProblem, prepare_problem, propagate_constraints
from models.denmark.things import Field
from utils import print_runtime
from optimize.fractional import enforce_positive_economy


def prepare_model(fields, original_metrics, job_model):
    model = cp_model.CpModel()
    constraints = get_accumulated_constraints(job_model, model, original_metrics, fields)
    problem = prepare_problem(fields, constraints, get_ignore_choice_constraints(job_model), job_model.goal.type)
    if problem.goal_type == SimulationGoalType.MAX_ECON_PER_NLOAD:
        enforce_positive_economy(model, problem)
        propagate_constraints(problem)
    return model, problem


def build_model(model: cp_model.CpModel, problem: PreparedProblem, hint=None):
    if problem.goal_type == SimulationGoalType.MAX_ECON_PER_NLOAD:
        raise ValueError("Regional ratios must use the fractional solve_region pipeline")
    hint_set = set(hint) if hint is not None else None
    x = {}
    for key, choices in problem.choices.items():
        if len(choices) == 1:
            choice = choices[0]
            x[key, choice.rotation.name] = True
            for constraint, coefficient in zip(problem.constraints, choice.coefficients):
                constraint.add_coefficient(problem.fields[key], coefficient, True)
            continue
        variables = []
        for choice in choices:
            # The mapping already identifies each variable; repeating field and
            # rotation names in the proto wastes memory in every solver copy.
            variable = model.NewBoolVar("")
            x[key, choice.rotation.name] = variable
            variables.append(variable)
            if hint_set is not None:
                model.AddHint(variable, (key, choice.rotation.name) in hint_set)
            for constraint, coefficient in zip(problem.constraints, choice.coefficients):
                constraint.add_coefficient(problem.fields[key], coefficient, variable)
        model.AddExactlyOne(variables)
    for constraint in problem.constraints:
        constraint.constraint()
    set_objective(model, problem, x)
    return model, x


def set_objective(model, problem, x):
    fixed = []
    variables, coefficients = [], []
    for key, choices in problem.choices.items():
        for choice in choices:
            variable = x[key, choice.rotation.name]
            if variable is True:
                fixed.append(choice.cost)
            elif choice.cost:
                variables.append(variable)
                coefficients.append(choice.cost)
    if variables:
        model.Minimize(cp_model.LinearExpr.WeightedSum(variables, coefficients) + math.fsum(fixed))
    else:
        # OR-Tools requires an expression rather than a bare float objective.
        model.Minimize(math.fsum(fixed) * model.NewConstant(1))


def set_hint(model, x, hint):
    model.ClearHints()
    if hint is not None:
        hint_set = set(hint)
        for key, variable in x.items():
            if variable is not True:
                model.AddHint(variable, key in hint_set)


@print_runtime
def setup_model(fields: dict[str, Field], original_metrics: Metrics, job_model: Model, hint=None):
    model, problem = prepare_model(fields, original_metrics, job_model)
    return build_model(model, problem, hint)
