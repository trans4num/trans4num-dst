from shared_datamodel.simulation import (
    Model,
    ModelConstraint,
    SimulationGoal,
    SimulationGoalType,
)

max_econ = SimulationGoal(
    name="Maximize Economy",
    description="Maximize the total economy of the region",
    type=SimulationGoalType.MAX_ECONOMY,
    configuration=[
        ModelConstraint(
            name="N-Load Change", enabled=True, value=0, range=(-100, 100), unit="%"
        ),
    ],
)

max_tradeoff = SimulationGoal(
    name="Max Economy & Min N-Load",
    description="Maximize the economy per N-Load",
    type=SimulationGoalType.MAX_ECON_PER_NLOAD,
    configuration=[],
)

min_nload = SimulationGoal(
    name="Minimize N-Load",
    description="Minimize the total N-Load of the region",
    type=SimulationGoalType.MIN_NLOAD,
    configuration=[
        ModelConstraint(
            name="Economy Change", enabled=True, value=0, range=(-100, 100), unit="%"
        ),
    ],
)

constraints = [
    ModelConstraint(
        name="Distance to Biogas",
        enabled=False,
        value=25,
        range=(0, 100),
        unit="km",
    ),
    ModelConstraint(
        name="Single Farmer Impact",
        enabled=False,
        value=50,
        range=(0, 100),
        unit="%",
    ),
    ModelConstraint(
        name="Nature Value",
        enabled=False,
        value=50,
        range=(0, 100),
        unit="%",
    ),
    ModelConstraint(
        name="Area Change",
        enabled=False,
        value=50,
        range=(0, 100),
        unit="%",
    ),
    ModelConstraint(
        name="Fields Change",
        enabled=False,
        value=50,
        range=(0, 100),
        unit="%",
    ),
    ModelConstraint(
        name="Percentage of farm type change",
        enabled=False,
        value=20,
        range=(0, 100),
        unit="%",
    ),
]


def get_models(region) -> list[Model]:
    """Get a list of all available models."""
    models = [
        Model(goal=max_econ, constraints=constraints),
        Model(goal=max_tradeoff, constraints=constraints),
        Model(goal=min_nload, constraints=constraints),
    ]
    return models


def get_model(target: SimulationGoalType) -> Model:
    """Get a list of all available models."""
    if target == SimulationGoalType.MAX_ECONOMY:
        return Model(goal=max_econ, constraints=constraints)
    elif target == SimulationGoalType.MIN_NLOAD:
        return Model(goal=min_nload, constraints=constraints)
    elif target == SimulationGoalType.MAX_ECON_PER_NLOAD:
        return Model(goal=max_tradeoff, constraints=constraints)
    else:
        raise ValueError(f"Unknown target: {target}")
