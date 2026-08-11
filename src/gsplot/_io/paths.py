"""Pure path normalization helpers used by explicit I/O operations."""

from __future__ import annotations

from os import PathLike
from pathlib import Path
from typing import TypeVar

from .._core.errors import OutputError

T = TypeVar("T", bound=Exception)


def resolve_path(value: str | PathLike[str], name: str = "path") -> Path:
    """Return a normalized absolute caller-owned path."""

    if not isinstance(value, (str, PathLike)):
        raise OutputError(f"{name} must be a path-like value")
    if isinstance(value, str) and not value.strip():
        raise OutputError(f"{name} must not be empty")
    try:
        return Path(value).expanduser().resolve()
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise OutputError(f"could not resolve {name}") from exc


__all__ = ["resolve_path"]
