"""Symmetric coefficient quantization and direction-aware integer limits."""
import math
import operator


def scaled_value(value, scale):
    scaled = float(value) * scale
    if not math.isfinite(scaled):
        raise ValueError("Constraint coefficients and limits must be finite")
    nearest = round(scaled)
    # Do not turn a value such as 227.00000000000003 into an extra unit.
    if abs(scaled - nearest) <= max(1e-9, 4 * math.ulp(scaled)):
        return nearest
    return scaled


def coefficient(value, scale):
    # Unlike truncation, nearest rounding is symmetric for opposite deltas.
    return round(scaled_value(value, scale))


def limit(value, scale, comparison):
    scaled = scaled_value(value, scale)
    if comparison == operator.le:
        return math.floor(scaled)
    if comparison == operator.ge:
        return math.ceil(scaled)
    return round(scaled)
