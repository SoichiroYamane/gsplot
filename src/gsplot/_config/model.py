"""Immutable schema values for explicit canonical configuration."""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from os import PathLike
from types import MappingProxyType
from typing import Any, Literal, Mapping, TypeAlias, overload

from .._core.errors import ConfigError
from .._core.types import ColorSpec, LayoutMode, SizeSpec, Unit
from .._core.validation import (
    MISSING,
    ensure_bool,
    ensure_mapping,
    ensure_nonempty_text,
    reject_unknown_keys,
)
from .schema import (
    FIGURE_KEYS,
    LEGACY_FIGURE_KEYS,
    PLOTTING_KEYS,
    ROOT_KEYS,
    SCHEMA_VERSION,
    parse_default_color,
    parse_figsize,
    parse_layout,
    parse_schema_version,
    parse_size,
    parse_unit,
    read_json_file,
    validate_section,
)

# Internal value union used by the literal-sensitive Config accessors.
ConfigValue: TypeAlias = tuple[float, float] | ColorSpec | bool | str | None


def _warn_legacy_view(name: str, replacement: str, *, stacklevel: int = 3) -> None:
    """Warn for one lossless or documented-lossy schema-1 read view."""

    warnings.warn(
        f"Config.figure.{name} is deprecated; use Config.figure.{replacement}",
        DeprecationWarning,
        stacklevel=stacklevel,
    )


