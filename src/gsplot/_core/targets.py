"""Deterministic explicit-Axes target normalization."""

from __future__ import annotations

from collections.abc import Mapping, Sequence, Set
from typing import Any, TypeVar

import numpy as np
from matplotlib.axes import Axes
from matplotlib.axes._base import _AxesBase
from matplotlib.figure import Figure

from .errors import PlotError
from .plans import TargetKind, TargetPlan, _axis_root_figure
from .types import AxesTarget

T = TypeVar("T")


def _root_figure(axis: Axes | _AxesBase, operation: str) -> Figure:
    """Resolve an Axes root Figure without version-specific root arguments."""

    owner = _axis_root_figure(axis)
    if owner is None:
        raise PlotError(f"{operation}: target Axes has no root Figure")
    return owner


def _snapshot_target(
    target: Any, operation: str
) -> tuple[TargetKind, tuple[object, ...], tuple[Any, ...]]:
    """Snapshot one supported target shape without retaining its container."""

    if isinstance(target, (Axes, _AxesBase)):
        return "single", (target,), (target,)
    if isinstance(target, Mapping):
        items = tuple(target.items())
        return (
            "mapping",
            tuple(key for key, _ in items),
            tuple(value for _, value in items),
        )
    if isinstance(target, np.ndarray):
        if target.ndim == 0:
            raise PlotError(f"{operation}: target array must contain at least one Axes")
        values = tuple(target.ravel(order="C").tolist())
        return "array", values, values
    if isinstance(target, (str, bytes)):
        raise PlotError(
            f"{operation}: target must be an Axes or ordered Axes collection"
        )
    if isinstance(target, Set):
        raise PlotError(f"{operation}: target must not be an unordered set")
    if isinstance(target, Sequence):
        values = tuple(target)
        return "sequence", values, values
    raise PlotError(f"{operation}: target must be an Axes or ordered Axes collection")


def normalize_axes(target: AxesTarget, *, operation: str) -> TargetPlan:
    """Normalize one finite Axes target before any Matplotlib mutation.

    Sequence order, NumPy C order, and mapping insertion order are preserved.
    Mapping keys remain the per-target keys; all other shapes use their Axes
    objects as keys.
    """

    kind, keys, values = _snapshot_target(target, operation)
    if not values:
        raise PlotError(f"{operation}: target must contain at least one Axes")
    if any(not isinstance(value, (Axes, _AxesBase)) for value in values):
        raise PlotError(f"{operation}: target contains a non-Axes value")
    axes = tuple(values)
    if len({id(axis) for axis in axes}) != len(axes):
        raise PlotError(f"{operation}: target contains a duplicate Axes")
    root = _root_figure(axes[0], operation)
    if any(_root_figure(axis, operation) is not root for axis in axes[1:]):
        raise PlotError(f"{operation}: target Axes must belong to one Figure")
    return TargetPlan(
        operation=operation,
        figure=root,
        axes=axes,
        keys=keys,
        kind=kind,
    )


def resolve_target_mapping(
    target: TargetPlan,
    values: Mapping[object, T],
    *,
    name: str,
) -> tuple[T, ...]:
    """Resolve an exact per-target mapping into normalized target order."""

    if not isinstance(values, Mapping):
        raise PlotError(f"{target.operation}: {name} must be a mapping")
    try:
        exact = len(values) == len(target.keys) and all(
            key in values for key in target.keys
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise PlotError(
            f"{target.operation}: {name} must use the normalized target keys"
        ) from exc
    if not exact:
        raise PlotError(
            f"{target.operation}: {name} must use exactly the normalized target keys"
        )
    return tuple(values[key] for key in target.keys)


__all__ = ["normalize_axes", "resolve_target_mapping"]
