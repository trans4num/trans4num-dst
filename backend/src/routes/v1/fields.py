from enum import Enum
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from geojson_pydantic import FeatureCollection
from shared_datamodel.schema import BaseSchema
from shared_datamodel.simulation import Variable

from src.store import IStore
from src.util.named_fields import get_named_fields


class VariableType(Enum):
    CONTINOUS = "continuous"
    CATEGORICAL = "categorical"


class FieldsResponse(BaseSchema):
    fields: list[str]


class VariableValuesResponse(BaseSchema):
    type: VariableType
    unit: str
    values: dict[str, str | int | float]


class VariablesResponse(BaseSchema):
    variables: list[Variable]


def extract_names(fields) -> list[str]:
    return [f.id for f in fields.features]


def variable_to_variable(variable: Variable) -> str:
    if variable == Variable.CROP:
        return "crop"
    if variable == Variable.ECONOMY:
        return "economy"
    if variable == Variable.NLOAD:
        return "leaching"
    if variable == Variable.NATURE:
        return "nature_value"


def variable_to_unit(variable: Variable) -> str:
    if variable == Variable.CROP:
        return "kg/ha"
    if variable == Variable.ECONOMY:
        return "kr/ha"
    if variable == Variable.NLOAD:
        return "kg/ha"
    if variable == Variable.NATURE:
        return ""
    raise ValueError(f"Unknown variable: {variable}")


def variable_to_type(variable: Variable) -> VariableType:
    if variable == Variable.CROP:
        return VariableType.CATEGORICAL
    if variable == Variable.ECONOMY:
        return VariableType.CONTINOUS
    if variable == Variable.NLOAD:
        return VariableType.CONTINOUS
    if variable == Variable.NATURE:
        return VariableType.CONTINOUS
    raise ValueError(f"Unknown variable: {variable}")


def get_router(store: IStore) -> APIRouter:
    router = APIRouter(prefix="/fields", tags=["fields"])

    @router.get("")
    async def get_fields(
        region: UUID = Query(
            description="The id of the region for which to fetch geometries."
        ),
    ) -> FieldsResponse:
        """Get all fields for the given region"""
        geometries = get_named_fields(region, store)
        if geometries is None:
            raise HTTPException(status_code=404, detail="No fields found for region")
        return FieldsResponse(fields=extract_names(geometries))

    @router.get("/geometries")
    async def get_geometries(
        region: UUID = Query(
            description="The id of the region for which to fetch geometries."
        ),
        limit: int | None = None,
    ) -> FeatureCollection:
        """Get geometry of all fields for the given region"""
        geometries = get_named_fields(region, store)
        if geometries is None:
            raise HTTPException(
                status_code=404, detail="No geometries found for region"
            )
        if limit is not None:
            return geometries.model_copy(
                update={"features": geometries.features[:limit]}
            )
        return geometries

    @router.get("/variables")
    async def get_variables(
        simulation: UUID = Query(
            description="The id of the simulation for which to fetch variables."
        ),
    ) -> VariablesResponse:
        """Get all variables for the given simulation"""

        # Make a list of all possible variables
        variables = [Variable[v.name] for v in Variable]
        return VariablesResponse(variables=variables)

    @router.get("/variables/{variable}")
    async def get_values(
        variable: Variable,
        simulation: UUID = Query(
            description="The id of the simulation for which to fetch values."
        ),
    ) -> VariableValuesResponse:
        """Get parameter values of all fields for the given simulation"""

        # This is a bit ugly. Only one path should exist
        data = store.get_variables(simulation)

        if data is None:
            raise HTTPException(
                status_code=404, detail="No region found for the simulation"
            )

        result: dict[str, str | int | float] = {
            str(n["field_id"]): n[variable_to_variable(variable)] for n in data
        }

        return VariableValuesResponse(
            values=result,
            unit=variable_to_unit(variable),
            type=variable_to_type(variable),
        )

    return router
