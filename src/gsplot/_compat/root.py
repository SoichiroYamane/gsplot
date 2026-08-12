"""Lazy adapters for the 0.3.x package-root API.

The compatibility layer is deliberately one-way: it may import historical
modules when a legacy name is first used, while canonical implementation
modules must never import this module. Keeping the lookup lazy prevents a
plain ``import gsplot`` from importing pyplot, configuring Matplotlib, or
loading the legacy configuration singleton.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any, Final

_LEGACY_EXPORTS: Final[dict[str, tuple[str, str]]] = {
    "get_cmap": ("gsplot._compat.legacy_api", "get_cmap"),
    "load_file": ("gsplot._compat.legacy_api", "load_file"),
    "load_file_fast": ("gsplot._compat.legacy_api", "load_file_fast"),
    "axes": ("gsplot._compat.legacy_api", "axes"),
    "axes_inset": ("gsplot._compat.legacy_api", "axes_inset"),
    "axes_inset_padding": ("gsplot._compat.legacy_api", "axes_inset_padding"),
    "get_figure_size": ("gsplot._compat.legacy_api", "get_figure_size"),
    "show": ("gsplot._compat.root_api", "show"),
    "hello_world": ("gsplot.hello_world.hello_world", "hello_world"),
    "config_load": ("gsplot._compat.legacy_api", "config_load"),
    "config_dict": ("gsplot._compat.legacy_api", "config_dict"),
    "config_entry_option": ("gsplot._compat.legacy_api", "config_entry_option"),
    "home": ("gsplot._compat.legacy_api", "home"),
    "pwd": ("gsplot._compat.legacy_api", "pwd"),
    "pwd_move": ("gsplot._compat.legacy_api", "pwd_move"),
    "pwd_main": ("gsplot._compat.legacy_api", "pwd_main"),
    "line": ("gsplot._compat.root_api", "line"),
    "line_colormap_solid": ("gsplot._compat.legacy_api", "line_colormap_solid"),
    "line_colormap_dashed": ("gsplot._compat.legacy_api", "line_colormap_dashed"),
    "scatter": ("gsplot._compat.root_api", "scatter"),
    "scatter_colormap": ("gsplot._compat.legacy_api", "scatter_colormap"),
    "graph_square": ("gsplot._compat.legacy_api", "graph_square"),
    "graph_square_axes": ("gsplot._compat.legacy_api", "graph_square_axes"),
    "graph_white": ("gsplot._compat.legacy_api", "graph_white"),
    "graph_white_axes": ("gsplot._compat.legacy_api", "graph_white_axes"),
    "graph_transparent": ("gsplot._compat.legacy_api", "graph_transparent"),
    "graph_transparent_axes": (
        "gsplot._compat.legacy_api",
        "graph_transparent_axes",
    ),
    "graph_facecolor": ("gsplot._compat.legacy_api", "graph_facecolor"),
    "label": ("gsplot._compat.root_api", "label"),
    "label_add_index": ("gsplot._compat.legacy_api", "label_add_index"),
    "legend": ("gsplot._compat.root_api", "legend"),
    "legend_axes": ("gsplot._compat.legacy_api", "legend_axes"),
    "legend_handlers": ("gsplot._compat.legacy_api", "legend_handlers"),
    "legend_reverse": ("gsplot._compat.legacy_api", "legend_reverse"),
    "legend_get_handlers": ("gsplot._compat.legacy_api", "legend_get_handlers"),
    "legend_colormap": ("gsplot._compat.legacy_api", "legend_colormap"),
    "ticks_off": ("gsplot._compat.legacy_api", "ticks_off"),
    "ticks_on": ("gsplot._compat.legacy_api", "ticks_on"),
    "ticks_on_axes": ("gsplot._compat.legacy_api", "ticks_on_axes"),
    "title": ("gsplot._compat.root_api", "title"),
    "title_axes": ("gsplot._compat.legacy_api", "title_axes"),
    "Config": ("gsplot.config.config", "Config"),
    "save_metadata": ("gsplot._compat.root_legacy", "save_metadata"),
    "logger": ("gsplot.logger", "logger"),
}

_CANONICAL_EXPORTS: Final[dict[str, tuple[str, str]]] = {
    "subplots": ("gsplot._figure.layout", "subplots"),
    "inset": ("gsplot._figure.inset", "inset"),
    "inset_axes": ("gsplot._figure.inset", "inset_axes"),
    "savefig": ("gsplot._figure.output", "savefig"),
    "show": ("gsplot._compat.root_api", "show"),
    "use_backend": ("gsplot._figure.backend", "use_backend"),
    "line": ("gsplot._compat.root_api", "line"),
    "scatter": ("gsplot._compat.root_api", "scatter"),
    "cmap_line": ("gsplot._plot.colored", "cmap_line"),
    "cmap_dash": ("gsplot._plot.colored", "cmap_dash"),
    "cmap_scatter": ("gsplot._plot.colored", "cmap_scatter"),
    "colors": ("gsplot._plot.colormap", "colors"),
    "sample_cmap": ("gsplot._plot.colormap", "sample_cmap"),
    "style_axes": ("gsplot._style.axes", "style_axes"),
    "label": ("gsplot._compat.root_api", "label"),
    "square": ("gsplot._style.axes", "square"),
    "title": ("gsplot._compat.root_api", "title"),
    "suptitle": ("gsplot._style.axes", "suptitle"),
    "minor_ticks": ("gsplot._style.axes", "minor_ticks"),
    "box_aspect": ("gsplot._style.axes", "box_aspect"),
    "panel_labels": ("gsplot._style.panels", "panel_labels"),
    "index": ("gsplot._style.panels", "index"),
    "fig_facecolor": ("gsplot._style.themes", "fig_facecolor"),
    "legend": ("gsplot._compat.root_api", "legend"),
    "legends": ("gsplot._style.legends", "legends"),
    "legend_entries": ("gsplot._style.legends", "legend_entries"),
    "cmap_legend": ("gsplot._style.legends", "cmap_legend"),
    "set_theme": ("gsplot._style.themes", "set_theme"),
    "paper": ("gsplot._style.paper", "paper"),
    "load_config": ("gsplot._compat.config", "load_config"),
    "read": ("gsplot._io.arrays", "read"),
    "read_array": ("gsplot._io.arrays", "read_array"),
    "write_meta": ("gsplot._io.metadata", "write_meta"),
    "build_info": ("gsplot._io.build", "build_info"),
    "Config": ("gsplot._config.model", "Config"),
    "AxisSpec": ("gsplot._core.types", "AxisSpec"),
    "Theme": ("gsplot._core.types", "Theme"),
    "InsetSpec": ("gsplot._core.types", "InsetSpec"),
    "MetadataSnapshot": ("gsplot._core.types", "MetadataSnapshot"),
    "BuildInfo": ("gsplot._core.types", "BuildInfo"),
    "LegendEntries": ("gsplot._core.types", "LegendEntries"),
    "GsplotError": ("gsplot._core.errors", "GsplotError"),
    "ConfigError": ("gsplot._core.errors", "ConfigError"),
    "DataError": ("gsplot._core.errors", "DataError"),
    "LayoutError": ("gsplot._core.errors", "LayoutError"),
    "PlotError": ("gsplot._core.errors", "PlotError"),
    "OutputError": ("gsplot._core.errors", "OutputError"),
    "MetadataError": ("gsplot._core.errors", "MetadataError"),
    "MosaicSpec": ("gsplot._core.types", "MosaicSpec"),
    "NormalizeSpec": ("gsplot._core.types", "NormalizeSpec"),
    "ColorSpec": ("gsplot._core.types", "ColorSpec"),
    "AxesTarget": ("gsplot._core.types", "AxesTarget"),
    "PerTarget": ("gsplot._core.types", "PerTarget"),
    "LineStyle": ("gsplot._core.types", "LineStyle"),
    "Marker": ("gsplot._core.types", "Marker"),
    "Unit": ("gsplot._core.types", "Unit"),
    "SizePreset": ("gsplot._core.types", "SizePreset"),
    "SizeSpec": ("gsplot._core.types", "SizeSpec"),
    "LayoutMode": ("gsplot._core.types", "LayoutMode"),
    "StyleMode": ("gsplot._core.types", "StyleMode"),
    "ZoomCorners": ("gsplot._core.types", "ZoomCorners"),
    "Limit": ("gsplot._core.types", "Limit"),
    "Scale": ("gsplot._core.types", "Scale"),
    "TickSpec": ("gsplot._core.types", "TickSpec"),
    "LabelRecord": ("gsplot._core.types", "LabelRecord"),
    "LabelRecords": ("gsplot._core.types", "LabelRecords"),
}

LEGACY_ALL: Final[tuple[str, ...]] = (
    "get_cmap",
    "load_file",
    "load_file_fast",
    "axes",
    "axes_inset",
    "axes_inset_padding",
    "get_figure_size",
    "show",
    "hello_world",
    "config_load",
    "config_dict",
    "config_entry_option",
    "home",
    "pwd",
    "pwd_move",
    "pwd_main",
    "line",
    "line_colormap_solid",
    "line_colormap_dashed",
    "scatter",
    "scatter_colormap",
    "graph_square",
    "graph_square_axes",
    "graph_white",
    "graph_white_axes",
    "graph_transparent",
    "graph_transparent_axes",
    "graph_facecolor",
    "label",
    "label_add_index",
    "legend",
    "legend_axes",
    "legend_handlers",
    "legend_reverse",
    "legend_get_handlers",
    "legend_colormap",
    "ticks_off",
    "ticks_on",
    "ticks_on_axes",
    "title",
    "title_axes",
)


def resolve_legacy(name: str) -> Any:
    """Load and return one historical root export on first use."""

    try:
        module_name, attribute_name = _LEGACY_EXPORTS[name]
    except KeyError as error:
        raise AttributeError(f"module 'gsplot' has no attribute {name!r}") from error

    module = import_module(module_name)
    return getattr(module, attribute_name)


def resolve_export(name: str) -> Any:
    """Resolve a canonical or historical root export lazily."""

    exports = _CANONICAL_EXPORTS if name in _CANONICAL_EXPORTS else _LEGACY_EXPORTS
    try:
        module_name, attribute_name = exports[name]
    except KeyError as error:
        raise AttributeError(f"module 'gsplot' has no attribute {name!r}") from error
    module = import_module(module_name)
    return getattr(module, attribute_name)


def legacy_names() -> tuple[str, ...]:
    """Return the stable historical names exposed by the root package."""

    return LEGACY_ALL


def canonical_names() -> tuple[str, ...]:
    """Return canonical root names currently implemented."""

    return tuple(_CANONICAL_EXPORTS)
