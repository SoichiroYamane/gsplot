"""Finite option binding with explicit precedence and provenance."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence, Set
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Generic, TypeVar, cast

import numpy as np

from .errors import OptionError
from .plans import OptionEntry, OptionPlan, OptionSource

T = TypeVar("T")


class _Missing:
    """Identity-only sentinel for an omitted canonical argument."""

    __slots__ = ()

    def __repr__(self) -> str:
        """Return a stable private diagnostic representation."""

        return "<omitted>"


MISSING: object = _Missing()


def _freeze(value: Any) -> Any:
    """Detach common mutable containers before they enter a frozen plan."""

    if isinstance(value, np.ndarray):
        return _freeze(value.tolist())
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, Set) and not isinstance(value, (str, bytes)):
        return frozenset(_freeze(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class OptionSpec(Generic[T]):
    """One canonical finite option definition shared by operation binders."""

    name: str
    default: T
    aliases: tuple[str, ...] = ()
    validator: Callable[[Any, str], T] | None = None

    def __post_init__(self) -> None:
        """Validate names and detach mutable default values."""

        if not isinstance(self.name, str) or not self.name:
            raise ValueError("option name must be non-empty text")
        aliases = tuple(self.aliases)
        if any(not isinstance(alias, str) or not alias for alias in aliases):
            raise ValueError("option aliases must be non-empty text")
        if self.name in aliases or len(set(aliases)) != len(aliases):
            raise ValueError("option aliases must be unique")
        if self.validator is not None and not callable(self.validator):
            raise ValueError("option validator must be callable or None")
        object.__setattr__(self, "aliases", aliases)
        object.__setattr__(self, "default", _freeze(self.default))

    def normalize(self, value: Any) -> T:
        """Validate and detach one resolved option value."""

        selected = self.validator(value, self.name) if self.validator else value
        return cast(T, _freeze(selected))


def resolve_option(
    explicit: T | object,
    configured: T | object,
    default: T,
) -> T:
    """Resolve one value using explicit, configured, then default precedence."""

    if explicit is not MISSING:
        return explicit  # type: ignore[return-value]
    if configured is not MISSING:
        return configured  # type: ignore[return-value]
    return default


def supplied_options(values: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return a detached mapping containing only non-omitted call arguments."""

    if not isinstance(values, Mapping) or any(
        not isinstance(key, str) for key in values
    ):
        raise TypeError("supplied options must be a string-keyed mapping")
    return MappingProxyType(
        {key: _freeze(value) for key, value in values.items() if value is not MISSING}
    )


def _spec_index(
    specs: Sequence[OptionSpec[Any]],
) -> tuple[tuple[OptionSpec[Any], ...], dict[str, str]]:
    """Validate a finite specification and map every spelling to canonical form."""

    selected = tuple(specs)
    names: dict[str, str] = {}
    for spec in selected:
        if not isinstance(spec, OptionSpec):
            raise TypeError("option specifications must contain OptionSpec values")
        for spelling in (spec.name, *spec.aliases):
            if spelling in names:
                raise ValueError(
                    f"duplicate option spelling in specification: {spelling}"
                )
            names[spelling] = spec.name
    return selected, names


def _canonicalize(
    operation: str,
    source: str,
    values: Mapping[str, Any] | None,
    spellings: Mapping[str, str],
    *,
    aliases: bool,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Validate one supplied mapping and retain the spelling used by its caller."""

    if values is None:
        return {}, {}
    if not isinstance(values, Mapping):
        raise OptionError(f"{operation}: {source} options must be a mapping")
    normalized: dict[str, Any] = {}
    supplied_as: dict[str, str] = {}
    for name, value in values.items():
        if not isinstance(name, str) or name not in spellings:
            raise OptionError(f"{operation}: {source} contains an unsupported option")
        canonical = spellings[name]
        if not aliases and name != canonical:
            raise OptionError(f"{operation}: {source} must use canonical option names")
        if value is MISSING:
            continue
        if canonical in normalized:
            raise OptionError(
                f"{operation}: option {canonical!r} was supplied more than once"
            )
        normalized[canonical] = value
        supplied_as[canonical] = name
    return normalized, supplied_as


def bind_options(
    operation: str,
    specs: Sequence[OptionSpec[Any]],
    *,
    explicit: Mapping[str, Any] | None = None,
    derived: Mapping[str, Any] | None = None,
    configured: Mapping[str, Any] | None = None,
    props: Mapping[str, Any] | None = None,
) -> OptionPlan:
    """Resolve a closed option set before a canonical operation mutates state.

    Precedence is explicit direct or ``props`` value, derived value, explicit
    Config value, then the validated library default.  Canonical/alias and
    direct/``props`` duplicates fail during binding.
    """

    selected, spellings = _spec_index(specs)
    direct, direct_names = _canonicalize(
        operation, "explicit", explicit, spellings, aliases=True
    )
    property_values, property_names = _canonicalize(
        operation, "props", props, spellings, aliases=True
    )
    derived_values, _ = _canonicalize(
        operation, "derived", derived, spellings, aliases=False
    )
    config_values, _ = _canonicalize(
        operation, "config", configured, spellings, aliases=False
    )
    conflicts = set(direct) & set(property_values)
    if conflicts:
        name = sorted(conflicts)[0]
        raise OptionError(
            f"{operation}: option {name!r} cannot be supplied directly and in props"
        )

    entries: list[OptionEntry[Any]] = []
    for spec in selected:
        supplied_as: str | None = None
        source: OptionSource
        if spec.name in direct:
            value = direct[spec.name]
            source = "explicit"
            supplied_as = direct_names[spec.name]
        elif spec.name in property_values:
            value = property_values[spec.name]
            source = "explicit"
            supplied_as = f"props.{property_names[spec.name]}"
        elif spec.name in derived_values:
            value = derived_values[spec.name]
            source = "derived"
        elif spec.name in config_values:
            value = config_values[spec.name]
            source = "config"
        else:
            value = spec.default
            source = "default"
        entries.append(
            OptionEntry(
                name=spec.name,
                value=spec.normalize(value),
                source=source,
                supplied_as=supplied_as,
            )
        )
    return OptionPlan(operation=operation, entries=tuple(entries))


__all__ = [
    "MISSING",
    "OptionSpec",
    "resolve_option",
    "supplied_options",
    "bind_options",
]
