"""Pure colormap sampling for canonical plotting operations."""

from __future__ import annotations

from collections.abc import Callable
from copy import copy
from typing import Any

import matplotlib as mpl
import numpy as np
from matplotlib.colors import Colormap, Normalize
from numpy.typing import ArrayLike, NDArray

from .._config.model import Config
from .._core.errors import DataError, OptionError, PlotError
from .._core.numerics import validate_color_values
from .._core.types import NormalizeSpec


def _validate_norm(norm: NormalizeSpec | None) -> Any:
    """Validate and normalize the supported normalizer forms."""

    if norm is None:
        return norm
    if isinstance(norm, Normalize):
        lower = norm.vmin
        upper = norm.vmax
        if (lower is None) != (upper is None):
            raise PlotError("norm must define both vmin and vmax or neither")
        if lower is not None and upper is not None:
            if not np.isfinite(lower) or not np.isfinite(upper) or lower >= upper:
                raise PlotError("norm bounds must be finite and increasing")
        return copy(norm)
    if callable(norm):
        return norm
    if isinstance(norm, (str, bytes)):
        raise PlotError("norm must be a normalizer or a finite (vmin, vmax) pair")
    try:
        bounds = tuple(norm)
    except TypeError as exc:
        raise PlotError(
            "norm must be a normalizer or a finite (vmin, vmax) pair"
        ) from exc
    if len(bounds) != 2:
        raise PlotError("norm must be a normalizer or a finite (vmin, vmax) pair")
    try:
        vmin, vmax = (float(bounds[0]), float(bounds[1]))
    except (TypeError, ValueError) as exc:
        raise PlotError("norm bounds must be finite") from exc
    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmin >= vmax:
        raise PlotError("norm bounds must be finite and increasing")
    return Normalize(vmin=vmin, vmax=vmax, clip=True)


def _normalized(values: NDArray[np.float64], norm: Any) -> NDArray[np.float64]:
    """Normalize finite values with a deterministic constant-data policy."""

    lower = float(np.min(values))
    upper = float(np.max(values))
    if norm is None:
        if lower == upper:
            return np.full(values.shape, 0.5, dtype=float)
        normalizer: Callable[..., Any] = Normalize(vmin=lower, vmax=upper, clip=True)
    else:
        normalizer = norm
        bound_min = getattr(normalizer, "vmin", None)
        bound_max = getattr(normalizer, "vmax", None)
        if lower == upper and (
            bound_min is None or bound_max is None or bound_min == bound_max
        ):
            return np.full(values.shape, 0.5, dtype=float)
    try:
        result = np.asarray(normalizer(values, clip=True), dtype=float)
    except (TypeError, ValueError) as exc:
        raise PlotError("norm must be callable with a clip argument") from exc
    if result.shape != values.shape or not np.all(np.isfinite(result)):
        raise PlotError("norm must return finite values with the input shape")
    return np.clip(result, 0.0, 1.0)


def map_values(
    values: ArrayLike,
    *,
    cmap: str | Colormap,
    norm: NormalizeSpec | None = None,
) -> NDArray[np.float64]:
    """Map finite values to RGBA rows without touching an Axes."""

    scalar_values = validate_color_values(values)
    try:
        colormap = mpl.colormaps.get_cmap(cmap)
    except (TypeError, ValueError) as exc:
        raise PlotError(f"unknown Matplotlib colormap: {cmap!r}") from exc
    selected_norm = _validate_norm(norm)
    normalized = _normalized(scalar_values, selected_norm)
    return np.asarray(colormap(normalized), dtype=float).copy()


