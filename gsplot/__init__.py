from .color.colormap import get_cmap

from .data.load import load_file
from .data.path import get_home, get_pwd, move_to_pwd


from .figure.axes import axes
from .figure.figure_tool import get_figure_size
from .figure.show import show

from .params.params import get_json_params

from .plot.line import line
from .plot.line_colormap import line_colormap
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
    ticks_on_by_axis,
    ticks_x,
    ticks_y,
    ticks_all,
)


__all__ = [
    # color/colormap.py
    "get_cmap",
    # data/load.py
    "load_file",
    # data/path.py
    "get_home",
    "get_pwd",
    "move_to_pwd",
    # figure/axes.py
    "axes",
    # figure/figure_tool.py
    "get_figure_size",
    # figure/show.py
    "show",
    # params/params.py
    "get_json_params",
    # plot/line.py
    "line",
    # plot/line_colormap.py
    "line_colormap",
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
    "ticks_on_by_axis",
    "ticks_x",
    "ticks_y",
    "ticks_all",
]
