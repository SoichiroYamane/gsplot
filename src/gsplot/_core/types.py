"""Shared type aliases and immutable value objects for canonical APIs."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Protocol, Sequence, TypeAlias

RGBColor: TypeAlias = tuple[float, float, float] | tuple[float, float, float, float]
ColorSpec: TypeAlias = str | RGBColor
MosaicSpec: TypeAlias = str | Sequence[Sequence[str | None]]


class NormalizeSpec(Protocol):
    """Protocol for objects that normalize numerical color values."""

    def __call__(self, value: Any, clip: bool | None = None) -> Any:
        """Normalize a value for a colormap operation."""


@dataclass(frozen=True, slots=True)
class AxisSpec:
    """Immutable axis labels, limits, scales, ticks, and padding."""

    xlabel: str | None = None
    ylabel: str | None = None
    xlim: tuple[float, float] | None = None
    ylim: tuple[float, float] | None = None
    xscale: str | None = None
    yscale: str | None = None
    xticks: tuple[float, ...] | None = None
    yticks: tuple[float, ...] | None = None
    xpadding: float | None = None
    ypadding: float | None = None


@dataclass(frozen=True, slots=True)
class InsetSpec:
    """Immutable placement specification for an inset axes."""

    bounds: tuple[float, float, float, float] | None = None
    width: float | str | None = None
    height: float | str | None = None
    loc: str = "upper right"
    borderpad: float = 0.5


@dataclass(frozen=True, slots=True)
class Theme:
    """Immutable figure/axes theme values applied to an explicit target."""

    name: str = "default"
    figure_facecolor: ColorSpec | None = None
    axes_facecolor: ColorSpec | None = None
    transparent: bool = False


@dataclass(frozen=True, slots=True)
class MetadataSnapshot:
    """Immutable metadata captured for one explicit output operation."""

    version: str
    commit: str | None = None
    config: Mapping[str, Any] = field(default_factory=dict)
    timestamp: str | None = None

    def __post_init__(self) -> None:
        """Freeze the top-level configuration mapping."""

        object.__setattr__(self, "config", MappingProxyType(dict(self.config)))


@dataclass(frozen=True, slots=True)
class BuildInfo:
    """Immutable distribution/build metadata returned by ``build_info``."""

    version: str
    commit: str | None = None
    distribution: str = "gsplot"


@dataclass(frozen=True, slots=True)
class LegendEntries:
    """Immutable handles, labels, and local legend handler mappings."""

    handles: tuple[Any, ...] = ()
    labels: tuple[str, ...] = ()
    handler_map: Mapping[Any, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Normalize sequences and freeze the handler mapping."""

        object.__setattr__(self, "handles", tuple(self.handles))
        object.__setattr__(self, "labels", tuple(self.labels))
        object.__setattr__(
            self, "handler_map", MappingProxyType(dict(self.handler_map))
        )


__all__ = [
    "RGBColor",
    "ColorSpec",
    "MosaicSpec",
    "NormalizeSpec",
    "AxisSpec",
    "InsetSpec",
    "Theme",
    "MetadataSnapshot",
    "BuildInfo",
    "LegendEntries",
]
