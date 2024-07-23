from .figure.axes import axes
from .figure.figure_tool import get_figure_size
from .figure.show import show

from .params.params import get_json_params
from .color.colormap import get_cmap


__all__ = [
    "axes",
    "get_figure_size",
    "show",
    "get_json_params",
    "get_cmap",
]
