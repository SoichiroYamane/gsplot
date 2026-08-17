"""Lazy public package boundary for the canonical gsplot API.

The 0.3.x names remain available through deprecated compatibility adapters.
Importing the package itself intentionally performs no Matplotlib,
configuration, logging, metadata-file, or backend initialization.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ._compat.root import canonical_names as _canonical_names
from ._compat.root import legacy_names as _legacy_names
from ._compat.root import (
    resolve_export,
)
from .version import __commit__, __version__

if TYPE_CHECKING:
    # Runtime lookup stays lazy.  Static analyzers see the canonical source
    # objects instead of an ``Any``-typed dynamic facade, so the shipped
    # ``py.typed`` marker provides useful signatures to downstream callers.
    from ._compat.config import load_config
    from ._config.model import Config
    from ._core.errors import (
        ConfigError,
        DataError,
        GsplotError,
        LayoutError,
        MetadataError,
        OutputError,
        PlotError,
    )
    from ._core.types import (
        AxesDict,
        AxesTarget,
        AxisSpec,
        BuildInfo,
        ColorSpec,
        InsetSpec,
        LabelRecord,
        LabelRecords,
        LayoutMode,
        LegendEntries,
        Limit,
        LineStyle,
        Marker,
        MetadataSnapshot,
        MosaicSpec,
        NormalizeSpec,
        PerTarget,
        Scale,
        SizePreset,
        SizeSpec,
        StyleMode,
        Theme,
        TickSpec,
        Unit,
        ZoomCorners,
    )
    from ._figure.backend import use_backend
    from ._figure.inset import inset, inset_axes
    from ._figure.layout import subplots
    from ._figure.output import save, savefig, show
    from ._io.arrays import read, read_array
    from ._io.build import build_info
    from ._io.metadata import write_meta
    from ._plot.basic import line, scatter
    from ._plot.colored import cmap_dash, cmap_line, cmap_scatter
    from ._plot.colormap import colors, sample_cmap
    from ._style.axes import (
        box_aspect,
        label,
        minor_ticks,
        square,
        style_axes,
        suptitle,
        ticks,
        title,
    )
    from ._style.legends import cmap_legend, legend, legend_entries, legends
    from ._style.panels import index, panel_labels
    from ._style.paper import paper
    from ._style.themes import fig_facecolor, set_theme

    # These are intentionally outside the canonical manifest but remain
    # discoverable for the documented compatibility window.
    get_cmap: Any
    load_file: Any
    load_file_fast: Any
    axes: Any
    axes_inset: Any
    axes_inset_padding: Any
    get_figure_size: Any
    hello_world: Any
    config_load: Any
    config_dict: Any
    config_entry_option: Any
    home: Any
    pwd: Any
    pwd_move: Any
    pwd_main: Any
    line_colormap_solid: Any
    line_colormap_dashed: Any
    scatter_colormap: Any
    graph_square: Any
    graph_square_axes: Any
    graph_white: Any
    graph_white_axes: Any
    graph_transparent: Any
    graph_transparent_axes: Any
    graph_facecolor: Any
    label_add_index: Any
    legend_axes: Any
    legend_handlers: Any
    legend_reverse: Any
    legend_get_handlers: Any
    legend_colormap: Any
    ticks_off: Any
    ticks_on: Any
    ticks_on_axes: Any
    title_axes: Any
    logger: Any
    save_metadata: Any

__all__ = [
    "subplots",
    "inset",
    "inset_axes",
    "line",
    "scatter",
    "cmap_line",
    "cmap_dash",
    "cmap_scatter",
    "colors",
    "sample_cmap",
    "style_axes",
    "label",
    "square",
    "title",
    "suptitle",
    "minor_ticks",
    "ticks",
    "box_aspect",
    "panel_labels",
    "index",
    "fig_facecolor",
    "legend",
    "legends",
    "legend_entries",
    "cmap_legend",
    "set_theme",
    "paper",
    "save",
    "savefig",
    "show",
    "load_config",
    "read",
    "read_array",
    "write_meta",
    "build_info",
    "use_backend",
    "Config",
    "AxisSpec",
    "Theme",
    "InsetSpec",
    "MetadataSnapshot",
    "BuildInfo",
    "LegendEntries",
    "GsplotError",
    "ConfigError",
    "DataError",
    "LayoutError",
    "PlotError",
    "OutputError",
    "MetadataError",
    "MosaicSpec",
    "NormalizeSpec",
    "ColorSpec",
    "AxesDict",
    "AxesTarget",
    "PerTarget",
    "LineStyle",
    "Marker",
    "Unit",
    "SizePreset",
    "SizeSpec",
    "LayoutMode",
    "StyleMode",
    "ZoomCorners",
    "Limit",
    "Scale",
    "TickSpec",
    "LabelRecord",
    "LabelRecords",
]


def __getattr__(name: str) -> Any:
    """Resolve a canonical or legacy root export only when requested."""

    value = resolve_export(name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Include lazy compatibility names in interactive discovery."""

    return sorted(
        set(globals())
        | set(_legacy_names())
        | set(_canonical_names())
        | {"__commit__", "__version__"}
    )
