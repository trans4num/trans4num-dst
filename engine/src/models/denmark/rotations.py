from models.denmark.things import Crop, CropRotation, Soil
from models.denmark.transitions import Transition, get_transition

rotations = [
    CropRotation(
        name="Husmon Con cg",
        indices=[Crop(int(n)) for n in "10_10_5_3_8_7_6".split("_")],
    ),
    CropRotation(
        name="Dairy Con m+cg",
        indices=[Crop(int(n)) for n in "10_10_10_6_2_2_2".split("_")],
    ),
    CropRotation(
        name="Dairy con cg",
        indices=[Crop(int(n)) for n in "10_10_10_10_5_1_8".split("_")],
    ),
    CropRotation(
        name="Arable Con cg",
        indices=[Crop(int(n)) for n in "10_11_5_3_1_8_6".split("_")],
    ),
    CropRotation(
        name="Arable con gfs ",
        indices=[Crop(int(n)) for n in "6_9_1_6_6_9_3".split("_")],
    ),
    CropRotation(
        name="Arable con cg_pot",
        indices=[Crop(int(n)) for n in "10_11_5_1_6_5_1".split("_")],
    ),
    CropRotation(
        name="Dairy org m+cg",
        indices=[Crop(int(n)) for n in "10_10_10_6_2_2_6".split("_")],
    ),
    CropRotation(
        name="Dairy org cg",
        indices=[Crop(int(n)) for n in "10_10_10_10_6_1_6".split("_")],
    ),
    CropRotation(
        name="Arable Org cg",
        indices=[Crop(int(n)) for n in "11_11_6_3_8_1_6".split("_")],
    ),
    CropRotation(
        name="Dairy Org lowN",
        indices=[Crop(int(n)) for n in "11_11_11_6_5_4_6".split("_")],
    ),
    CropRotation(
        name="Arable Org LowN",
        indices=[Crop(int(n)) for n in "11_11_6_3_4_1_6".split("_")],
    ),
    CropRotation(
        name="Take Out",
        indices=[Crop(int(n)) for n in "12_12_12_12_12_12_12".split("_")],
    ),
]


def rotation_difference(indices_a: list[Crop], indices_b: list[Crop]) -> float:
    """
    This implementation is quite naive, but it works for now.
    Further it is quite inefficient.
    """

    rotation_length = len(indices_a)

    # Make sure we do not modify the original lists
    indices_a = list(indices_a)
    indices_b = list(indices_b)

    # First remove similar crops from both lists
    to_remove_from_a = []
    for crop_a in indices_a:
        if crop_a in indices_b:
            # Remove the first occurence of crop_a from each list
            to_remove_from_a.append(crop_a)
            indices_b.remove(crop_a)
    # We could not remove the crop from indices_a while iterating over it, so we collect them first
    # and then remove them
    for crop in to_remove_from_a:
        indices_a.remove(crop)

    # Now we take a greedy approach to find the best match
    score = 0
    for crop_a in indices_a:
        best_match = None
        best_score = float("inf")  # Start with the worst possible score
        for crop_b in indices_b:
            current_score = get_transition(
                crop_a,
                crop_b,
                Soil.CLAY,  # soil is not relevant for similarity
                0.0,  # retention is not relevant for similarity
                1.0,  # area is not relevant for similarity
                Transition.SIMILARITY,
            )
            if current_score is not None and current_score < best_score:
                best_match = crop_b
                best_score = current_score
                if best_score == 0:
                    break
        # If we found a match, we add the score and remove the crop from indices_b

        if best_match is not None:
            score += best_score
            indices_b.remove(best_match)
    return score / rotation_length


def encode_name(crop_rotation_indices: list[Crop]) -> str:
    crops = list(set(crop_rotation_indices))
    counts = [crop_rotation_indices.count(crop) for crop in crops]
    merged = zip(crops, counts)
    # To get stable sorting, we first sort by name, then by count
    result_list = sorted(merged, key=lambda x: x[0].name)  # Sort by crop name
    result_list = sorted(
        result_list, key=lambda x: x[1], reverse=True
    )  # Sort by crop count
    result_list = result_list[:2]  # Take the top 2 crops
    # We now sort by name again, to get fewer classes
    # This is not like the previous sort on name to get stable sorting, but rather to get a consistent order and hence fewer classes
    result_list = sorted(result_list, key=lambda x: x[0].name)  # Sort by crop name
    return "_".join([f"{r[0]}" for r in result_list])
