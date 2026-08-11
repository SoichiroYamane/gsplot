"""Pure numerical validation used by canonical plotting functions."""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .errors import DataError


def as_float_array(
    values: ArrayLike,
    name: str,
    *,
    ndim: int | None = None,
    allow_empty: bool = False,
) -> NDArray[np.float64]:
    """Copy values into a finite floating array with a validated shape."""

    try:
        array = np.array(values, dtype=float, copy=True)
    except (TypeError, ValueError) as exc:
        raise DataError(f"{name} must contain numeric values") from exc

    if ndim is not None and array.ndim != ndim:
        raise DataError(f"{name} must be {ndim}-dimensional")
    if not allow_empty and array.size == 0:
        raise DataError(f"{name} must not be empty")
    if not np.all(np.isfinite(array)):
        raise DataError(f"{name} must contain only finite values")
    return array


def validate_xy(
    x: ArrayLike,
    y: ArrayLike,
    *,
    colored: bool = False,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Validate one-dimensional x/y data for ordinary or colored plots."""

    x_array = as_float_array(x, "x", ndim=1)
    y_array = as_float_array(y, "y", ndim=1)
    if x_array.shape != y_array.shape:
        raise DataError("x and y must have the same one-dimensional shape")
    if colored and x_array.size < 2:
        raise DataError("colored plots require at least two points")
    return x_array, y_array


def validate_color_values(
    values: ArrayLike, *, name: str = "values"
) -> NDArray[np.float64]:
    """Validate finite one-dimensional values used for color mapping."""

    return as_float_array(values, name, ndim=1)


def segment_points(
    x: ArrayLike,
    y: ArrayLike,
) -> NDArray[np.float64]:
    """Return adjacent x/y points as an ``(n - 1, 2, 2)`` segment array."""

    x_array, y_array = validate_xy(x, y, colored=True)
    points = np.column_stack((x_array, y_array))
    return np.stack((points[:-1], points[1:]), axis=1)


__all__ = [
    "as_float_array",
    "validate_xy",
    "validate_color_values",
    "segment_points",
]
