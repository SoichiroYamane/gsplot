from typing import Any

import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from numpy.typing import ArrayLike, NDArray

from ..base.base import CreateClassParams, ParamsGetter, bind_passed_params
from ..base.base_alias_validator import AliasValidator
from ..figure.axes_range_base import AxesRangeSingleton
from ..style.legend_colormap import LegendColormap
from .line_colormap_base import LineColormapBase

__all__: list[str] = ["line_colormap_solid"]


class LineColormapSolid:
    """
    A class for plotting solid lines with a colormap applied along the line segments.

    This class generates a single continuous line where the color is mapped to the
    provided data using a colormap. It also supports interpolating points for smoother
    color transitions.

    Parameters
    --------------------
    ax : matplotlib.axes.Axes
        The target axis for plotting.
    x : ArrayLike
        The x-coordinates of the line.
    y : ArrayLike
        The y-coordinates of the line.
    cmapdata : ArrayLike
        Data values used to map colors to the line segments.
    cmap : str, optional
        Name of the colormap to use (default is "viridis").
    linewidth : int or float, optional
        Width of the line (default is 1).
    label : str or None, optional
        Label for the line, used in legends (default is `None`).
    interpolation_points : int or None, optional
        Number of interpolation points for smooth color transitions (default is `None`).
    **kwargs : Any
        Additional keyword arguments passed to the `LegendColormap` class.

    Attributes
    --------------------
    x : numpy.ndarray
        The x-coordinates as a NumPy array.
    y : numpy.ndarray
        The y-coordinates as a NumPy array.
    cmapdata : numpy.ndarray
        The colormap data as a NumPy array.

    Methods
    --------------------
    add_legend_colormap()
        Adds a legend entry for the colormap associated with the solid line.
    normal_interpolate_points(interpolation_points)
        Interpolates x, y, and colormap data for smoother color transitions.
    plot()
        Creates and plots the solid line with a colormap and returns the `LineCollection`.

    Examples
    --------------------
    >>> x = [0, 1, 2, 3, 4]
    >>> y = [1, 3, 2, 5, 4]
    >>> cmapdata = [0.1, 0.3, 0.6, 0.9, 1.0]
    >>> line = LineColormapSolid(ax=ax, x=x, y=y, cmapdata=cmapdata, cmap="plasma")
    >>> line.plot()
    """

    def __init__(
        self,
        ax: Axes,
        x: ArrayLike,
        y: ArrayLike,
        cmapdata: ArrayLike,
        cmap: str = "viridis",
        linewidth: int | float = 1,
        label: str | None = None,
        interpolation_points: int | None = None,
        **kwargs: Any,
    ) -> None:
        self.ax: Axes = ax
        self._x: ArrayLike = x
        self._y: ArrayLike = y
        self._cmapdata: ArrayLike = cmapdata
        self.cmap: str = cmap
        self.linewidth = linewidth
        self.label: str | None = label
        self.interpolation_points: int | None = interpolation_points

        self.kwargs: Any = kwargs

        self.x: NDArray[Any] = np.array(self._x)
        self.y: NDArray[Any] = np.array(self._y)
        self.cmapdata: NDArray[Any] = np.array(self._cmapdata)

        if self.label is not None:
            self.add_legend_colormap()

    def add_legend_colormap(self) -> None:
        """
        Adds a legend entry for the colormap associated with the solid line.

        Determines the number of stripes in the colormap based on the interpolation
        points or the colormap data length and adds a colormap patch to the legend.
        """
        if self.interpolation_points is None:
            NUM_STRIPES = len(self.cmapdata)
        else:
            NUM_STRIPES = self.interpolation_points

        # NUM_STRIPES in colormap should be subtracted by 1
        NUM_STRIPES -= 1

        LegendColormap(
            self.ax,
            self.cmap,
            self.label,
            NUM_STRIPES,
            **self.kwargs,
        ).axis_patch()

    def normal_interpolate_points(self, interpolation_points: int) -> tuple:
        """
        Interpolates x, y, and colormap data to create smoother transitions.

        Parameters
        --------------------
        interpolation_points : int
            Number of points for interpolation.

        Returns
        --------------------
        tuple
            Interpolated x-coordinates, y-coordinates, and colormap data.
        """
        xdiff = np.diff(self.x)
        ydiff = np.diff(self.y)
        distances = np.sqrt(xdiff**2 + ydiff**2)
        cumulative_distances = np.insert(np.cumsum(distances), 0, 0)
        interpolated_distances = np.linspace(
            0, cumulative_distances[-1], interpolation_points
        )

        x_interpolated = np.interp(interpolated_distances, cumulative_distances, self.x)
        y_interpolated = np.interp(interpolated_distances, cumulative_distances, self.y)

        # Interpolate cmapdata
        cmap_interpolated = np.interp(
            interpolated_distances, cumulative_distances, self.cmapdata
        )

        return x_interpolated, y_interpolated, cmap_interpolated

    @AxesRangeSingleton.update
    def plot(self) -> list[LineCollection]:
        """
        Plots the solid line with a colormap applied to its segments.

        This method interpolates points if required, creates line segments from the
        data, and applies the colormap to the segments. The resulting line collection
        is added to the axis.

        Returns
        --------------------
        list[matplotlib.collections.LineCollection]
            A list containing the single `LineCollection` object for the plotted solid line.

        Notes
        --------------------
        This method is decorated with `@AxesRangeSingleton.update` to update the axis range.
        """
        if self.interpolation_points is not None:
            self.x, self.y, self.cmapdata = self.normal_interpolate_points(
                self.interpolation_points
            )
        segments: NDArray[np.float64] = LineColormapBase()._create_segment(
            self.x, self.y
        )
        norm = LineColormapBase()._create_cmap(self.cmapdata)

        lc: LineCollection = LineCollection(
            segments.tolist(), cmap=self.cmap, norm=norm
        )
        lc.set_array(self.cmapdata)
        lc.set_linewidth(self.linewidth)
        lc.set_capstyle("projecting")
        self.ax.add_collection(lc)

        return [lc]


