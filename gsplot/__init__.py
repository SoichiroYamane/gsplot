import matplotlib.pyplot as plt

from .color.colormap import get_cmap

from .data.load import load_file

from .figure.axes import axes
from .figure.figure_tools import get_figure_size
from .figure.show import show

from .config.config import config_load, config_dict, config_entry_option

from .path.path import home, pwd, pwd_move

from .plot.line import line
from .plot.line_colormap_solid import line_colormap_solid
from .plot.line_colormap_dashed import line_colormap_dashed
from .plot.scatter import scatter
from .plot.scatter_colormap import scatter_colormap


from .style.graph import graph_square, graph_square_all
from .style.graph import (
    graph_white,
    graph_white_all,
    graph_white_axis,
    graph_white_axis_all,
    graph_transparent,
    graph_transparent_all,
)

from .style.label import label
from .style.label import label_add_index

from .style.legend import legend, legend_handlers, legend_reverse, legend_get_handlers
from .style.legend_colormap import legend_colormap
from .style.ticks import (
    ticks_off,
    ticks_on,
    ticks_all,
)
from .config.config import Config

# install()
# ╭──────────────────────────────────────────────────────────╮
# │ Load the configuration file                              │
# ╰──────────────────────────────────────────────────────────╯
Config()

# !TODO: remove passed_variables
# !TODO modify args
# !TODO modify NDArray hint


__all__ = [
    # color/colormap.py
    "get_cmap",
    # data/load.py
    "load_file",
    # figure/axes.py
    "axes",
    # figure/figure_tools.py
    "get_figure_size",
    # figure/show.py
    "show",
    # config/config.py
    "config_load",
    "config_dict",
    "config_entry_option",
    # path/path.py
    "home",
    "pwd",
    "pwd_move",
    # plot/line.py
    "line",
    # plot/line_colormap.py
    "line_colormap",
    # plot/line_colormap_solid.py
    "line_colormap_solid",
    # plot/line_colormap_dashed.py
    "line_colormap_dashed",
    # plot/scatter.py
    "scatter",
    # plot/scatter_colormap.py
    "scatter_colormap",
    # style/graph.py
    "graph_square",
    "graph_square_all",
    "graph_white",
    "graph_white_all",
    "graph_white_axis",
    "graph_white_axis_all",
    "graph_transparent",
    "graph_transparent_all",
    # style/label.py
    "label",
    "label_add_index",
    # style/legend.py
    "legend",
    "legend_handlers",
    "legend_reverse",
    "legend_get_handlers",
    # style/legend_colormap.py
    "legend_colormap",
    # style/ticks.py
    "ticks_off",
    "ticks_on",
    "ticks_all",
]
