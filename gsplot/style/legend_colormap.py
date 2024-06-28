from ..figure.axes import AxesSingleton
from ..color.colormap import Colormap
from .legend import Legend

from matplotlib.patches import Rectangle
from matplotlib.legend_handler import HandlerBase
import numpy as np


class HandlerColormap(HandlerBase):
    def __init__(self, cmap, num_stripes=8, min=0, max=1, reverse=False, **kw):
        HandlerBase.__init__(self, **kw)
        self.cmap = cmap
        self.num_stripes = num_stripes
        self.min = min
        self.max = max
        self.reverse = reverse

    def create_artists(
        self, legend, orig_handle, xdescent, ydescent, width, height, fontsize, trans
    ):
        stripes = []
        cmap_ndarray = np.linspace(self.min, self.max, self.num_stripes)
        cmap_list = Colormap(
            cmap=self.cmap, ndarray=cmap_ndarray, normalize=False
        ).get_split_cmap()
        # cmap_list = self.cmap(np.linspace(self.min, self.max, self.num_stripes))
        for i in range(self.num_stripes):
            if self.reverse:
                fc = cmap_list[self.num_stripes - i - 1]
            else:
                fc = cmap_list[i]
            s = Rectangle(
                [xdescent + i * width / self.num_stripes, ydescent],
                width / self.num_stripes,
                height,
                fc=fc,
                transform=trans,
            )
            stripes.append(s)
        return stripes


class LegendColormap:
    def __init__(
        self,
        axis_index,
        cmap="viridis",
        label=None,
        num_stripes=8,
        min=0,
        max=1,
        reverse=False,
        *args,
        **kwargs,
    ):
        self.axis_index = axis_index
        self.cmap = cmap
        self.label = label
        self.num_stripes = num_stripes
        self.min = min
        self.max = max
        self.reverse = reverse

        self.__axes = AxesSingleton()
        self._axis = self.__axes.axes[self.axis_index]

        self._args = args
        self._kwargs = kwargs

    def get_legend_handlers_colormap(self) -> tuple:
        handle = [Rectangle((0, 0), 1, 1)]
        label = [self.label]
        handler = HandlerColormap(
            cmap=self.cmap,
            num_stripes=self.num_stripes,
            reverse=self.reverse,
            min=self.min,
            max=self.max,
        )
        handler = {handle[0]: handler}
        return handle, label, handler

    def add_legend_colormap(self):
        handles, labels, handlers = Legend(self.axis_index).get_legend_handlers()
        handle_cmap, label_cmap, handler_cmap = self.get_legend_handlers_colormap()

        handles += handle_cmap
        labels += label_cmap
        handlers |= handler_cmap

        Legend(
            self.axis_index,
            handles=handles,
            labels=labels,
            handlers=handlers,
            *self._args,
            **self._kwargs,
        ).legend()
