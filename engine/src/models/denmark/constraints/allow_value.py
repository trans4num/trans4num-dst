from typing import Callable

from models.denmark.load import Field


class AllowValueConstraint:
    def __init__(self, max_value, loader: Callable[[Field], float]):
        self.max_value = max_value
        self.loader = loader

    def allow(self, field: Field) -> bool:
        return self.loader(field) <= self.max_value
