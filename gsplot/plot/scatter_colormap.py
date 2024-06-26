from ..params.params import Params
from ..base.base import AttributeSetter
from ..plts.axes import AxesSingleton, AxesRangeSingleton
from ..style.legend_colormap import LegendColormap

import numpy as np


class ScatterColormap:
    def __init__(
        self,
        axis_index: int,
        xdata: np.ndarray,
        ydata: np.ndarray,
        cmapdata: np.ndarray,
        label=None,
        *args,
        **kwargs,
    ):
        self.axis_index = axis_index
        self.xdata = np.array(xdata)
        self.ydata = np.array(ydata)
        self.cmapdata = np.array(cmapdata)
        self.label = label

        self.cmap_norm = self._get_cmap_norm()

        kwargs = self._handle_kwargs(kwargs)
        params = self._handle_kwargs(Params().getitem("scatter_colormap"))

        defaults = self._get_defaults(kwargs)
        attribute_setter = AttributeSetter(defaults, params, **kwargs)

        self._args = args
        self._kwargs = attribute_setter.set_attributes(self)

        self.__axes = AxesSingleton()
        self._axes = self.__axes.axes
        self.axis = self._axes[self.axis_index]

    def _handle_kwargs(self, kwargs):
        alias_map = {
            "s": "size",
            "c": "color",
        }
        for alias, key in alias_map.items():
            if alias in kwargs:
                if key in kwargs:
                    raise ValueError(f"Both '{alias}' and '{key}' are in kwargs.")
                kwargs[key] = kwargs[alias]
                del kwargs[alias]
        return kwargs

    def _get_defaults(self, kwargs):
        return {
            "size": 1,
            "cmap": "viridis",
            "vmin": 0,
            "vmax": 1,
            "alpha": 1,
        }

    def _get_cmap_norm(self):
        cmapdata_max = max(self.cmapdata)
        cmapdata_min = min(self.cmapdata)
        cmap_norm = (self.cmapdata - cmapdata_min) / (cmapdata_max - cmapdata_min)
        return cmap_norm

    @AxesRangeSingleton.update
    def plot(self):
        self.axis.scatter(
            self.xdata,
            self.ydata,
            s=self.size,
            c=self.cmap_norm,
            cmap=self.cmap,
            vmin=self.vmin,
            vmax=self.vmax,
            alpha=self.alpha,
            *self._args,
            **self._kwargs,
        )
        pass

    #! Bad statement of args and kwargs
    # TODO: Fix this part
    def _set_legend(self):
        NUM_STRIPES = 100
        if self.label is not None:
            LegendColormap(
                axis_index=self.axis_index,
                cmap=self.cmap,
                label=self.label,
                num_stripes=NUM_STRIPES,
            ).add_legend_colormap()


# def Yama_colormap_plot(
#     plts_i,
#     datax,
#     datay,
#     colordata,
#     s=1,
#     cmap="viridis",
#     zorder=0,
#     alpha=1,
#     *args,
#     **kwargs,
# ):
#     cl_max = max(colordata)
#     cl_min = min(colordata)
#     cl_data = colordata
#     color_bar = (cl_data - cl_min) / (cl_max - cl_min)
#     plts_i.scatter(
#         datax,
#         datay,
#         c=color_bar,
#         cmap=cmap,
#         vmin=min(color_bar),
#         vmax=max(color_bar),
#         alpha=alpha,
#         s=s,
#         zorder=zorder,
#         *args,
#         **kwargs,
#     )