@dataclass(frozen=True, slots=True)
class FigureConfig:
    """Validated, immutable schema-2 figure defaults."""

    size: SizeSpec = "auto"
    unit: Unit = "in"
    squeeze: bool = True
    layout: LayoutMode = "auto"

    def __post_init__(self) -> None:
        """Validate direct constructor values as well as parsed mappings."""

        object.__setattr__(self, "size", parse_size(self.size))
        object.__setattr__(self, "unit", parse_unit(self.unit))
        object.__setattr__(self, "squeeze", ensure_bool(self.squeeze, "figure.squeeze"))
        object.__setattr__(self, "layout", parse_layout(self.layout))
        if not isinstance(self.size, tuple) and self.unit != "in":
            raise ConfigError(
                "figure.unit must be 'in' unless figure.size is an explicit tuple"
            )

    @property
    def figsize(self) -> tuple[float, float] | None:
        """Return the deprecated lossy schema-1 figure-size view."""

        _warn_legacy_view("figsize", "size")
        return self.size if isinstance(self.size, tuple) else None

    @property
    def tight_layout(self) -> bool:
        """Return whether the schema-2 layout is explicitly ``"tight"``."""

        _warn_legacy_view("tight_layout", "layout")
        return self.layout == "tight"

    @property
    def constrained_layout(self) -> bool:
        """Return whether the schema-2 layout is explicitly ``"constrained"``."""

        _warn_legacy_view("constrained_layout", "layout")
        return self.layout == "constrained"


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
        Canonical configuration schema identity, integer ``2``.
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

    schema_version: Literal[2] = SCHEMA_VERSION
    figure: FigureConfig = field(default_factory=FigureConfig)
    plotting: PlottingConfig = field(default_factory=PlottingConfig)

    def __post_init__(self) -> None:
        """Validate schema identity and nested value types."""

        if self.schema_version != SCHEMA_VERSION or isinstance(
            self.schema_version, bool
        ):
            raise ConfigError("schema_version must be the integer 2")
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
            sections and their reviewed keys. Schema 1 is translated with one
            migration warning.

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
        >>> config = gs.Config.from_mapping(
        ...     {"schema_version": 2, "plotting": {"default_cmap": "plasma"}}
        ... )
        >>> config.plotting.default_cmap
        'plasma'
        """

        return cls._from_mapping(mapping, warning_stacklevel=3)

    @classmethod
    def _from_mapping(
        cls, mapping: Mapping[str, Any], *, warning_stacklevel: int
    ) -> "Config":
        """Parse one mapping with caller-controlled warning attribution."""

        mapping = ensure_mapping(mapping, "configuration")
        reject_unknown_keys(mapping, ROOT_KEYS, "configuration")
        if "schema_version" not in mapping:
            raise ConfigError("configuration requires schema_version")
        schema_version = parse_schema_version(mapping["schema_version"])

        figure_keys = LEGACY_FIGURE_KEYS if schema_version == 1 else FIGURE_KEYS
        figure_mapping = validate_section(
            mapping.get("figure", {}), "figure", figure_keys
        )
        plotting_mapping = validate_section(
            mapping.get("plotting", {}), "plotting", PLOTTING_KEYS
        )

        if schema_version == 1:
            tight = ensure_bool(
                figure_mapping.get("tight_layout", False), "figure.tight_layout"
            )
            constrained = ensure_bool(
                figure_mapping.get("constrained_layout", False),
                "figure.constrained_layout",
            )
            if tight and constrained:
                raise ConfigError(
                    "figure.tight_layout and figure.constrained_layout cannot both be true"
                )
            layout: LayoutMode = (
                "tight" if tight else "constrained" if constrained else "none"
            )
            figure = FigureConfig(
                size=parse_figsize(figure_mapping.get("figsize")),
                unit=parse_unit(figure_mapping.get("unit", "in")),
                squeeze=ensure_bool(
                    figure_mapping.get("squeeze", True), "figure.squeeze"
                ),
                layout=layout,
            )
        else:
            figure = FigureConfig(
                size=parse_size(figure_mapping.get("size", "auto")),
                unit=parse_unit(figure_mapping.get("unit", "in")),
                squeeze=ensure_bool(
                    figure_mapping.get("squeeze", True), "figure.squeeze"
                ),
                layout=parse_layout(figure_mapping.get("layout", "auto")),
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
        if schema_version == 1:
            warnings.warn(
                "configuration schema 1 is deprecated; migrate to schema_version 2",
                DeprecationWarning,
                stacklevel=warning_stacklevel,
            )
        return cls(schema_version=SCHEMA_VERSION, figure=figure, plotting=plotting)

    @classmethod
    def from_file(cls, path: str | PathLike[str]) -> "Config":
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
        2
        """

        mapping = read_json_file(path)
        if "schema_version" not in mapping:
            raise ConfigError("configuration requires schema_version")
        return cls._from_mapping(mapping, warning_stacklevel=3)

    def section(self, name: Literal["figure", "plotting"]) -> Mapping[str, ConfigValue]:
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
                "size": self.figure.size,
                "unit": self.figure.unit,
                "squeeze": self.figure.squeeze,
                "layout": self.figure.layout,
            }
        elif name == "plotting":
            values = {
                "default_color": self.plotting.default_color,
                "default_cmap": self.plotting.default_cmap,
                "nonfinite": self.plotting.nonfinite,
            }
        else:
            raise ConfigError("unknown configuration section")
        return MappingProxyType(values)

    @overload
    def get(self, section: Literal["figure"], option: Literal["size"]) -> SizeSpec: ...

    @overload
    def get(
        self, section: Literal["figure"], option: Literal["unit"]
    ) -> Literal["mm", "cm", "in", "pt"]: ...

    @overload
    def get(
        self,
        section: Literal["figure"],
        option: Literal["squeeze"],
    ) -> bool: ...

    @overload
    def get(
        self, section: Literal["figure"], option: Literal["layout"]
    ) -> LayoutMode: ...

    @overload
    def get(
        self, section: Literal["figure"], option: Literal["figsize"]
    ) -> tuple[float, float] | None: ...

    @overload
    def get(
        self,
        section: Literal["figure"],
        option: Literal["tight_layout", "constrained_layout"],
    ) -> bool: ...

    @overload
    def get(
        self, section: Literal["plotting"], option: Literal["default_color"]
    ) -> Literal["axes"] | ColorSpec: ...

    @overload
    def get(
        self, section: Literal["plotting"], option: Literal["default_cmap"]
    ) -> str: ...

    @overload
    def get(
        self, section: Literal["plotting"], option: Literal["nonfinite"]
    ) -> Literal["raise"]: ...

    @overload
    def get(
        self,
        section: Literal["figure", "plotting"],
        option: str,
        default: Any = MISSING,
    ) -> Any: ...

    def get(
        self,
        section: Literal["figure", "plotting"],
        option: str,
        default: Any = MISSING,
    ) -> Any:
        """Return one validated value from a section.

        Parameters
        ----------
        section
            Section name, either ``"figure"`` or ``"plotting"``.
        option
            Validated key within that section.
        default
            Optional fallback used only when ``option`` is absent.

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

        if section == "figure" and option in {
            "figsize",
            "tight_layout",
            "constrained_layout",
        }:
            replacement = "size" if option == "figsize" else "layout"
            _warn_legacy_view(option, replacement, stacklevel=3)
            if option == "figsize":
                size = self.figure.size
                return size if isinstance(size, tuple) else None
            if option == "tight_layout":
                return self.figure.layout == "tight"
            return self.figure.layout == "constrained"
        values = self.section(section)
        if option not in values:
            if default is not MISSING:
                return default
            raise ConfigError("unknown configuration key in requested section")
        return values[option]

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
        2
        """

        return MappingProxyType(
            {
                "schema_version": self.schema_version,
                "figure": self.section("figure"),
                "plotting": self.section("plotting"),
            }
        )


__all__ = ["FigureConfig", "PlottingConfig", "Config"]
