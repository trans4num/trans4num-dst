from typing import Callable

from ortools.sat.python.cp_model import CpModel, IntVar, LinearExpr

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
        self.variables = []
        self.coefficients = []
        self.fixed = 0
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
        if model_var is True:
            self.fixed += value
        else:
            self.variables.append(model_var)
            self.coefficients.append(value)

    def constraint(self):
        # UPSCALE MAX TO INT TO MATCH THE UPSCALED TERMS
        max_change = self.limit()
        if self.variables or not self.operator(self.fixed, max_change):
            expression = LinearExpr.WeightedSum(self.variables, self.coefficients) + self.fixed
            self.model.Add(self.operator(expression, max_change))
        # The row now lives in the model proto. Keeping these Python arrays
        # alive throughout search duplicates the matrix for no benefit.
        self.variables.clear()
        self.coefficients.clear()
        self.fixed = 0
