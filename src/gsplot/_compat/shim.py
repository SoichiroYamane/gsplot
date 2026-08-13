"""Shared implementation for historical module forwarding shims."""

from __future__ import annotations

import warnings
from collections.abc import Collection
from importlib import import_module
from types import ModuleType
from typing import Any


def load_legacy(target: str, public_name: str) -> ModuleType:
    """Warn once per historical module import and load its isolated target."""

    warnings.warn(
        f"{public_name} is a deprecated compatibility module; migrate to the "
        "canonical gsplot root API",
        DeprecationWarning,
        stacklevel=3,
    )
    return import_module(target)


def module_dir(module: ModuleType, namespace: dict[str, Any]) -> list[str]:
    """Expose forwarded names for interactive discovery."""

    return sorted(set(namespace) | set(dir(module)))


def forwarded_attr(
    module: ModuleType, name: str, public_exports: Collection[str]
) -> Any:
    """Resolve documented functions through reviewed root adapters.

    Historical implementation classes remain reachable for source
    compatibility, but names declared by a documented module's ``__all__``
    share the same adapter as the package root and cannot fork behavior.
    """

    if name in public_exports:
        from .root import resolve_legacy

        return resolve_legacy(name)
    return getattr(module, name)
