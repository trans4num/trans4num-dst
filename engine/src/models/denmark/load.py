import pandas as pd
from models.denmark.rotations import encode_name, rotations
from models.denmark.things import (
    Col,
    Crop,
    CropRotation,
    Field,
    Soil,
    SpatialIndicator,
)
from store import IStore

crop_years = [17, 18, 19, 20, 21, 22, 23]

crop_cols = [
    Col(
        name=f"crop_{year}", name_in_input=f"AgCropNr{year}", dtype=str(pd.Int16Dtype())
    )
    for year in crop_years
]

meta_cols = [
    Col(name="org_id", name_in_input="CVR", dtype=str(pd.Int32Dtype())),
    Col(name="field_id", name_in_input="IMK_ID", dtype=str(pd.Int32Dtype())),
    Col(name="soil_id", name_in_input="Soil_ID", dtype=str(pd.Int16Dtype())),
    Col(
        name="retention",
        name_in_input="retention",
        dtype=str(pd.Float64Dtype()),
    ),
    Col(
        name="area",
        name_in_input="IMK_areal",
        dtype=str(pd.Float64Dtype()),
    ),
    Col(
        name="dist_to_biora",
        name_in_input="BiogasNetM",
        dtype=str(pd.Float64Dtype()),
    ),
    Col(
        name="nature_value_mean",
        name_in_input="PctHnvOve5",
        dtype=str(pd.Float64Dtype()),
    ),
]

cols = crop_cols + meta_cols


def load_fields(store: IStore, region_id) -> dict[str, Field]:
    df = store.read_fields_csv(region_id, cols)
    df = df.rename(columns={c.name_in_input: c.name for c in cols})

    print("Replacing 0 with 13 for every fields crop. We do not have a crop 0")
    for year in crop_years:
        df.loc[df[f"crop_{year}"] == 0, f"crop_{year}"] = 13

    print("Removing all fields with crop 13")
    size_before = len(df)
    for year in crop_years:
        df = df[df[f"crop_{year}"] != 13]
    size_after = len(df)
    print(f"Removed {size_before - size_after} fields with crop 13")

    print(f"Replacing soil for {len(df[df['soil_id'] == 11])} hummus fields with clay")

    df.loc[df["soil_id"] == 11, "soil_id"] = (
        20  # TODO: For now we fake HUMUS and says that it is clay
    )

    df["soil_id"] //= 10  # Convert the soil ids into soil

    df.loc[df["nature_value_mean"] > 100, "nature_value_mean"] = (
        100  # Sometimes the percentage gets unrealistically large.
    )

    # Convert this to fields which are nicer to work with
    fields = {}
    for ds_idx, ds_entry in df.iterrows():
        rotation_crops = [Crop(ds_entry[f"crop_{year}"]) for year in crop_years]
        actual_rotation = CropRotation(
            name=encode_name(rotation_crops),
            indices=rotation_crops,
        )

        field_id = f"f-{ds_entry['field_id']}"
        field = Field(
            field_id=field_id,
            spatial_indicator=SpatialIndicator(
                soil=Soil(ds_entry["soil_id"]),
                retention=ds_entry["retention"],
                area=ds_entry["area"],
                nature_value_mean=ds_entry["nature_value_mean"],
                dist_to_biora=ds_entry["dist_to_biora"],
                org_id=f"o-{ds_entry['org_id']}",
            ),
            rotation=actual_rotation,
            choices=rotations,
        )
        fields[field_id] = field

    return fields
