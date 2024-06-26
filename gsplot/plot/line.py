from ..params.params import Params
from ..base.base import AttributeSetter
from ..plts.axes_base import AxesSingleton, AxesRangeSingleton
from ..color.colormap import Colormap
from .line_base import NumLines
from .line_base import AutoColor

from matplotlib import colors
import numpy as np


class Line:
    def __init__(self, axis_index, xdata, ydata, *args, **kwargs):
        self.axis_index = axis_index
        self.xdata = np.array(xdata)
        self.ydata = np.array(ydata)

        self.cycle_color = AutoColor(self.axis_index).get_color()
        kwargs = self._handle_kwargs(kwargs)
        params = self._handle_kwargs(Params().getitem("line"))

        defaults = self._get_defaults(kwargs)
        attribute_setter = AttributeSetter(defaults, params, **kwargs)

        self._args = args
        self._kwargs = attribute_setter.set_attributes(self)

        self.__axes = AxesSingleton()
        self._axis = self.__axes.axes
        # TODO: add warning if axis_index is out of range
        self.axis = self._axis[self.axis_index]
        self._set_colors()

    @NumLines.count
    @AxesRangeSingleton.update
    def plot(self):
        self.axis.plot(
            self.xdata,
            self.ydata,
            color=self._color,
            marker=self.marker,
            markersize=self.markersize,
            markeredgewidth=self.markeredgewidth,
            linestyle=self.linestyle,
            linewidth=self.linewidth,
            markeredgecolor=self._color_mec,
            markerfacecolor=self._color_mfc,
            label=self.label,
            *self._args,
            **self._kwargs,
        )

    def _handle_kwargs(self, kwargs):
        alias_map = {
            "ms": "markersize",
            "mew": "markeredgewidth",
            "ls": "linestyle",
            "lw": "linewidth",
            "c": "color",
            "mec": "markeredgecolor",
            "mfc": "markerfacecolor",
        }

        for alias, key in alias_map.items():
            if alias in kwargs:
                if key in kwargs:
                    raise ValueError(f"Both '{alias}' and '{key}' are in kwargs.")
                kwargs[key] = kwargs[alias]
                del kwargs[alias]
        return kwargs

    def _get_defaults(self, kwargs):
        default_color = self.cycle_color if "color" not in kwargs else kwargs["color"]
        return {
            "color": default_color,
            "marker": "o",
            "markersize": 7,
            "markeredgewidth": 1.5,
            "markeredgecolor": default_color,
            "markerfacecolor": default_color,
            "linestyle": "--",
            "linewidth": 1,
            "alpha": 0.2,
            "alpha_all": 1,
            "label": None,
        }

    def _set_colors(self):
        self._color = self._modify_color_alpha(self.color, self.alpha_all)
        self._color_mec = self._modify_color_alpha(self.markeredgecolor, self.alpha_all)
        self._color_mfc = self._modify_color_alpha(
            self.markerfacecolor, self.alpha * self.alpha_all
        )

    def _modify_color_alpha(self, color=None, alpha=None) -> tuple:
        rgb = list(colors.to_rgba(color))
        rgb[3] = alpha
        return tuple(rgb)
