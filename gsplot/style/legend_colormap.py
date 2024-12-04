from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.legend import Legend as Lg
from matplotlib.legend_handler import HandlerBase
from matplotlib.patches import Rectangle

from ..base.base import CreateClassParams, ParamsGetter, bind_passed_params
from ..color.colormap import Colormap
from ..figure.axes_base import AxesResolver
from ..plot.line import Line
from .legend import Legend

__all__: list[str] = ["legend_colormap"]


class HandlerColormap(HandlerBase):

    def __init__(
        self,
        cmap: str,
        num_stripes: int = 8,
        vmin: int | float = 0,
        vmax: int | float = 1,
        reverse: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.cmap: str = cmap
        self.num_stripes: int = num_stripes
        self.vmin: int | float = vmin
        self.vmax: int | float = vmax
        self.reverse: bool = reverse
        self.kwargs = kwargs

    def create_artists(
        self,
        legend,
        orig_handle,
        xdescent,
        ydescent,
        width,
        height,
        fontsize,
        trans,
    ):

        stripes = []
        cmap_ndarray = np.linspace(self.vmin, self.vmax, self.num_stripes)
        cmap_list = Colormap(
            cmap=self.cmap, cmap_data=cmap_ndarray, normalize=False, reverse=False
        ).get_split_cmap()

        for i in range(self.num_stripes):
            fc = cmap_list[self.num_stripes - i - 1] if self.reverse else cmap_list[i]
            s = Rectangle(
                (xdescent + i * width / self.num_stripes, ydescent),
                width / self.num_stripes,
                height,
                fc=fc,
                transform=trans,
                **self.kwargs,
            )
            stripes.append(s)
        return stripes


class ColormapRectangle(Rectangle):
    pass


class LegendColormap:

    def __init__(
        self,
        axis_target: int | Axes,
        cmap: str = "viridis",
        label: str | None = None,
        num_stripes: int = 8,
        vmin: int | float = 0,
        vmax: int | float = 1,
        reverse: bool = False,
        **kwargs: Any,
    ):
        self.axis_target: int | Axes = axis_target
        self.cmap: str = cmap
        self.label: str | None = label
        self.num_stripes: int = num_stripes
        self.vmin: int | float = vmin
        self.vmax: int | float = vmax
        self.reverse: bool = reverse
        self.kwargs: Any = kwargs

        _axes_resolver = AxesResolver(axis_target)
        self.axis_index: int = _axes_resolver.axis_index
        self.axis: Axes = _axes_resolver.axis

        MAX_NUM_STRIPES = 256
        if self.num_stripes > MAX_NUM_STRIPES:
            self.num_stripes = MAX_NUM_STRIPES

        self.handler_colormap = HandlerColormap(
            cmap=self.cmap,
            num_stripes=self.num_stripes,
            reverse=self.reverse,
            vmin=self.vmin,
            vmax=self.vmax,
            **self.kwargs,
        )

    def get_legend_handlers_colormap(
        self,
    ) -> tuple[list[Rectangle], list[str | None], dict[Rectangle, HandlerColormap]]:

        handle = [Rectangle((0, 0), 1, 1)]
        label: list[str | None] = [self.label]

        handler: dict[Rectangle, HandlerColormap] = {handle[0]: self.handler_colormap}
        return handle, label, handler

    @staticmethod
    def create_unique_class_with_handler(base_class, handler, class_name=None):
        # Create Unique Class
        if class_name is None:
            class_name = f"Custom{base_class.__name__}_{id(handler)}"

        # Create a new class with the given handler
        UniqueClass = type(class_name, (base_class,), {})
        return UniqueClass

    def axis_patch(self):
        UniqueClass = self.create_unique_class_with_handler(
            Rectangle, self.handler_colormap
        )
        cmap_dummy_handle = UniqueClass((0, 0), 0, 0, label=self.label, visible=False)
        self.axis.add_patch(cmap_dummy_handle)
        Lg.update_default_handler_map({cmap_dummy_handle: self.handler_colormap})
        self.axis.legend(handles=[cmap_dummy_handle], labels=[self.label])

    def legend_colormap(self) -> Lg:
        self.axis_patch()
        return self.axis.legend()


# TODO: modify the docsring
@bind_passed_params()
def legend_colormap(
    axis_target: int | Axes,
    cmap: str = "viridis",
    label: str | None = None,
    num_stripes: int = 8,
    vmin: int | float = 0,
    vmax: int | float = 1,
    reverse: bool = False,
    **kwargs: Any,
) -> Lg:
    """
    Add a colormap-based legend to a specified axis.

    This function creates and adds a legend to the given axis that visually
    represents a colormap. It supports customization of the colormap, value range,
    number of stripes, and label.

    Parameters
    ----------
    axis_target : int or Axes
        The target axis where the colormap legend will be added. Can be an integer
        index of the axis or an `Axes` instance.
    cmap : str, optional
        The name of the colormap to use. Default is "viridis".
    label : str or None, optional
        The label to display alongside the legend. Default is None.
    num_stripes : int, optional
        The number of discrete stripes to display in the colormap legend. Default is 8.
    vmin : int or float, optional
        The minimum value of the colormap range. Default is 0.
    vmax : int or float, optional
        The maximum value of the colormap range. Default is 1.
    reverse : bool, optional
        If True, reverse the direction of the colormap. Default is False.
    **kwargs : Any
        Additional keyword arguments passed to the `LegendColormap` class for
        further customization.

    Returns
    -------
    Lg
        The legend object representing the colormap.

    Notes
    -----
    - This function uses the `LegendColormap` class to handle the creation and
      customization of the colormap legend.
    - The `num_stripes` parameter determines the granularity of the visual
      representation of the colormap in the legend.
    - The `reverse` parameter allows the colormap direction to be flipped.

    Examples
    --------
    Add a default colormap legend to a plot:

    >>> legend_colormap(axis_target=0)

    Customize the colormap and value range:

    >>> legend_colormap(axis_target=0, cmap="plasma", vmin=0.2, vmax=0.8)

    Add a colormap legend with a label and more stripes:

    >>> legend_colormap(axis_target=0, label="Intensity", num_stripes=16)

    Reverse the colormap direction:

    >>> legend_colormap(axis_target=0, reverse=True)
    """

    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    class_params = CreateClassParams(passed_params).get_class_params()

    _legend_colormap = LegendColormap(
        class_params["axis_target"],
        class_params["cmap"],
        class_params["label"],
        class_params["num_stripes"],
        class_params["vmin"],
        class_params["vmax"],
        class_params["reverse"],
        **class_params["kwargs"],
    )

    return _legend_colormap.legend_colormap()
