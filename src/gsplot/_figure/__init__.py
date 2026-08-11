"""Private explicit figure ownership and backend helpers."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = ["subplots", "inset_axes", "use_backend"]

if TYPE_CHECKING:
    subplots: Any
    inset_axes: Any
    use_backend: Any


def __getattr__(name: str) -> Any:
    """Load one figure helper without importing pyplot for the package."""

    if name == "subplots":
        value = getattr(import_module("gsplot._figure.layout"), name)
    elif name == "inset_axes":
        value = getattr(import_module("gsplot._figure.inset"), name)
    elif name == "use_backend":
        value = getattr(import_module("gsplot._figure.backend"), name)
    else:
        raise AttributeError(f"module 'gsplot._figure' has no attribute {name!r}")
    globals()[name] = value
    return value
