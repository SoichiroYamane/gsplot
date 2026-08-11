"""Unit tests for the side-effect-free canonical foundation."""

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from gsplot._core import (
    MISSING,
    AxisSpec,
    ConfigError,
    DataError,
    as_float_array,
    ensure_pair,
    resolve_option,
    validate_xy,
)


def test_immutable_value_and_precedence_helpers() -> None:
    """Value objects are immutable and precedence is explicit."""

    spec = AxisSpec(xlabel="time")
    with pytest.raises(FrozenInstanceError):
        spec.xlabel = "other"  # type: ignore[misc]

    assert resolve_option(MISSING, "configured", "default") == "configured"
    assert resolve_option("explicit", "configured", "default") == "explicit"
    assert resolve_option(MISSING, MISSING, "default") == "default"
    assert resolve_option(None, "configured", "default") is None


def test_numeric_validation_copies_input_and_rejects_invalid_shapes() -> None:
    """Numerical helpers enforce finite one-dimensional data contracts."""

    source = np.array([1.0, 2.0])
    copied = as_float_array(source, "source", ndim=1)
    copied[0] = 99
    assert source[0] == 1

    x, y = validate_xy([0, 1], [2, 3])
    assert x.tolist() == [0.0, 1.0]
    assert y.tolist() == [2.0, 3.0]

    with pytest.raises(DataError, match="same"):
        validate_xy([0, 1], [2])
    with pytest.raises(DataError, match="finite"):
        validate_xy([0, np.inf], [2, 3])
    with pytest.raises(DataError, match="at least two"):
        validate_xy([0], [1], colored=True)


def test_validation_errors_are_typed() -> None:
    """Invalid layout and configuration values use the public error hierarchy."""

    with pytest.raises(ConfigError):
        ensure_pair([1], "size", error=ConfigError)
    with pytest.raises(ConfigError):
        ensure_pair([1, float("inf")], "size", error=ConfigError)
