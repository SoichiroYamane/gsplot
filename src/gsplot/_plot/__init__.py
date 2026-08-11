"""Lazy canonical plotting adapters."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = [
    "line",
    "scatter",
    "cmap_line",
    "cmap_dash",
    "cmap_scatter",
    "sample_cmap",
]

if TYPE_CHECKING:
    line: Any
    scatter: Any
    cmap_line: Any
    cmap_dash: Any
    cmap_scatter: Any
    sample_cmap: Any


_MODULES = {
    "line": ("gsplot._plot.basic", "line"),
    "scatter": ("gsplot._plot.basic", "scatter"),
    "cmap_line": ("gsplot._plot.colored", "cmap_line"),
    "cmap_dash": ("gsplot._plot.colored", "cmap_dash"),
    "cmap_scatter": ("gsplot._plot.colored", "cmap_scatter"),
    "sample_cmap": ("gsplot._plot.colormap", "sample_cmap"),
}


def __getattr__(name: str) -> Any:
    """Import one plotting adapter only when requested."""

    try:
        module_name, attribute_name = _MODULES[name]
    except KeyError as error:
        raise AttributeError(
            f"module 'gsplot._plot' has no attribute {name!r}"
        ) from error
    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value
