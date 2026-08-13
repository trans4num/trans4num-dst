from dataclasses import dataclass
from enum import Enum


class Soil(Enum):
    SAND = 1
    CLAY = 2


class Crop(Enum):
    POTATO = 1
    MAIZE = 2
    RAPE = 3
    LEGUMES = 4
    CEREAL_SPRING = 5
    CEREAL_SPRING_COVER = 6
    CEREAL_WINTER = 7
    CEREAL_WINTER_COVER = 8
    GRASS_SEED = 9
    GRASS = 10
    GRASS_REDUCED = 11
    TAKEOUT = 12
    OTHER = 13

    def __str__(self) -> str:
        if self.value == Crop.POTATO.value:
            return "potato"
        if self.value == Crop.MAIZE.value:
            return "maize"
        if self.value == Crop.RAPE.value:
            return "rape seed"
        if self.value == Crop.LEGUMES.value:
            return "legumes"
        if self.value == Crop.CEREAL_SPRING.value:
            return "cereal spring"
        if self.value == Crop.CEREAL_SPRING_COVER.value:
            return "cereal spring with cover crop"
        if self.value == Crop.CEREAL_WINTER.value:
            return "cereal winter"
        if self.value == Crop.CEREAL_WINTER_COVER.value:
            return "cereal winter with cover crop"
        if self.value == Crop.GRASS_SEED.value:
            return "grass for seed"
        if self.value == Crop.GRASS.value:
            return "grass/clover fertilized to norm"
        if self.value == Crop.GRASS_REDUCED.value:
            return "grass/clover reduced fertilization"
        if self.value == Crop.TAKEOUT.value:
            return "take out"
        if self.value == Crop.OTHER.value:
            return "other"
        raise Exception(f"This crop does not exist: {self.name}")


@dataclass(frozen=True)
class CropRotation:
    name: str
    indices: list[Crop]


@dataclass(frozen=True)
class SpatialIndicator:
    soil: Soil
    retention: float
    area: float
    nature_value_mean: float
    dist_to_biora: float
    org_id: str


@dataclass(frozen=True)
class Field:
    field_id: str
    rotation: CropRotation
    spatial_indicator: SpatialIndicator
    choices: list[CropRotation]


@dataclass
class Col:
    name: str
    dtype: str
    name_in_input: str
