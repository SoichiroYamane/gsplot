"""Immutable plans shared by canonical plotting operations."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any, Generic, Literal, TypeVar

from matplotlib.axes import Axes
from matplotlib.axes._base import _AxesBase
from matplotlib.figure import Figure

from .errors import PlotError

T = TypeVar("T")
TargetKind = Literal["single", "sequence", "array", "mapping"]
OptionSource = Literal["explicit", "derived", "config", "default"]


def _operation_name(value: str) -> str:
    """Validate an internal operation label used in safe error messages."""

    if not isinstance(value, str) or not value or not value.replace("_", "").isalnum():
        raise ValueError("operation must be a non-empty identifier")
    return value


def _axis_root_figure(axis: Any) -> Figure | None:
    """Return an Axes root Figure without requiring ``root=True`` support."""

    owner: Any = axis.get_figure()
    visited: set[int] = set()
    while not isinstance(owner, Figure):
        if owner is None or id(owner) in visited:
            return None
        visited.add(id(owner))
        owner = getattr(owner, "figure", None)
    return owner


@dataclass(frozen=True, slots=True)
class TargetPlan:
    """Normalized, ordered Axes ownership for one canonical operation.

    The plan exists only for the lifetime of an operation.  Canonical code must
    not store it in a module-level registry.
    """

    operation: str
    figure: Figure
    axes: tuple[Axes | _AxesBase, ...]
    keys: tuple[object, ...]
    kind: TargetKind

    def __post_init__(self) -> None:
        """Reject malformed plans even when constructed without the normalizer."""

        _operation_name(self.operation)
        if not isinstance(self.figure, Figure):
            raise PlotError(f"{self.operation}: target has no root Figure")
        if not self.axes or len(self.keys) != len(self.axes):
            raise PlotError(f"{self.operation}: target plan is empty or incomplete")
        if self.kind not in {"single", "sequence", "array", "mapping"}:
            raise PlotError(f"{self.operation}: target kind is invalid")
        if any(not isinstance(axis, (Axes, _AxesBase)) for axis in self.axes):
            raise PlotError(f"{self.operation}: target contains a non-Axes value")
        if len({id(axis) for axis in self.axes}) != len(self.axes):
            raise PlotError(f"{self.operation}: target contains a duplicate Axes")
        if any(_axis_root_figure(axis) is not self.figure for axis in self.axes):
            raise PlotError(
                f"{self.operation}: target plan does not match its root Figure"
            )

    @property
    def single(self) -> bool:
        """Return whether the normalized target contains exactly one Axes."""

        return len(self.axes) == 1


@dataclass(frozen=True, slots=True)
class OptionEntry(Generic[T]):
    """One validated option value and its resolution provenance."""

    name: str
    value: T
    source: OptionSource
    supplied_as: str | None = None

    def __post_init__(self) -> None:
        """Validate the finite option identity and source."""

        if not isinstance(self.name, str) or not self.name:
            raise ValueError("option name must be non-empty text")
        if self.source not in {"explicit", "derived", "config", "default"}:
            raise ValueError("option source is invalid")
        if self.supplied_as is not None and not isinstance(self.supplied_as, str):
            raise ValueError("supplied option name must be text or None")


@dataclass(frozen=True, slots=True)
class OptionPlan(Mapping[str, Any]):
    """Immutable finite option set resolved before Matplotlib mutation."""

    operation: str
    entries: tuple[OptionEntry[Any], ...]

    def __post_init__(self) -> None:
        """Reject duplicate option names and malformed operation labels."""

        _operation_name(self.operation)
        names = tuple(entry.name for entry in self.entries)
        if len(set(names)) != len(names):
            raise ValueError("option plan contains duplicate names")

    def __getitem__(self, name: str) -> Any:
        """Return one resolved value by canonical option name."""

        return self.entry(name).value

    def __iter__(self) -> Iterator[str]:
        """Iterate canonical option names in specification order."""

        return (entry.name for entry in self.entries)

    def __len__(self) -> int:
        """Return the number of finite options in the plan."""

        return len(self.entries)

    def entry(self, name: str) -> OptionEntry[Any]:
        """Return one complete option entry, including provenance."""

        for entry in self.entries:
            if entry.name == name:
                return entry
        raise KeyError(name)

    def source(self, name: str) -> OptionSource:
        """Return the precedence source selected for one option."""

        return self.entry(name).source

    def was_supplied(self, name: str) -> bool:
        """Return whether a caller supplied the resolved option explicitly."""

        return self.entry(name).source == "explicit"


@dataclass(frozen=True, slots=True)
class OperationPlan:
    """Reusable immutable pairing of target and finite option plans."""

    operation: str
    target: TargetPlan
    options: OptionPlan

    def __post_init__(self) -> None:
        """Require every component to describe the same operation."""

        _operation_name(self.operation)
        if not isinstance(self.target, TargetPlan):
            raise ValueError("target must be a TargetPlan")
        if not isinstance(self.options, OptionPlan):
            raise ValueError("options must be an OptionPlan")
        if self.target.operation != self.operation:
            raise ValueError("target plan belongs to a different operation")
        if self.options.operation != self.operation:
            raise ValueError("option plan belongs to a different operation")


__all__ = [
    "TargetKind",
    "OptionSource",
    "TargetPlan",
    "OptionEntry",
    "OptionPlan",
    "OperationPlan",
]
