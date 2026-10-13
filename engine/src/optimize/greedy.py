"""Improve a feasible seed without relaxing any supported hard constraint."""
import operator
from models.denmark.constraints.accumulated_change import AccumulatedChangeConstraint
from models.denmark.constraints.grouped_accumulated_change import GroupedAccumulatedChangeConstraint
from models.denmark.prepare import is_feasible


def _state(problem, selected):
    totals, limits, scopes = {}, {}, {}
    for key, choice in selected.items():
        field_scopes = []
        for index, constraint in enumerate(problem.constraints):
            if type(constraint) is GroupedAccumulatedChangeConstraint:
                field = problem.fields[key]
                scope = (index, constraint.grouper(field))
                limit = constraint.limit(field)
            else:
                scope = (index, None)
                limit = constraint.limit()
            field_scopes.append(scope)
            limits.setdefault(scope, limit)
            totals[scope] = totals.get(scope, 0) + choice.coefficients[index]
        scopes[key] = field_scopes

    return totals, limits, scopes


def improve_seed(problem, initial):
    if initial is None or not is_feasible(problem, initial):
        return None
    selected = initial.copy()
    totals, limits, scopes = _state(problem, selected)
    moves = [(selected[key].cost - choice.cost, key, index)
             for key, choices in problem.choices.items()
             for index, choice in enumerate(choices) if choice.cost < selected[key].cost]
    moves.sort(reverse=True)
    for _, key, index in moves:
        choice, previous = problem.choices[key][index], selected[key]
        if choice.cost >= previous.cost:
            continue
        changes = [totals[scope] + new - old
                   for scope, new, old in zip(scopes[key], choice.coefficients, previous.coefficients)]
        if all(constraint.operator(value, limits[scope])
               for constraint, value, scope in zip(problem.constraints, changes, scopes[key])):
            selected[key] = choice
            for scope, value in zip(scopes[key], changes):
                totals[scope] = value
    # This is a warm-start heuristic, not an optimality certificate. Its bound
    # comes from the relaxation or solver, and its constraints are rechecked.
    return selected if is_feasible(problem, selected) else None


def repair_seed(problem, initial):
    """Try to reach feasibility without ever breaking a satisfied hard limit.

    Failure to repair is not evidence of infeasibility; the general solver
    remains responsible for cases requiring coordinated field exchanges.
    """
    if initial is None or any(type(c) not in (AccumulatedChangeConstraint, GroupedAccumulatedChangeConstraint)
                             or c.operator not in (operator.le, operator.ge) for c in problem.constraints):
        return None
    if is_feasible(problem, initial):
        return initial
    selected = initial.copy()
    totals, limits, scopes = _state(problem, selected)
    comparisons = {scope: problem.constraints[scope[0]].operator for scope in totals}
    norms = {scope: max(1, abs(value), abs(limits[scope])) for scope, value in totals.items()}
    def violation(scope, value):
        return max(0, value - limits[scope]) if comparisons[scope] == operator.le else max(0, limits[scope] - value)
    def gain(key, choice):
        previous = selected[key]
        result = 0.0
        for index, scope in enumerate(scopes[key]):
            before = violation(scope, totals[scope])
            after = violation(scope, totals[scope] + choice.coefficients[index] - previous.coefficients[index])
            if after > before:
                return 0.0
            result += (before - after) / norms[scope]
        return result
    moves = []
    for key, choices in problem.choices.items():
        for index, choice in enumerate(choices):
            progress = gain(key, choice)
            if progress > 0:
                loss = max(0, choice.cost - selected[key].cost)
                moves.append((loss / progress, -progress, key, index))
    moves.sort()
    unsatisfied = sum(violation(scope, value) > 0 for scope, value in totals.items())
    for _, _, key, index in moves:
        choice = problem.choices[key][index]
        if gain(key, choice) <= 0:
            continue
        previous = selected[key]
        for row, scope in enumerate(scopes[key]):
            before = violation(scope, totals[scope]) > 0
            totals[scope] += choice.coefficients[row] - previous.coefficients[row]
            unsatisfied += int(violation(scope, totals[scope]) > 0) - int(before)
        selected[key] = choice
        if unsatisfied == 0:
            return selected if is_feasible(problem, selected) else None
    return selected if is_feasible(problem, selected) else None
