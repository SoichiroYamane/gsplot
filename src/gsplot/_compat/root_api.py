"""Root-level compatibility dispatch for overlapping 0.x names.

This boundary is intentionally the only place that chooses between the strict
canonical explicit-target form and a characterized legacy call form. Private
canonical modules never import it.
"""

from __future__ import annotations

import inspect
import warnings
from typing import Any, Callable, cast

from matplotlib.axes import Axes
from matplotlib.figure import Figure

from .._figure.output import show as _show
from .._plot.basic import line as _line
from .._plot.basic import scatter as _scatter
from .._style.axes import title as _title
from .._style.legends import legend as _legend

_LEGACY_LINE_KEYS = {
    "color",
    "marker",
    "markersize",
    "markeredgewidth",
    "markeredgecolor",
    "markerfacecolor",
    "linestyle",
    "linewidth",
    "alpha",
    "alpha_mfc",
    "label",
    "ms",
    "mew",
    "ls",
    "lw",
    "c",
    "mec",
    "mfc",
}
_LEGACY_SCATTER_KEYS = {"color", "size", "alpha", "s"}
_CANONICAL_LEGEND_KEYS = {
    "handles",
    "labels",
    "handler_map",
    "reverse",
    "replace",
    "props",
}


def _warn(name: str) -> None:
    """Emit one caller-facing deprecation warning for a legacy dispatch."""

    warnings.warn(
        f"legacy gsplot.{name} call syntax is deprecated; use the canonical "
        "explicit-target signature",
        DeprecationWarning,
        stacklevel=3,
    )


def _legacy(function_name: str) -> Callable[..., Any]:
    """Load one historical implementation only for a legacy call."""

    if function_name == "line":
        from ..plot.line import line

        return cast(Callable[..., Any], line)
    if function_name == "scatter":
        from ..plot.scatter import scatter

        return cast(Callable[..., Any], scatter)
    if function_name == "legend":
        from ..style.legend import legend

        return cast(Callable[..., Any], legend)
    if function_name == "title":
        from ..style.title import title

        return cast(Callable[..., Any], title)
    if function_name == "show":
        from ..figure.show import show

        return cast(Callable[..., Any], show)
    raise RuntimeError(f"unknown legacy function: {function_name}")


def line(*args: Any, **kwargs: Any) -> Any:
    """Dispatch canonical ``line`` or a legacy named-option call."""

    legacy = len(args) > 3 or bool(_LEGACY_LINE_KEYS & set(kwargs))
    if not legacy:
        return _line(*args, **kwargs)
    _warn("line")
    return _legacy("line")(*args, **kwargs)


def scatter(*args: Any, **kwargs: Any) -> Any:
    """Dispatch canonical ``scatter`` or a legacy named-option call."""

    legacy = len(args) > 3 or bool(_LEGACY_SCATTER_KEYS & set(kwargs))
    if not legacy:
        return _scatter(*args, **kwargs)
    _warn("scatter")
    return _legacy("scatter")(*args, **kwargs)


def legend(*args: Any, **kwargs: Any) -> Any:
    """Dispatch canonical ``legend`` or a legacy positional/keyword call."""

    legacy = bool(args) and not isinstance(args[0], Axes)
    if len(args) > 1:
        legacy = True
    legacy = legacy or bool(set(kwargs) - _CANONICAL_LEGEND_KEYS)
    if not legacy:
        return _legend(*args, **kwargs)
    _warn("legend")
    return _legacy("legend")(*args, **kwargs)


def title(*args: Any, **kwargs: Any) -> Any:
    """Dispatch explicit Axes title or the legacy current-Figure title."""

    if args and isinstance(args[0], Axes):
        return _title(*args, **kwargs)
    if isinstance(kwargs.get("ax"), Axes):
        return _title(*args, **kwargs)
    _warn("title")
    return _legacy("title")(*args, **kwargs)


def show(*args: Any, **kwargs: Any) -> Any:
    """Dispatch explicit Figure display or legacy save-and-display syntax."""

    if args and isinstance(args[0], Figure) and not kwargs:
        return _show(*args)
    if isinstance(kwargs.get("fig"), Figure) and set(kwargs) <= {"fig"}:
        return _show(kwargs["fig"])
    _warn("show")
    return _legacy("show")(*args, **kwargs)


line.__signature__ = inspect.signature(_line)  # type: ignore[attr-defined]
scatter.__signature__ = inspect.signature(_scatter)  # type: ignore[attr-defined]
legend.__signature__ = inspect.signature(_legend)  # type: ignore[attr-defined]
title.__signature__ = inspect.signature(_title)  # type: ignore[attr-defined]
show.__signature__ = inspect.signature(_show)  # type: ignore[attr-defined]


__all__ = ["line", "scatter", "legend", "title", "show"]
