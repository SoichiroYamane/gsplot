from typing import Any

import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from numpy.typing import ArrayLike, NDArray

from ..base.base import CreateClassParams, ParamsGetter, bind_passed_params
from ..base.base_alias_validator import AliasValidator
from ..figure.axes_base import AxesRangeSingleton, AxesResolver
from ..style.legend_colormap import LegendColormap


class ScatterColormap:
    def __init__(
        self,
        axis_target: int | Axes,
        x: ArrayLike,
        y: ArrayLike,
        cmapdata: ArrayLike,
        size: int | float = 1,
        cmap: str = "viridis",
        vmin: int | float = 0,
        vmax: int | float = 1,
        alpha: int | float = 1,
        label: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.axis_target: int | Axes = axis_target

        self.axis_index: int = AxesResolver(self.axis_target).axis_index
        self.axis: Axes = AxesResolver(self.axis_target).axis

        self._x: ArrayLike = x
        self._y: ArrayLike = y
        self._cmapdata: ArrayLike = cmapdata
        self.size: int | float = size
        self.cmap: str = cmap
        self._vmin: int | float = vmin
        self._vmax: int | float = vmax
        self.alpha: int | float = alpha
        self.label: str | None = label
        self.kwargs: Any = kwargs

        self.x: NDArray[Any] = np.array(self._x)
        self.y: NDArray[Any] = np.array(self._y)
        self.cmapdata: NDArray[Any] = np.array(self._cmapdata)
        self.vmin: float = float(self._vmin)
        self.vmax: float = float(self._vmax)

        self.cmap_norm: NDArray[Any] = self.get_cmap_norm()

        if self.label is not None:
            self.add_legend_colormap()

    def add_legend_colormap(self):

        if self.label is not None:
            LegendColormap(
                axis_target=self.axis_target,
                cmap=self.cmap,
                label=self.label,
                num_stripes=len(self.cmapdata),
            ).legend_colormap()

    def get_cmap_norm(self) -> NDArray[Any]:

        cmapdata_max = max(self.cmapdata)
        cmapdata_min = min(self.cmapdata)
        cmap_norm: NDArray[Any] = (self.cmapdata - cmapdata_min) / (
            cmapdata_max - cmapdata_min
        )
        return cmap_norm

    @AxesRangeSingleton.update
    def plot(self) -> PathCollection:

        _plot = self.axis.scatter(
            x=self.x,
            y=self.y,
            s=self.size,
            c=self.cmap_norm,
            cmap=self.cmap,
            vmin=self.vmin,
            vmax=self.vmax,
            alpha=self.alpha,
            **self.kwargs,
        )
        return _plot


# TODO: modify the docstring
@bind_passed_params()
def scatter_colormap(
    axis_target: int | Axes,
    x: ArrayLike,
    y: ArrayLike,
    cmapdata: ArrayLike,
    size: int | float = 1,
    cmap: str = "viridis",
    vmin: int | float = 0,
    vmax: int | float = 1,
    alpha: int | float = 1,
    label: str | None = None,
    **kwargs: Any,
) -> PathCollection:
    """
    Create a scatter plot with a colormap applied to the points.

    This function creates a scatter plot where the color of each point is determined
    by the values in `cmapdata` and mapped to the specified colormap. Additional
    customization options for size, transparency, and labels are provided.

    Parameters
    ----------
    axis_target : int or Axes
        The target axis where the scatter plot will be created. Can be an integer
        index of the axis or an `Axes` instance.
    x : ArrayLike
        The x-coordinates of the data points.
    y : ArrayLike
        The y-coordinates of the data points.
    cmapdata : ArrayLike
        The data values used to map colors to the points.
    size : int or float, optional
        The size of the points. Default is 1.
    cmap : str, optional
        The name of the colormap to use. Default is "viridis".
    vmin : int or float, optional
        The minimum value for the colormap. Data values smaller than this will be
        clamped to `vmin`. Default is 0.
    vmax : int or float, optional
        The maximum value for the colormap. Data values larger than this will be
        clamped to `vmax`. Default is 1.
    alpha : int or float, optional
        The transparency of the points. Value should be between 0 (transparent) and 1
        (opaque). Default is 1.
    label : str or None, optional
        The label for the scatter plot, used in legends. Default is None.
    **kwargs : Any
        Additional keyword arguments passed to the `ScatterColormap` class for further
        customization.

    Returns
    -------
    PathCollection
        A Matplotlib `PathCollection` object representing the scatter plot.

    Notes
    -----
    - This function uses the `ScatterColormap` class for plotting and customization.
    - Data values in `cmapdata` are mapped to the colormap using `vmin` and `vmax`.
    - Aliases for parameters are supported (e.g., "s" for "size").

    Examples
    --------
    Create a scatter plot with a colormap applied:

    >>> import numpy as np
    >>> x = np.linspace(0, 10, 100)
    >>> y = np.sin(x)
    >>> cmapdata = np.abs(y)  # Map colors based on the absolute value of y
    >>> scatter_colormap(axis_target=0, x=x, y=y, cmapdata=cmapdata)

    Customize the colormap and point size:

    >>> scatter_colormap(axis_target=0, x=x, y=y, cmapdata=cmapdata,
    ...                  cmap="plasma", size=10)

    Adjust colormap range with `vmin` and `vmax`:

    >>> scatter_colormap(axis_target=0, x=x, y=y, cmapdata=cmapdata,
    ...                  vmin=0.2, vmax=0.8)

    Add transparency and a label:

    >>> scatter_colormap(axis_target=0, x=x, y=y, cmapdata=cmapdata,
    ...                  alpha=0.5, label="My Data")
    """

    alias_map = {
        "s": "size",
    }

    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    AliasValidator(alias_map, passed_params).validate()
    class_params: dict[str, Any] = CreateClassParams(passed_params).get_class_params()

    _scatter_colormap = ScatterColormap(
        class_params["axis_target"],
        class_params["x"],
        class_params["y"],
        class_params["cmapdata"],
        class_params["size"],
        class_params["cmap"],
        class_params["vmin"],
        class_params["vmax"],
        class_params["alpha"],
        class_params["label"],
        **class_params["kwargs"],
    )
    return _scatter_colormap.plot()
