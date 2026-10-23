import os

from shared_datamodel.simulation import OptimizationSettings


def settings_for_job(override: OptimizationSettings | None = None) -> OptimizationSettings:
    if override is not None:
        return override
    names = {
        "max_time_seconds": "TRANS4NUM_OPTIMIZER_MAX_TIME_SECONDS",
        "relative_gap": "TRANS4NUM_OPTIMIZER_RELATIVE_GAP",
        "workers": "TRANS4NUM_OPTIMIZER_WORKERS",
        "max_memory_mb": "TRANS4NUM_OPTIMIZER_MAX_MEMORY_MB",
        "use_linear_relaxation": "TRANS4NUM_OPTIMIZER_LINEAR_RELAXATION",
        "use_fast_path": "TRANS4NUM_OPTIMIZER_FAST_PATH",
        "debug": "TRANS4NUM_OPTIMIZER_DEBUG",
        "max_fractional_iterations": "TRANS4NUM_OPTIMIZER_MAX_FRACTIONAL_ITERATIONS",
    }
    return OptimizationSettings.model_validate({key: os.environ[name] for key, name in names.items() if name in os.environ})
