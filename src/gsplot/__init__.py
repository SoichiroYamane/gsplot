"""Public package boundary for gsplot.

The 0.3.x names remain available through lazy compatibility adapters while
the canonical implementation is introduced in later reform slices. Importing
the package itself intentionally performs no Matplotlib, configuration,
logging, metadata-file, or backend initialization.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ._compat.root import legacy_names, resolve_legacy
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

__all__ = [
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
]


def __getattr__(name: str) -> Any:
    """Resolve a legacy root export only when user code requests it."""

    value = resolve_legacy(name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """Include lazy compatibility names in interactive discovery."""

    return sorted(set(globals()) | set(legacy_names()) | {"__commit__", "__version__"})
