"""Immutable schema values for explicit canonical configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, Mapping

from .._core.errors import ConfigError
from .._core.types import ColorSpec
from .._core.validation import (
    MISSING,
    ensure_bool,
    ensure_mapping,
    ensure_nonempty_text,
    reject_unknown_keys,
)
from .schema import (
    FIGURE_KEYS,
    PLOTTING_KEYS,
    ROOT_KEYS,
    SCHEMA_VERSION,
    parse_default_color,
    parse_figsize,
    parse_schema_version,
    parse_unit,
    read_json_file,
    validate_section,
)


@dataclass(frozen=True, slots=True)
class FigureConfig:
    """Validated, immutable figure defaults."""

    figsize: tuple[float, float] | None = None
    unit: Literal["mm", "cm", "in", "pt"] = "in"
    squeeze: bool = True
    tight_layout: bool = False
    constrained_layout: bool = False

    def __post_init__(self) -> None:
        """Validate direct constructor values as well as parsed mappings."""

        object.__setattr__(self, "figsize", parse_figsize(self.figsize))
        object.__setattr__(self, "unit", parse_unit(self.unit))
        object.__setattr__(self, "squeeze", ensure_bool(self.squeeze, "figure.squeeze"))
        object.__setattr__(
            self,
            "tight_layout",
            ensure_bool(self.tight_layout, "figure.tight_layout"),
        )
        object.__setattr__(
            self,
            "constrained_layout",
            ensure_bool(self.constrained_layout, "figure.constrained_layout"),
        )


@dataclass(frozen=True, slots=True)
class PlottingConfig:
    """Validated, immutable plotting defaults."""

    default_color: ColorSpec | Literal["axes"] = "axes"
    default_cmap: str = "viridis"
    nonfinite: Literal["raise"] = "raise"

    def __post_init__(self) -> None:
        """Validate color, colormap, and non-finite-data policy."""

        object.__setattr__(
            self, "default_color", parse_default_color(self.default_color)
        )
        object.__setattr__(
            self,
            "default_cmap",
            ensure_nonempty_text(self.default_cmap, "plotting.default_cmap"),
        )
        if self.nonfinite != "raise":
            raise ConfigError("plotting.nonfinite must be 'raise'")


@dataclass(frozen=True, slots=True, kw_only=True)
class Config:
    """Immutable schema-versioned configuration for canonical operations.

    Parameters
    ----------
    schema_version
        Supported configuration schema identity, currently integer ``1``.
    figure
        Immutable figure defaults such as size, units, and layout flags.
    plotting
        Immutable plotting defaults such as color, colormap, and finite-data
        policy.

    Notes
    -----
    ``Config()`` contains library defaults and is independent from every other
    instance.  Use :meth:`from_mapping` or :meth:`from_file` for caller data;
    no mutable mapping is retained.

    Examples
    --------
    >>> import gsplot as gs
    >>> config = gs.Config()
    >>> config.plotting.default_cmap
    'viridis'
    """

    schema_version: Literal[1] = SCHEMA_VERSION
    figure: FigureConfig = field(default_factory=FigureConfig)
    plotting: PlottingConfig = field(default_factory=PlottingConfig)

    def __post_init__(self) -> None:
        """Validate schema identity and nested value types."""

        object.__setattr__(
            self, "schema_version", parse_schema_version(self.schema_version)
        )
        if not isinstance(self.figure, FigureConfig):
            raise ConfigError("figure must be a FigureConfig")
        if not isinstance(self.plotting, PlottingConfig):
            raise ConfigError("plotting must be a PlottingConfig")

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "Config":
        """Create validated configuration from a mapping without retaining it.

        Parameters
        ----------
        mapping
            Versioned mapping containing only ``figure`` and ``plotting``
            sections and their reviewed keys.

        Returns
        -------
        Config
            A fresh immutable configuration value.

        Raises
        ------
        ConfigError
            If a section, key, schema value, or scalar has an invalid type or
            value.

        Examples
        --------
        >>> import gsplot as gs
        >>> config = gs.Config.from_mapping({"plotting": {"default_cmap": "plasma"}})
        >>> config.plotting.default_cmap
        'plasma'
        """

        mapping = ensure_mapping(mapping, "configuration")
        reject_unknown_keys(mapping, ROOT_KEYS, "configuration")
        schema_version = parse_schema_version(mapping.get("schema_version", 1))

        figure_mapping = validate_section(
            mapping.get("figure", {}), "figure", FIGURE_KEYS
        )
        plotting_mapping = validate_section(
            mapping.get("plotting", {}), "plotting", PLOTTING_KEYS
        )

        figure = FigureConfig(
            figsize=parse_figsize(figure_mapping.get("figsize")),
            unit=parse_unit(figure_mapping.get("unit", "in")),
            squeeze=ensure_bool(figure_mapping.get("squeeze", True), "figure.squeeze"),
            tight_layout=ensure_bool(
                figure_mapping.get("tight_layout", False), "figure.tight_layout"
            ),
            constrained_layout=ensure_bool(
                figure_mapping.get("constrained_layout", False),
                "figure.constrained_layout",
            ),
        )
        plotting = PlottingConfig(
            default_color=parse_default_color(
                plotting_mapping.get("default_color", "axes")
            ),
            default_cmap=ensure_nonempty_text(
                plotting_mapping.get("default_cmap", "viridis"),
                "plotting.default_cmap",
            ),
            nonfinite=plotting_mapping.get("nonfinite", "raise"),
        )
        return cls(schema_version=schema_version, figure=figure, plotting=plotting)

    @classmethod
    def from_file(cls, path: str | Path) -> "Config":
        """Load one explicit bounded JSON file into immutable values.

        Parameters
        ----------
        path
            Explicit UTF-8 JSON configuration path.

        Returns
        -------
        Config
            A fresh immutable configuration value.

        Raises
        ------
        ConfigError
            If the path cannot be read or the bounded JSON schema is invalid.

        Examples
        --------
        >>> import gsplot as gs
        >>> config = gs.Config.from_file("gsplot.json")
        >>> config.schema_version
        1
        """

        return cls.from_mapping(read_json_file(path))

    def section(self, name: Literal["figure", "plotting"]) -> Mapping[str, Any]:
        """Return an immutable top-level section mapping.

        Parameters
        ----------
        name
            Section name, either ``"figure"`` or ``"plotting"``.

        Returns
        -------
        collections.abc.Mapping
            Read-only values detached from mutable caller data.

        Raises
        ------
        ConfigError
            If ``name`` is not a supported section.

        Examples
        --------
        >>> import gsplot as gs
        >>> section = gs.Config().section("figure")
        >>> section["unit"]
        'in'
        """

        if name == "figure":
            values: dict[str, Any] = {
                "figsize": self.figure.figsize,
                "unit": self.figure.unit,
                "squeeze": self.figure.squeeze,
                "tight_layout": self.figure.tight_layout,
                "constrained_layout": self.figure.constrained_layout,
            }
        elif name == "plotting":
            values = {
                "default_color": self.plotting.default_color,
                "default_cmap": self.plotting.default_cmap,
                "nonfinite": self.plotting.nonfinite,
            }
        else:
            raise ConfigError(f"unknown configuration section: {name!r}")
        return MappingProxyType(values)

    def get(
        self,
        section: Literal["figure", "plotting"],
        key: str,
        default: Any = MISSING,
    ) -> Any:
        """Return one validated value from a section.

        Parameters
        ----------
        section
            Section name, either ``"figure"`` or ``"plotting"``.
        key
            Validated key within that section.
        default
            Optional fallback used only when ``key`` is absent.

        Returns
        -------
        Any
            The immutable configured value or the supplied default.

        Raises
        ------
        ConfigError
            If the section or key is unsupported and no default is supplied.

        Examples
        --------
        >>> import gsplot as gs
        >>> gs.Config().get("plotting", "default_cmap")
        'viridis'
        """

        values = self.section(section)
        if key not in values:
            if default is not MISSING:
                return default
            raise ConfigError(f"unknown configuration key: {section}.{key}")
        return values[key]

    def as_mapping(self) -> Mapping[str, Any]:
        """Return an immutable top-level representation suitable for metadata.

        Returns
        -------
        collections.abc.Mapping
            Read-only schema-versioned configuration values.

        Examples
        --------
        >>> import gsplot as gs
        >>> mapping = gs.Config().as_mapping()
        >>> mapping["schema_version"]
        1
        """

        return MappingProxyType(
            {
                "schema_version": self.schema_version,
                "figure": self.section("figure"),
                "plotting": self.section("plotting"),
            }
        )


__all__ = ["FigureConfig", "PlottingConfig", "Config"]
