"""Public package boundary for gsplot.

The 0.3.x names remain available through lazy compatibility adapters while
the canonical implementation is introduced in later reform slices. Importing
the package itself intentionally performs no Matplotlib, configuration,
logging, metadata-file, or backend initialization.
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
    # Runtime lookup stays lazy; these declarations keep static analyzers
    # aware of the compatibility names exported through ``__getattr__``.
    get_cmap: Any
    load_file: Any
    load_file_fast: Any
    axes: Any
    axes_inset: Any
    axes_inset_padding: Any
    get_figure_size: Any
    show: Any
    hello_world: Any
    config_load: Any
    config_dict: Any
    config_entry_option: Any
    home: Any
    pwd: Any
    pwd_move: Any
    pwd_main: Any
    line: Any
    cmap_line: Any
    cmap_dash: Any
    cmap_scatter: Any
    sample_cmap: Any
    line_colormap_solid: Any
    line_colormap_dashed: Any
    scatter: Any
    scatter_colormap: Any
    graph_square: Any
    graph_square_axes: Any
    graph_white: Any
    graph_white_axes: Any
    graph_transparent: Any
    graph_transparent_axes: Any
    graph_facecolor: Any
    label: Any
    label_add_index: Any
    legend: Any
    legend_axes: Any
    legend_handlers: Any
    legend_reverse: Any
    legend_get_handlers: Any
    legend_colormap: Any
    ticks_off: Any
    ticks_on: Any
    ticks_on_axes: Any
    title: Any
    title_axes: Any
    inset_axes: Any
    savefig: Any
    style_axes: Any
    suptitle: Any
    minor_ticks: Any
    box_aspect: Any
    panel_labels: Any
    fig_facecolor: Any
    legends: Any
    legend_entries: Any
    cmap_legend: Any
    set_theme: Any
    load_config: Any
    read_array: Any
    write_meta: Any
    build_info: Any
    Config: Any
    AxisSpec: Any
    Theme: Any
    InsetSpec: Any
    MetadataSnapshot: Any
    BuildInfo: Any
    LegendEntries: Any
    GsplotError: Any
    ConfigError: Any
    DataError: Any
    LayoutError: Any
    PlotError: Any
    OutputError: Any
    MetadataError: Any
    MosaicSpec: Any
    NormalizeSpec: Any
    ColorSpec: Any
    subplots: Any
    use_backend: Any

__all__ = [
    "subplots",
    "inset_axes",
    "line",
    "scatter",
    "cmap_line",
    "cmap_dash",
    "cmap_scatter",
    "sample_cmap",
    "style_axes",
    "title",
    "suptitle",
    "minor_ticks",
    "box_aspect",
    "panel_labels",
    "fig_facecolor",
    "legend",
    "legends",
    "legend_entries",
    "cmap_legend",
    "set_theme",
    "savefig",
    "show",
    "load_config",
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
