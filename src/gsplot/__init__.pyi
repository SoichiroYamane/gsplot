from __future__ import annotations

from typing import Any

from ._compat.config import load_config as load_config
from ._config.model import Config as Config
from ._core.errors import ConfigError as ConfigError
from ._core.errors import DataError as DataError
from ._core.errors import GsplotError as GsplotError
from ._core.errors import LayoutError as LayoutError
from ._core.errors import MetadataError as MetadataError
from ._core.errors import OutputError as OutputError
from ._core.errors import PlotError as PlotError
from ._core.types import AxesDict as AxesDict
from ._core.types import AxesTarget as AxesTarget
from ._core.types import AxisSpec as AxisSpec
from ._core.types import BuildInfo as BuildInfo
from ._core.types import ColorSpec as ColorSpec
from ._core.types import InsetSpec as InsetSpec
from ._core.types import LabelRecord as LabelRecord
from ._core.types import LabelRecords as LabelRecords
from ._core.types import LayoutMode as LayoutMode
from ._core.types import LegendEntries as LegendEntries
from ._core.types import Limit as Limit
from ._core.types import LineStyle as LineStyle
from ._core.types import Marker as Marker
from ._core.types import MetadataSnapshot as MetadataSnapshot
from ._core.types import MosaicSpec as MosaicSpec
from ._core.types import NormalizeSpec as NormalizeSpec
from ._core.types import PerTarget as PerTarget
from ._core.types import Scale as Scale
from ._core.types import SizePreset as SizePreset
from ._core.types import SizeSpec as SizeSpec
from ._core.types import StyleMode as StyleMode
from ._core.types import Theme as Theme
from ._core.types import TickSpec as TickSpec
from ._core.types import Unit as Unit
from ._core.types import ZoomCorners as ZoomCorners
from ._figure.backend import use_backend as use_backend
from ._figure.inset import inset as inset
from ._figure.inset import inset_axes as inset_axes
from ._figure.layout import subplots as subplots
from ._figure.output import save as save
from ._figure.output import savefig as savefig
from ._figure.output import show as show
from ._io.arrays import read as read
from ._io.arrays import read_array as read_array
from ._io.build import build_info as build_info
from ._io.metadata import write_meta as write_meta
from ._plot.basic import line as line
from ._plot.basic import scatter as scatter
from ._plot.colored import cmap_dash as cmap_dash
from ._plot.colored import cmap_line as cmap_line
from ._plot.colored import cmap_scatter as cmap_scatter
from ._plot.colormap import colors as colors
from ._plot.colormap import sample_cmap as sample_cmap
from ._style.axes import box_aspect as box_aspect
from ._style.axes import label as label
from ._style.axes import minor_ticks as minor_ticks
from ._style.axes import square as square
from ._style.axes import style_axes as style_axes
from ._style.axes import suptitle as suptitle
from ._style.axes import title as title
from ._style.legends import cmap_legend as cmap_legend
from ._style.legends import legend as legend
from ._style.legends import legend_entries as legend_entries
from ._style.legends import legends as legends
from ._style.panels import index as index
from ._style.panels import panel_labels as panel_labels
from ._style.paper import paper as paper
from ._style.themes import fig_facecolor as fig_facecolor
from ._style.themes import set_theme as set_theme
from .version import __commit__ as __commit__
from .version import __version__ as __version__

# Legacy compatibility exports
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

def __getattr__(name: str) -> Any: ...
