from ..params.params import Params
from ..base.base import AttributeSetter
from ..plts.axes import _Axes

from .base_plot import NumLines
from .base_plot import AutoColor

from matplotlib import colors


class Line:
    def __init__(self):
        self.cycle_color = AutoColor().get_color()

    @NumLines.count
    def plot(self, axis_index, xdata, ydata, *args, **kwargs):
        self.axis_index = axis_index
        self.xdata = xdata
        self.ydata = ydata

        kwargs = self._handle_kwargs(kwargs)
        params = self._handle_kwargs(Params().getitem("line"))

        defaults = self._get_defaults(kwargs)
        attribute_setter = AttributeSetter(defaults, params, **kwargs)

        self._args = args
        self._kwargs = attribute_setter.set_attributes(self)

        self.__axes = _Axes()
        self._axis = self.__axes.axes[self.axis_index]

        self._set_colors()

        self._axis.plot(
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
        self._color = self.modify_color_alpha(self.color, self.alpha_all)
        self._color_mec = self.modify_color_alpha(self.markeredgecolor, self.alpha_all)
        self._color_mfc = self.modify_color_alpha(
            self.markerfacecolor, self.alpha * self.alpha_all
        )

    def modify_color_alpha(self, color=None, alpha=None) -> tuple:
        rgb = list(colors.to_rgba(color))
        rgb[3] = alpha
        return tuple(rgb)
