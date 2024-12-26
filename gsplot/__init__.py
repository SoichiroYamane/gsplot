from .color.colormap import get_cmap
from .config.config import (Config, config_dict, config_entry_option,
                            config_load, save_metadata)
from .data.load_file import load_file
from .figure.axes import axes
from .figure.figure_tools import get_figure_size
from .figure.show import show
from .hello_world.hello_world import hello_world
from .logger import logger
from .path.path import home, pwd, pwd_main, pwd_move
from .plot.line import line
from .plot.line_colormap_dashed import line_colormap_dashed
from .plot.line_colormap_solid import line_colormap_solid
from .plot.scatter import scatter
from .plot.scatter_colormap import scatter_colormap
from .style.graph import (graph_facecolor, graph_square, graph_square_axes,
                          graph_transparent, graph_transparent_axes,
                          graph_white, graph_white_axes)
from .style.label import label, label_add_index
from .style.legend import (legend, legend_axes, legend_get_handlers,
                           legend_handlers, legend_reverse)
from .style.legend_colormap import legend_colormap
from .style.ticks import ticks_off, ticks_on, ticks_on_axes
from .version import __commit__, __version__

# ╭──────────────────────────────────────────────────────────╮
# │ Load the configuration file                              │
# ╰──────────────────────────────────────────────────────────╯
Config()

# ╭──────────────────────────────────────────────────────────╮
# │ Logging setup                                            │
# ╰──────────────────────────────────────────────────────────╯
logger()

# ╭──────────────────────────────────────────────────────────╮
# │ Save Metadata                                            │
# ╰──────────────────────────────────────────────────────────╯
save_metadata()

__version__ = __version__
__commit__ = __commit__


__all__ = [
    # color/colormap.py
    "get_cmap",
    # data/load_file.py
    "load_file",
    # figure/axes.py
    "axes",
    # figure/figure_tools.py
    "get_figure_size",
    # figure/show.py
    "show",
    # hello_world.py
    "hello_world",
    # config/config.py
    "config_load",
    "config_dict",
    "config_entry_option",
    # path/path.py
    "home",
    "pwd",
    "pwd_move",
    "pwd_main",
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
    "graph_square_axes",
    "graph_white",
    "graph_white_axes",
    "graph_transparent",
    "graph_transparent_axes",
    "graph_facecolor",
    # style/label.py
    "label",
    "label_add_index",
    # style/legend.py
    "legend",
    "legend_axes",
    "legend_handlers",
    "legend_reverse",
    "legend_get_handlers",
    # style/legend_colormap.py
    "legend_colormap",
    # style/ticks.py
    "ticks_off",
    "ticks_on",
    "ticks_on_axes",
]
