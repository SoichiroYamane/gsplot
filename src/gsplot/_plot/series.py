"""Frozen publication-series identities for concise plotting operations."""

from __future__ import annotations

from typing import Final

from matplotlib.typing import LineStyleType, MarkerType

from .._core.errors import PlotError
from .._core.types import ColorSpec

SeriesColor = tuple[float, float, float, float]

SERIES_COLORS: Final[tuple[SeriesColor, ...]] = (
    (0.267004, 0.004874, 0.329415, 1.0),
    (0.281412, 0.155834, 0.469201, 1.0),
    (0.244972, 0.287675, 0.537260, 1.0),
    (0.190631, 0.407061, 0.556089, 1.0),
    (0.147607, 0.511733, 0.557049, 1.0),
    (0.119699, 0.618490, 0.536347, 1.0),
    (0.208030, 0.718701, 0.472873, 1.0),
    (0.430983, 0.808473, 0.346476, 1.0),
    (0.709898, 0.868751, 0.169257, 1.0),
    (0.993248, 0.906157, 0.143936, 1.0),
)

SERIES_LINESTYLES: Final[tuple[LineStyleType, ...]] = (
    "-",
    "--",
    "-.",
    ":",
    (0, (1, 1, 3, 1)),
    (0, (1, 1, 5, 2)),
    (0, (5, 2, 1, 2)),
    (0, (5, 2, 1, 2, 1, 2)),
    (0, (3, 1, 1, 2)),
    (0, (8, 2, 2, 2)),
)

SERIES_MARKERS: Final[tuple[MarkerType, ...]] = (
    "o",
    "s",
    "^",
    "D",
    "v",
    "P",
    "X",
    "<",
    ">",
    "*",
)


def series_index(value: object) -> int:
    """Return an exact publication-series index from zero through nine."""

    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
        raise PlotError(
            "series must be an integer from 0 through 9; "
            "provide explicit style values for other identities"
        )
    return value


def line_series(value: object) -> tuple[ColorSpec, LineStyleType]:
    """Return the deterministic color and line style for one series index."""

    index = series_index(value)
    return SERIES_COLORS[index], SERIES_LINESTYLES[index]


def scatter_series(value: object) -> tuple[ColorSpec, MarkerType]:
    """Return the deterministic color and marker for one series index."""

    index = series_index(value)
    return SERIES_COLORS[index], SERIES_MARKERS[index]


__all__ = [
    "SERIES_COLORS",
    "SERIES_LINESTYLES",
    "SERIES_MARKERS",
    "line_series",
    "scatter_series",
    "series_index",
]
