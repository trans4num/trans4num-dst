"""Improve a feasible seed without relaxing any supported hard constraint."""
from models.denmark.constraints.accumulated_change import AccumulatedChangeConstraint
from models.denmark.constraints.grouped_accumulated_change import GroupedAccumulatedChangeConstraint
from models.denmark.prepare import is_feasible


def improve_seed(problem, initial):
    if initial is None or not is_feasible(problem, initial):
        return None
    if any(type(c) not in (AccumulatedChangeConstraint, GroupedAccumulatedChangeConstraint) for c in problem.constraints):
        return None
    selected = initial.copy()
    totals, limits, scopes = {}, {}, {}
    for key, choice in selected.items():
        field_scopes = []
        for index, constraint in enumerate(problem.constraints):
            if type(constraint) is GroupedAccumulatedChangeConstraint:
                field = problem.fields[key]
                scope = (index, constraint.grouper(field))
                limit = int(constraint.get_max_change(field) * constraint.scale)
            else:
                scope = (index, None)
                limit = int(constraint.max_change * constraint.scale)
            field_scopes.append(scope)
            limits.setdefault(scope, limit)
            totals[scope] = totals.get(scope, 0) + choice.coefficients[index]
        scopes[key] = field_scopes

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
