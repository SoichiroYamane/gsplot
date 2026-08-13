"""Small side-effect-free validation and precedence helpers."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Set
from numbers import Real
from typing import Any, cast

from .errors import ConfigError, DataError, LayoutError
from .options import MISSING, resolve_option


def ensure_finite_real(
    value: Any, name: str, *, error: type[Exception] = DataError
) -> float:
    """Return a finite real number or raise a typed error."""

    if isinstance(value, bool) or not isinstance(value, Real):
        raise error(f"{name} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise error(f"{name} must be finite")
    return result


def ensure_positive(
    value: Any, name: str, *, error: type[Exception] = LayoutError
) -> float:
    """Return a finite positive number or raise a typed error."""

    result = ensure_finite_real(value, name, error=error)
    if result <= 0:
        raise error(f"{name} must be positive")
    return result


def ensure_nonnegative(
    value: Any,
    name: str,
    *,
    error: type[Exception] = LayoutError,
) -> float:
    """Return a finite non-negative number or raise a typed error."""

    result = ensure_finite_real(value, name, error=error)
    if result < 0:
        raise error(f"{name} must be non-negative")
    return result


def ensure_pair(
    value: Any,
    name: str,
    *,
    positive: bool = False,
    error: type[Exception] = LayoutError,
) -> tuple[float, float]:
    """Validate and return a finite numeric pair."""

    if isinstance(value, (str, bytes)):
        raise error(f"{name} must contain exactly two numbers")
    try:
        values = tuple(value)
    except TypeError as exc:
        raise error(f"{name} must contain exactly two numbers") from exc
    if len(values) != 2:
        raise error(f"{name} must contain exactly two numbers")
    validator = ensure_positive if positive else ensure_finite_real
    return (
        validator(values[0], f"{name}[0]", error=error),
        validator(values[1], f"{name}[1]", error=error),
    )


def reject_unknown_keys(
    mapping: Mapping[str, Any],
    allowed: Set[str],
    context: str,
    *,
    error: type[Exception] = ConfigError,
) -> None:
    """Raise when a mapping contains a key outside its closed schema."""

    unknown = set(mapping) - set(allowed)
    if unknown:
        raise error(f"{context} contains unknown key(s)")


def ensure_mapping(
    value: Any, name: str, *, error: type[Exception] = ConfigError
) -> Mapping[str, Any]:
    """Validate a string-keyed mapping without returning mutable state."""

    if not isinstance(value, Mapping):
        raise error(f"{name} must be an object")
    if any(not isinstance(key, str) for key in value):
        raise error(f"{name} keys must be strings")
    return cast(Mapping[str, Any], value)


def ensure_nonempty_text(
    value: Any, name: str, *, error: type[Exception] = ConfigError
) -> str:
    """Return a non-empty string after rejecting whitespace-only values."""

    if not isinstance(value, str) or not value.strip():
        raise error(f"{name} must be a non-empty string")
    return value


def ensure_bool(value: Any, name: str, *, error: type[Exception] = ConfigError) -> bool:
    """Return a strict boolean value."""

    if not isinstance(value, bool):
        raise error(f"{name} must be a boolean")
    return value


def ensure_iterable(
    value: Any, name: str, *, error: type[Exception] = DataError
) -> Iterable[Any]:
    """Return an iterable while rejecting text values that hide a typo."""

    if isinstance(value, (str, bytes)):
        raise error(f"{name} must be an iterable of values, not text")
    try:
        iter(value)
    except TypeError as exc:
        raise error(f"{name} must be iterable") from exc
    return cast(Iterable[Any], value)


__all__ = [
    "MISSING",
    "resolve_option",
    "ensure_finite_real",
    "ensure_positive",
    "ensure_nonnegative",
    "ensure_pair",
    "reject_unknown_keys",
    "ensure_mapping",
    "ensure_nonempty_text",
    "ensure_bool",
    "ensure_iterable",
]
