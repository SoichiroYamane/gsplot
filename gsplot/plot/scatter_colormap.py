from typing import Any

import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from numpy.typing import ArrayLike, NDArray

from ..base.base import CreateClassParams, ParamsGetter, bind_passed_params
from ..base.base_alias_validator import AliasValidator
from ..figure.axes_range_base import AxesRangeSingleton
from ..style.legend_colormap import LegendColormap

__all__: list[str] = ["scatter_colormap"]


class ScatterColormap:
    """
    A class for creating scatter plots with colormap-based coloring on a specified Matplotlib axis.

    Parameters
    --------------------
    ax : matplotlib.axes.Axes
        The target axis for the scatter plot.
    x : ArrayLike
        The x-coordinates of the scatter points.
    y : ArrayLike
        The y-coordinates of the scatter points.
    cmapdata : ArrayLike
        The data used to determine the color of the scatter points.
    size : int or float, optional
        Size of the scatter points (default is 1).
    cmap : str, optional
        The name of the colormap to use (default is "viridis").
    vmin : int or float, optional
        The minimum value of the colormap scale (default is 0).
    vmax : int or float, optional
        The maximum value of the colormap scale (default is 1).
    alpha : int or float, optional
        Opacity of the scatter points (default is 1).
    label : str or None, optional
        Label for the colormap, used in legends (default is None).
    **kwargs : Any
        Additional keyword arguments passed to the `scatter` method of Matplotlib's `Axes`.

    Attributes
    --------------------
    x : numpy.ndarray
        The x-coordinates as a NumPy array.
    y : numpy.ndarray
        The y-coordinates as a NumPy array.
    cmapdata : numpy.ndarray
        The colormap data as a NumPy array.
    cmap_norm : numpy.ndarray
        Normalized colormap data.
    vmin : float
        The minimum value of the colormap scale.
    vmax : float
        The maximum value of the colormap scale.

    Methods
    --------------------
    add_legend_colormap() -> None
        Adds a colormap legend to the plot, if a label is provided.
    get_cmap_norm() -> numpy.ndarray
        Normalizes the colormap data to a range of [0, 1].
    plot() -> matplotlib.collections.PathCollection
        Creates and plots the scatter points with colormap-based coloring.

    Examples
    --------------------
    >>> x = [1, 2, 3, 4]
    >>> y = [10, 20, 15, 25]
    >>> cmapdata = [0.1, 0.5, 0.3, 0.9]
    >>> scatter = ScatterColormap(ax=ax, x=x, y=y, cmapdata=cmapdata, cmap="plasma")
    >>> scatter.plot()
    """

    def __init__(
        self,
        ax: Axes,
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
        self.ax: Axes = ax
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

    def add_legend_colormap(self) -> None:
        """
        Adds a colormap legend to the plot.

        If a label is provided, this method creates a colormap legend with stripes
        corresponding to the colormap data.

        Notes
        --------------------
        The legend is created using the `LegendColormap` class.

        Examples
        --------------------
        >>> scatter = ScatterColormap(ax=ax, x=[1, 2], y=[3, 4], cmapdata=[0.1, 0.9], label="Intensity")
        >>> scatter.add_legend_colormap()
        """
        if self.label is not None:
            LegendColormap(
                ax=self.ax,
                cmap=self.cmap,
                label=self.label,
                num_stripes=len(self.cmapdata),
            ).legend_colormap()

    def get_cmap_norm(self) -> NDArray[Any]:
        """
        Normalizes the colormap data to a range of [0, 1].

        The normalization is based on the minimum and maximum values of the colormap data.

        Returns
        --------------------
        numpy.ndarray
            Normalized colormap data.

        Examples
        --------------------
        >>> scatter = ScatterColormap(ax=ax, x=[1, 2], y=[3, 4], cmapdata=[0.1, 0.9])
        >>> scatter.get_cmap_norm()
        array([0. , 1.])
        """
        cmapdata_max = max(self.cmapdata)
        cmapdata_min = min(self.cmapdata)
        cmap_norm: NDArray[Any] = (self.cmapdata - cmapdata_min) / (
            cmapdata_max - cmapdata_min
        )
        return cmap_norm

    @AxesRangeSingleton.update
    def plot(self) -> PathCollection:
        """
        Plots the scatter points with colormap-based coloring.

        This method uses the normalized colormap data to assign colors to the scatter points
        and creates the plot on the specified axis.

        Returns
        --------------------
        matplotlib.collections.PathCollection
            The scatter plot as a PathCollection object.

        Notes
        --------------------
        - This method is decorated with `@AxesRangeSingleton.update` to update the axis range with the scatter data.
        - The colormap and normalization are applied using the `cmap` and `cmap_norm` attributes.

        Examples
        --------------------
        >>> scatter = ScatterColormap(ax=ax, x=[1, 2, 3], y=[4, 5, 6], cmapdata=[0.2, 0.5, 0.8])
        >>> scatter.plot()
        <matplotlib.collections.PathCollection>
        """
        _plot = self.ax.scatter(
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


@bind_passed_params()
def scatter_colormap(
    ax: Axes,
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
    Creates a scatter plot with colormap-based coloring on the specified axis.

    This function uses the `ScatterColormap` class to generate a scatter plot with customizable
    size, colormap, and transparency.

    Parameters
    --------------------
    ax : matplotlib.axes.Axes
        The target axis for the scatter plot.
    x : ArrayLike
        The x-coordinates of the scatter points.
    y : ArrayLike
        The y-coordinates of the scatter points.
    cmapdata : ArrayLike
        The data used to determine the color of the scatter points.
    size : int or float, optional
        Size of the scatter points (default is 1).
    cmap : str, optional
        The name of the colormap to use (default is "viridis").
    vmin : int or float, optional
        The minimum value of the colormap scale (default is 0).
    vmax : int or float, optional
        The maximum value of the colormap scale (default is 1).
    alpha : int or float, optional
        Opacity of the scatter points (default is 1).
    label : str or None, optional
        Label for the colormap, used in legends (default is None).
    **kwargs : Any
        Additional keyword arguments passed to the `scatter` method of Matplotlib's `Axes`.

    Notes
    --------------------
    - This function utilizes the `ParamsGetter` to retrieve bound parameters and the `CreateClassParams` class to handle the merging of default, configuration, and passed parameters.
    - Alias validation is performed using the `AliasValidator` class.

        - 's' (size)

    Returns
    --------------------
    matplotlib.collections.PathCollection
        The scatter plot as a PathCollection object.

    Examples
    --------------------
    >>> import gsplot as gs
    >>> x = [1, 2, 3, 4]
    >>> y = [10, 20, 15, 25]
    >>> cmapdata = [0.1, 0.5, 0.3, 0.9]
    >>> gs.scatter_colormap(ax=ax, x=x, y=y, cmapdata=cmapdata, cmap="plasma", label="Data")
    <matplotlib.collections.PathCollection>
    """
    alias_map = {
        "s": "size",
    }

    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    AliasValidator(alias_map, passed_params).validate()
    class_params: dict[str, Any] = CreateClassParams(passed_params).get_class_params()

    _scatter_colormap = ScatterColormap(
        class_params["ax"],
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