@bind_passed_params()
def line_colormap_solid(
    ax: Axes,
    x: ArrayLike,
    y: ArrayLike,
    cmapdata: ArrayLike,
    cmap: str = "viridis",
    linewidth: float | int = 1,
    label: str | None = None,
    interpolation_points: int | None = None,
    **kwargs: Any,
) -> list[LineCollection]:
    """
    Plots a solid line with a colormap applied along its segments.

    This function creates a solid line on the specified axis with colors mapped
    to the provided colormap data. It supports interpolation for smoother transitions
    between segments.

    Parameters
    --------------------
    ax : matplotlib.axes.Axes
        The target axis for plotting.
    x : ArrayLike
        The x-coordinates of the line.
    y : ArrayLike
        The y-coordinates of the line.
    cmapdata : ArrayLike
        Data values used to map colors to the line segments.
    cmap : str, optional
        Name of the colormap to use (default is "viridis").
    linewidth : float or int, optional
        Width of the line (default is 1).
    label : str or None, optional
        Label for the line, used in legends (default is `None`).
    interpolation_points : int or None, optional
        Number of interpolation points for smooth color transitions (default is `None`).
    **kwargs : Any
        Additional keyword arguments passed to the `LegendColormap` class.

    Notes
    --------------------
    - This function utilizes the `ParamsGetter` to retrieve bound parameters and the `CreateClassParams` class to handle the merging of default, configuration, and passed parameters.
    - Alias validation is performed using the `AliasValidator` class.

        - 'lw' (linewidth)

    Returns
    --------------------
    list[matplotlib.collections.LineCollection]
        A list containing the single `LineCollection` object for the plotted solid line.


    Examples
    --------------------
    >>> import gsplot as gs
    >>> x = [0, 1, 2, 3, 4]
    >>> y = [1, 3, 2, 5, 4]
    >>> cmapdata = [0.1, 0.3, 0.6, 0.9, 1.0]
    >>> lc_list = gs.line_colormap_solid(ax=ax, x=x, y=y, cmapdata=cmapdata, cmap="plasma")
    >>> print(len(lc_list))
    1
    """

    alias_map = {
        "lw": "linewidth",
    }

    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    AliasValidator(alias_map, passed_params).validate()
    class_params = CreateClassParams(passed_params).get_class_params()

    _line_colormap_solid: LineColormapSolid = LineColormapSolid(
        class_params["ax"],
        class_params["x"],
        class_params["y"],
        class_params["cmapdata"],
        class_params["cmap"],
        class_params["linewidth"],
        class_params["label"],
        class_params["interpolation_points"],
        **class_params["kwargs"],
    )
    return _line_colormap_solid.plot()
