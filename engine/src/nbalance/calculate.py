from dataclasses import dataclass, fields

from models.denmark.things import Crop, Field
from nbalance.lookup import (
    crop_to_fixed_nutrient,
    crop_to_harvested_nutrient,
)

# Please update lookup numbers with the excel sheet too (first tab).


@dataclass
class NBalance:
    in_manure: float
    in_excreted: float
    in_fertilizer: float
    in_other: float
    fixated: float
    harvested: float
    out_losses: float
    in_total: float
    out_total: float
    balance: float

    @classmethod
    def from_crop(cls, crop: Crop) -> "NBalance":
        in_manure = 106
        in_excreted = 76
        in_fertilizer = 57
        in_other = 3
        fixated = crop_to_fixed_nutrient(crop)
        harvested = crop_to_harvested_nutrient(crop)
        out_losses = in_manure * 0.1
        in_total = in_manure + in_fertilizer + in_other + fixated
        out_total = harvested + out_losses
        balance = in_total - out_total

        return cls(
            in_manure=in_manure,
            in_excreted=in_excreted,
            in_fertilizer=in_fertilizer,
            in_other=in_other,
            fixated=fixated,
            harvested=harvested,
            out_losses=out_losses,
            in_total=in_total,
            out_total=out_total,
            balance=balance,
        )

    @classmethod
    def average(cls, balances: list["NBalance"]) -> "NBalance":
        if not balances:
            raise ValueError("Cannot average an empty list of NBalance instances.")

        return cls.sum(balances).scaled(1 / len(balances))

    @classmethod
    def sum(cls, balances: list["NBalance"]) -> "NBalance":
        if not balances:
            raise ValueError("Cannot sum an empty list of NBalance instances.")

        values = {
            field.name: sum(getattr(balance, field.name) for balance in balances)
            for field in fields(cls)
        }
        return cls(**values)

    def scaled(self, factor: float) -> "NBalance":
        values = {
            field.name: getattr(self, field.name) * factor for field in fields(self)
        }
        return NBalance(**values)


def n_balance_for_field(field: Field) -> NBalance:
    # We calculate the fields N-balance as the average N-balance over the rotation
    entries = []
    for crop in field.rotation.indices:
        entries.append(NBalance.from_crop(crop))
    return NBalance.average(entries).scaled(field.spatial_indicator.area)


# We assume that N in and N out can be measured on a field basis.
