from typing import Callable

from ortools.sat.python.cp_model import CpModel, IntVar

from models.denmark.things import CropRotation, Field
from . import scaling


class AccumulatedChangeConstraint:
    def __init__(
        self,
        model: CpModel,
        scale: int,
        operator: Callable[[int, int], bool],
        loader: Callable[[CropRotation, Field], float],
        max_change: float,
    ):
        self.terms = []
        self.model = model
        self.scale = scale
        self.operator = operator
        self.loader = loader
        self.max_change = max_change
        self.freeze_field = None

    def add_term(
        self,
        choice: CropRotation,
        field: Field,
        model_var: IntVar,
    ):
        self.add_coefficient(field, self.coefficient(choice, field), model_var)

    def coefficient(self, choice: CropRotation, field: Field) -> int:
        return scaling.coefficient(self.loader(choice, field), self.scale)

    def limit(self, field=None) -> int:
        return scaling.limit(self.max_change, self.scale, self.operator)

    def add_coefficient(self, field: Field, value: int, model_var: IntVar):
        if value == 0:
            return
        term = value * model_var
        self.terms.append(term)

    def constraint(self):
        # UPSCALE MAX TO INT TO MATCH THE UPSCALED TERMS
        max_change = self.limit()
        if not self.terms and self.operator(0, max_change):
            return
        self.model.Add(self.operator(sum(self.terms), max_change))
