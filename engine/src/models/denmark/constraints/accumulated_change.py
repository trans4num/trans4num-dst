from typing import Callable

from ortools.sat.python.cp_model import CpModel, IntVar

from models.denmark.things import CropRotation, Field


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

    def add_term(
        self,
        choice: CropRotation,
        field: Field,
        model_var: IntVar,
    ):
        value = self.loader(choice, field)
        # UPSCALE TO INT
        value = int(value * self.scale)
        term = value * model_var
        self.terms.append(term)

    def constraint(self):
        # UPSCALE MAX TO INT TO MATCH THE UPSCALED TERMS
        max_change = int(self.max_change * self.scale)
        self.model.Add(self.operator(sum(self.terms), max_change))
