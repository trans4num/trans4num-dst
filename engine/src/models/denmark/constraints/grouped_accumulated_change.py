from typing import Callable

from ortools.sat.python.cp_model import CpModel, IntVar

from models.denmark.constraints.accumulated_change import (
    AccumulatedChangeConstraint,
)
from models.denmark.things import CropRotation, Field


class GroupedAccumulatedChangeConstraint:
    def __init__(
        self,
        model: CpModel,
        scale: int,
        operator: Callable[[int, int], bool],
        loader: Callable[[CropRotation, Field], float],
        grouper: Callable[[Field], str],
        get_max_change: Callable[[Field], float],
    ):
        self.group_constraints: dict[str, AccumulatedChangeConstraint] = {}
        self.model = model
        self.scale = scale
        self.operator = operator
        self.loader = loader
        self.grouper = grouper
        self.get_max_change = get_max_change

    def add_term(
        self,
        choice: CropRotation,
        field: Field,
        model_var: IntVar,
    ):
        group_name = self.grouper(field)
        if group_name not in self.group_constraints:
            self.group_constraints[group_name] = AccumulatedChangeConstraint(
                self.model,
                self.scale,
                self.operator,
                self.loader,
                max_change=self.get_max_change(field),
            )
        self.group_constraints[group_name].add_term(choice, field, model_var)

    def constraint(self):
        # print(list(self.group_constraints.keys())[:5])

        # inspect = ["o-14655107", "o-11812082", "o-26672104", "o-30303849", "o-43003739"]
        # for nam in inspect:
        #     if nam in self.group_constraints:
        #         print("####")
        #         print(nam)
        #         print("----")
        #         print(f"Has {len(self.group_constraints[nam].terms)} terms")
        #         print(f"Max change: {self.group_constraints[nam].max_change}")
        #         print("")
        #     else:
        #         print(f"No constraint for {nam}")

        # import sys

        # sys.exit()

        for constraint in self.group_constraints.values():
            constraint.constraint()