def sample_cmap(
    name: str | Colormap,
    *,
    count: int | None = None,
    values: ArrayLike | None = None,
    norm: NormalizeSpec | None = None,
    reverse: bool = False,
) -> NDArray[np.float64]:
    """Sample a Matplotlib colormap as an ``(n, 4)`` RGBA array.

    When both ``count`` and ``values`` are omitted, ten count-based samples are
    returned.  Otherwise exactly one of the two controls is accepted.
    Count-based samples cover the inclusive interval from zero to one.
    Value-based samples use their finite data range; constant values map to
    the midpoint unless an explicit normalizer supplies bounds.

    Parameters
    ----------
    name
        Matplotlib colormap name or native ``Colormap`` object.
    count
        Number of evenly spaced samples, defaulting to ten when ``values`` is
        omitted.
    values
        Finite scalar values to normalize and sample.
    norm
        Optional finite ``(vmin, vmax)`` pair or Matplotlib-compatible callable.
    reverse
        Whether to reverse the sampled colors.

    Returns
    -------
    numpy.ndarray
        An independent floating-point ``(n, 4)`` RGBA array.

    Raises
    ------
    DataError, PlotError
        If the name, count, values, normalizer, or control combination is
        invalid.

    Examples
    --------
    >>> import gsplot as gs
    >>> colors = gs.sample_cmap("viridis", count=3)
    >>> colors.shape
    (3, 4)
    """

    if isinstance(name, str):
        if not name.strip():
            raise PlotError("name must be a non-empty colormap name")
    elif not isinstance(name, Colormap):
        raise PlotError("name must be a colormap name or Colormap")
    if count is not None and values is not None:
        raise PlotError("count and values cannot be supplied together")
    if count is None and values is None:
        count = 10
    if values is None and norm is not None:
        raise OptionError("norm requires values when count is used")
    if not isinstance(reverse, bool):
        raise PlotError("reverse must be a boolean")
    if count is not None:
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            raise PlotError("count must be a positive integer")
        samples = np.linspace(0.0, 1.0, count, dtype=float)
        normalized = (
            samples if norm is None else _normalized(samples, _validate_norm(norm))
        )
        if reverse:
            normalized = normalized[::-1].copy()
        try:
            colormap = mpl.colormaps.get_cmap(name)
        except (TypeError, ValueError) as exc:
            raise PlotError(f"unknown Matplotlib colormap: {name!r}") from exc
        return np.asarray(colormap(normalized), dtype=float).copy()
    if values is None:
        raise PlotError("provide exactly one of count or values")
    scalar_values = validate_color_values(values, name="values")
    try:
        colormap = mpl.colormaps.get_cmap(name)
    except (TypeError, ValueError) as exc:
        raise PlotError(f"unknown Matplotlib colormap: {name!r}") from exc
    if reverse:
        colormap = colormap.reversed()
    normalized = _normalized(scalar_values, _validate_norm(norm))
    return np.asarray(colormap(normalized), dtype=float).copy()


def colors(
    n: int = 10,
    cmap: str | Colormap = "viridis",
    *,
    reverse: bool = False,
) -> NDArray[np.float64]:
    """Return evenly spaced publication colors from a Matplotlib colormap.

    Parameters
    ----------
    n
        Positive number of RGBA rows, defaulting to ``10``.
    cmap
        Registered Matplotlib colormap name or native ``Colormap`` object.
    reverse
        Reverse the sampled row order when ``True``.

    Returns
    -------
    numpy.ndarray
        New finite floating-point ``(n, 4)`` RGBA array.

    Raises
    ------
    PlotError
        If the count, colormap, or reverse control is invalid.

    Notes
    -----
    Multiple colors cover the inclusive interval from zero to one. One color
    samples the midpoint ``0.5``. The operation does not register or mutate a
    colormap.

    Examples
    --------
    >>> import gsplot as gs
    >>> palette = gs.colors(3)
    >>> palette.shape
    (3, 4)
    """

    if type(n) is not int or n < 1:
        raise PlotError("colors: n must be a positive integer")
    if isinstance(cmap, str):
        if not cmap.strip():
            raise PlotError("colors: cmap must be a non-empty colormap name")
    elif not isinstance(cmap, Colormap):
        raise PlotError("colors: cmap must be a colormap name or Colormap")
    if not isinstance(reverse, bool):
        raise PlotError("colors: reverse must be a boolean")
    try:
        colormap = mpl.colormaps.get_cmap(cmap)
    except (TypeError, ValueError) as exc:
        raise PlotError(f"colors: unknown Matplotlib colormap: {cmap!r}") from exc
    points = (
        np.array([0.5], dtype=float)
        if n == 1
        else np.linspace(0.0, 1.0, n, dtype=float)
    )
    try:
        result = np.asarray(colormap(points), dtype=float)
    except (TypeError, ValueError) as exc:
        raise PlotError("colors: cmap could not be sampled as RGBA rows") from exc
    if result.shape != (n, 4) or not np.all(np.isfinite(result)):
        raise PlotError("colors: cmap must return finite RGBA rows")
    return result[::-1].copy() if reverse else result.copy()


def cmap_from_config(config: Config | None) -> str:
    """Resolve the explicit plotting colormap default."""

    if config is None:
        return "viridis"
    if not isinstance(config, Config):
        raise PlotError("config must be a gsplot Config")
    return config.plotting.default_cmap


__all__ = ["colors", "sample_cmap", "map_values", "cmap_from_config"]
