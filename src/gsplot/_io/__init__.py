"""Lazy canonical file, metadata, and build-information adapters."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = ["read_array", "write_meta", "build_info"]

if TYPE_CHECKING:
    read_array: Any
    write_meta: Any
    build_info: Any


_MODULES = {
    "read_array": ("gsplot._io.arrays", "read_array"),
    "write_meta": ("gsplot._io.metadata", "write_meta"),
    "build_info": ("gsplot._io.build", "build_info"),
}


def __getattr__(name: str) -> Any:
    """Import one I/O adapter only when requested."""

    try:
        module_name, attribute_name = _MODULES[name]
    except KeyError as error:
        raise AttributeError(
            f"module 'gsplot._io' has no attribute {name!r}"
        ) from error
    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value
