from models.denmark.things import Crop

# Source for data https://docs.google.com/spreadsheets/d/1QcYToT66zQGqLQW92ZuEZN_PKDlnn4XS/edit?gid=990130607#gid=990130607


def crop_to_harvested_nutrient(crop: Crop) -> float:
    if crop == Crop.CEREAL_SPRING or crop == Crop.CEREAL_SPRING_COVER:
        return 97
    if crop == Crop.CEREAL_WINTER or crop == Crop.CEREAL_WINTER_COVER:
        return 123
    if crop == Crop.GRASS_SEED:
        return 27
    if crop == Crop.GRASS:
        return 220
    if crop == Crop.GRASS_REDUCED:
        return 163
    if crop == Crop.LEGUMES:
        return 185
    if crop == Crop.MAIZE:
        return 218
    if crop == Crop.POTATO:
        return 174
    if crop == Crop.RAPE:
        return 114
    if crop == Crop.TAKEOUT:
        return 0
    return 0


def crop_to_fixed_nutrient(crop: Crop) -> float:
    if crop == Crop.CEREAL_SPRING or crop == Crop.CEREAL_SPRING_COVER:
        return 3
    if crop == Crop.CEREAL_WINTER or crop == Crop.CEREAL_WINTER_COVER:
        return 0
    if crop == Crop.GRASS_SEED:
        return 0
    if crop == Crop.GRASS:
        return 95
    if crop == Crop.GRASS_REDUCED:
        return 52
    if crop == Crop.LEGUMES:
        return 195
    if crop == Crop.MAIZE:
        return 0
    if crop == Crop.POTATO:
        return 0
    if crop == Crop.RAPE:
        return 0
    if crop == Crop.TAKEOUT:
        return 0
    return 0


def crop_to_rec_nutrient(crop: Crop) -> float:
    if crop == Crop.CEREAL_SPRING or crop == Crop.CEREAL_SPRING_COVER:
        return 134
    if crop == Crop.CEREAL_WINTER or crop == Crop.CEREAL_WINTER_COVER:
        return 168
    if crop == Crop.GRASS_SEED:
        return 183
    if crop == Crop.GRASS:
        return 244
    if crop == Crop.GRASS_REDUCED:
        return 127
    if crop == Crop.LEGUMES:
        return 0
    if crop == Crop.MAIZE:
        return 148
    if crop == Crop.POTATO:
        return 192
    if crop == Crop.RAPE:
        return 188
    if crop == Crop.TAKEOUT:
        return 0
    return 0
