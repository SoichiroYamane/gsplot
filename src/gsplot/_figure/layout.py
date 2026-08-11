"""Explicit figure and axes ownership for the canonical ``subplots`` API."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal, cast

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from numpy.typing import NDArray

from .._config.model import Config
from .._core.errors import ConfigError, LayoutError
from .._core.types import MosaicSpec
from .._core.validation import ensure_bool, ensure_pair
from .backend import use_backend

Unit = Literal["mm", "cm", "in", "pt"]
_UNIT_TO_INCH = {"in": 1.0, "mm": 1 / 25.4, "cm": 1 / 2.54, "pt": 1 / 72.0}


def _validate_count(value: Any, name: str) -> int:
    """Validate a positive subplot count."""

    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise LayoutError(f"{name} must be a positive integer")
    return value


def _validate_mosaic(mosaic: MosaicSpec | None) -> MosaicSpec | None:
    """Validate the basic shape of a Matplotlib mosaic before mutation."""

    if mosaic is None:
        return None
    if isinstance(mosaic, str):
        if not mosaic.strip():
            raise LayoutError("mosaic must not be empty")
        return mosaic
    if isinstance(mosaic, (str, bytes)) or not isinstance(mosaic, Sequence):
        raise LayoutError("mosaic must be a string or a sequence of rows")
    rows = tuple(mosaic)
    if not rows or any(not isinstance(row, Sequence) or not row for row in rows):
        raise LayoutError("mosaic must contain non-empty rows")
    if any(isinstance(row, (str, bytes)) for row in rows):
        raise LayoutError("mosaic rows must be sequences of labels")
    return mosaic


def _size_in_inches(figsize: Any, unit: Unit | None) -> tuple[float, float] | None:
    """Validate and convert an optional figure size to inches."""

    if figsize is None:
        return None
    if unit is None:
        unit = "in"
    if unit not in _UNIT_TO_INCH:
        raise LayoutError(f"unit must be one of: {', '.join(_UNIT_TO_INCH)}")
    width, height = ensure_pair(figsize, "figsize", positive=True)
    factor = _UNIT_TO_INCH[unit]
    return width * factor, height * factor


def _resolve_layout(
    *,
    nrows: int,
    ncols: int,
    mosaic: MosaicSpec | None,
    figsize: tuple[float, float] | None,
    unit: Unit | None,
    squeeze: bool | None,
    tight_layout: bool | None,
    constrained_layout: bool | None,
    config: Config | None,
) -> tuple[int, int, MosaicSpec | None, tuple[float, float] | None, bool, bool, bool]:
    """Validate all layout arguments before touching an existing figure."""

    selected_config = Config() if config is None else config
    if not isinstance(selected_config, Config):
        raise ConfigError("config must be a gsplot Config")
    rows = _validate_count(nrows, "nrows")
    cols = _validate_count(ncols, "ncols")
    selected_mosaic = _validate_mosaic(mosaic)
    if selected_mosaic is not None and (rows != 1 or cols != 1):
        raise LayoutError("mosaic cannot be combined with non-default nrows/ncols")

    selected_unit: Unit = cast(
        Unit,
        unit if unit is not None else selected_config.figure.unit,
    )
    if selected_unit not in _UNIT_TO_INCH:
        raise LayoutError(f"unit must be one of: {', '.join(_UNIT_TO_INCH)}")
    selected_size = selected_config.figure.figsize if figsize is None else figsize
    size_in_inches = _size_in_inches(selected_size, selected_unit)
    selected_squeeze = ensure_bool(
        selected_config.figure.squeeze if squeeze is None else squeeze,
        "squeeze",
        error=LayoutError,
    )
    selected_tight = ensure_bool(
        selected_config.figure.tight_layout if tight_layout is None else tight_layout,
        "tight_layout",
        error=LayoutError,
    )
    selected_constrained = ensure_bool(
        (
            selected_config.figure.constrained_layout
            if constrained_layout is None
            else constrained_layout
        ),
        "constrained_layout",
        error=LayoutError,
    )
    if selected_tight and selected_constrained:
        raise LayoutError("tight_layout and constrained_layout cannot both be true")
    return (
        rows,
        cols,
        selected_mosaic,
        size_in_inches,
        selected_squeeze,
        selected_tight,
        selected_constrained,
    )


def subplots(
    *,
    nrows: int = 1,
    ncols: int = 1,
    mosaic: MosaicSpec | None = None,
    figsize: tuple[float, float] | None = None,
    unit: Unit | None = None,
    squeeze: bool | None = None,
    fig: Figure | None = None,
    clear: bool = False,
    tight_layout: bool | None = None,
    constrained_layout: bool | None = None,
    config: Config | None = None,
) -> tuple[Figure, Axes | NDArray[Any] | dict[str, Axes]]:
    """Create or reuse a figure while returning all owned axes explicitly.

    Parameters
    ----------
    nrows, ncols
        Positive subplot dimensions when ``mosaic`` is not supplied.
    mosaic
        A Matplotlib-compatible string or row sequence of labels.
    figsize, unit
        Optional positive figure dimensions and their unit. Units default to
        inches and are converted before the figure is created.
    squeeze
        Whether ordinary subplot arrays use Matplotlib's squeeze behavior.
    fig
        An existing figure to reuse. It is never resized.
    clear
        Clear an existing figure only after all arguments have been validated.
    tight_layout, constrained_layout
        Mutually exclusive layout flags.
    config
        Immutable canonical configuration used only for omitted values.

    Returns
    -------
    tuple
        The explicitly owned ``Figure`` and either an ``Axes``, NumPy axes
        array, or mosaic mapping following Matplotlib's return conventions.

    Raises
    ------
    LayoutError
        If layout arguments are invalid or the existing target is not a
        Matplotlib figure.
    """

    (
        rows,
        cols,
        selected_mosaic,
        size_in_inches,
        selected_squeeze,
        selected_tight,
        selected_constrained,
    ) = _resolve_layout(
        nrows=nrows,
        ncols=ncols,
        mosaic=mosaic,
        figsize=figsize,
        unit=unit,
        squeeze=squeeze,
        tight_layout=tight_layout,
        constrained_layout=constrained_layout,
        config=config,
    )

    if fig is not None and not isinstance(fig, Figure):
        raise LayoutError("fig must be a Matplotlib Figure")
    target = fig
    if target is None:
        target = plt.figure(
            figsize=size_in_inches, constrained_layout=selected_constrained
        )
    elif clear:
        target.clear()

    if selected_constrained:
        cast(Any, target).set_constrained_layout(True)
    if selected_mosaic is not None:
        axes: Axes | NDArray[Any] | dict[str, Axes] = cast(
            dict[str, Axes],
            target.subplot_mosaic(cast(Any, selected_mosaic)),
        )
    else:
        axes = target.subplots(rows, cols, squeeze=selected_squeeze)
    if selected_tight:
        cast(Any, target).set_tight_layout(True)
    return target, axes


__all__ = ["subplots", "use_backend"]
