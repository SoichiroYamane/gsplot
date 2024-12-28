import numbers
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.typing import ColorType, LineStyleType, MarkerType
from numpy.typing import ArrayLike, NDArray

from ..base.base import CreateClassParams, ParamsGetter, bind_passed_params
from ..base.base_alias_validator import AliasValidator
from ..figure.axes_range_base import AxesRangeSingleton
from .line_base import AutoColor, NumLines

__all__: list[str] = ["line"]


class Line:
    """
    A utility class for creating and plotting a line on a specified axis.

    This class manages line properties such as color, markers, and styles, and provides a method to plot the line on a specified Matplotlib axis.

    Parameters
    --------------------
    ax : matplotlib.axes.Axes
        The target axis where the line should be plotted.
    x : ArrayLike
        The x-coordinates of the data points.
    y : ArrayLike
        The y-coordinates of the data points.
    color : ColorType, optional
        The color of the line (default is None, which uses the auto color).
    marker : MarkerType, optional
        The marker style (default is "o").
    markersize : int or float, optional
        The size of the marker (default is 7.0).
    markeredgewidth : int or float, optional
        The width of the marker edge (default is 1.5).
    markeredgecolor : ColorType, optional
        The color of the marker edge (default is None, which uses the line color).
    markerfacecolor : ColorType, optional
        The color of the marker face (default is None, which uses the line color with modified alpha).
    linestyle : LineStyleType, optional
        The line style (default is "--").
    linewidth : int or float, optional
        The width of the line (default is 1.0).
    alpha : int or float, optional
        The opacity of the line (default is 1.0).
    alpha_mfc : int or float, optional
        The opacity of the marker face color (default is 0.2).
    label : str, optional
        The label for the line (default is None).
    *args : Any
        Additional positional arguments passed to `Axes.plot`.
    **kwargs : Any
        Additional keyword arguments passed to `Axes.plot`.

    Methods
    --------------------
    plot()
        Plots the line on the specified axis.

    Examples
    --------------------
    >>> line = Line(axis_target=0, x=[0, 1, 2], y=[2, 4, 6], color="red", linestyle="-")
    >>> line.plot()
    """

    def __init__(
        self,
        ax: Axes,
        x: ArrayLike,
        y: ArrayLike,
        color: ColorType | None = None,
        marker: MarkerType = "o",
        markersize: int | float = 7.0,
        markeredgewidth: int | float = 1.5,
        markeredgecolor: ColorType | None = None,
        markerfacecolor: ColorType | None = None,
        linestyle: LineStyleType = "--",
        linewidth: int | float = 1.0,
        alpha: int | float = 1.0,
        alpha_mfc: int | float = 0.2,
        label: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:

        self.ax: Axes = ax

        self._x: ArrayLike = x
        self._y: ArrayLike = y

        self.color: ColorType | None = color
        self.marker: MarkerType = marker
        self.markersize: int | float = markersize
        self.markeredgewidth: int | float = markeredgewidth
        self.markeredgecolor: ColorType | None = markeredgecolor
        self.markerfacecolor: ColorType | None = markerfacecolor
        self.linestyle: LineStyleType = linestyle
        self.linewidth: int | float = linewidth
        self.alpha: int | float = alpha
        self.alpha_mfc: int | float = alpha_mfc
        self.label: str | None = label
        self.args: Any = args
        self.kwargs: Any = kwargs

        # Ensure x and y data are NumPy arrays
        self.x: NDArray[Any] = np.array(self._x)
        self.y: NDArray[Any] = np.array(self._y)

        self._set_colors()

    def _set_colors(self) -> None:
        """
        Sets the colors for the line, marker edge, and marker face.
        """
        cycle_color: NDArray[Any] | str = AutoColor(self.ax).get_color()
        if isinstance(cycle_color, np.ndarray):
            cycle_color = colors.to_hex(
                tuple(cycle_color)
            )  # convert numpy array to tuple

        default_color: ColorType = cycle_color if self.color is None else self.color

        self._color = self._modify_color_alpha(default_color, self.alpha)
        self._color_mec = self._modify_color_alpha(
            self.markeredgecolor if self.markeredgecolor is not None else default_color,
            self.alpha,
        )
        self._color_mfc = self._modify_color_alpha(
            self.markerfacecolor if self.markerfacecolor is not None else default_color,
            self.alpha_mfc * self.alpha,
        )

    def _modify_color_alpha(self, color: ColorType, alpha: float | int | None) -> tuple:
        """
        Modifies the alpha value of the given color.

        Parameters
        --------------------
        color : ColorType
            The base color.
        alpha : float or int or None
            The alpha value to apply.

        Returns
        --------------------
        tuple
            The RGBA color with the modified alpha value.

        Raises
        --------------------
        ValueError
            If `color` or `alpha` is None, or if `alpha` is not a float.
        """
        if color is None or alpha is None:
            raise ValueError("Both color and alpha must be provided")

        if not isinstance(alpha, numbers.Real):
            raise ValueError("Alpha must be a float")

        rgb = list(colors.to_rgba(color))
        rgb[3] = float(alpha)
        return tuple(rgb)

    @NumLines.count
    @AxesRangeSingleton.update
    def plot(self) -> list[Line2D]:
        """
        Plots the line on the specified axis.

        Returns
        --------------------
        list of matplotlib.lines.Line2D
            The list of Line2D objects representing the plotted line.

        Examples
        --------------------
        >>> line = Line(axis_target=0, x=[0, 1, 2], y=[2, 4, 6], color="blue")
        >>> line.plot()
        """
        _plot = self.ax.plot(
            self.x,
            self.y,
            color=self._color,
            marker=self.marker,
            markersize=self.markersize,
            markeredgewidth=self.markeredgewidth,
            linestyle=self.linestyle,
            linewidth=self.linewidth,
            markeredgecolor=self._color_mec,
            markerfacecolor=self._color_mfc,
            label=self.label,
            *self.args,
            **self.kwargs,
        )
        return _plot


@bind_passed_params()
def line(
    ax: Axes,
    x: ArrayLike,
    y: ArrayLike,
    color: ColorType | None = None,
    marker: MarkerType = "o",
    markersize: int | float = 7.0,
    markeredgewidth: int | float = 1.5,
    markeredgecolor: ColorType | None = None,
    markerfacecolor: ColorType | None = None,
    linestyle: LineStyleType = "--",
    linewidth: int | float = 1.0,
    alpha: int | float = 1,
    alpha_mfc: int | float = 0.2,
    label: str | None = None,
    *args: Any,
    **kwargs: Any,
) -> list[Line2D]:
    """
    A convenience function to plot a line with extensive customization on a Matplotlib axis.

    This function wraps the `Line` class for easier usage and provides support for aliasing
    common parameters. It handles axis resolution, automatic color cycling, and parameter validation.

    Parameters
    --------------------
    ax : matplotlib.axes.Axes
        The target axis where the line should be plotted.
    x : ArrayLike
        The x-coordinates of the line data.
    y : ArrayLike
        The y-coordinates of the line data.
    color : ColorType or None, optional
        The color of the line (default is `None`, using auto color cycling).
    marker : MarkerType, optional
        The marker style for the data points (default is "o").
    markersize : int or float, optional
        The size of the markers (default is 7.0).
    markeredgewidth : int or float, optional
        The width of the marker edges (default is 1.5).
    markeredgecolor : ColorType or None, optional
        The edge color of the markers (default is `None`).
    markerfacecolor : ColorType or None, optional
        The face color of the markers (default is `None`).
    linestyle : LineStyleType, optional
        The style of the line (default is "--").
    linewidth : int or float, optional
        The width of the line (default is 1.0).
    alpha : int or float, optional
        The transparency level of the line (default is 1).
    alpha_mfc : int or float, optional
        The transparency level of the marker face color (default is 0.2).
    label : str or None, optional
        The label for the line, used in legends (default is `None`).
    *args : Any
        Additional positional arguments passed to `matplotlib.axes.Axes.plot`.
    **kwargs : Any
        Additional keyword arguments passed to `matplotlib.axes.Axes.plot`.

    Notes
    --------------------
    - This function utilizes the `ParamsGetter` to retrieve bound parameters and the `CreateClassParams` class to handle the merging of default, configuration, and passed parameters.
    - Alias validation is performed using the `AliasValidator` class.

        - 'ms' (markersize)
        - 'mew' (markeredgewidth)
        - 'ls' (linestyle)
        - 'lw' (linewidth)
        - 'c' (color)
        - 'mec' (markeredgecolor)
        - 'mfc' (markerfacecolor).

    Returns
    --------------------
    list of matplotlib.lines.Line2D
        The list of Line2D objects representing the plotted line.

    Examples
    --------------------
    >>> import gsplot as gs
    >>> x = [0, 1, 2, 3]
    >>> y = [1, 2, 3, 4]
    >>> line_plot = gs.line(ax, x, y, color="blue", linestyle="-")
    >>> print(line_plot)
    [<matplotlib.lines.Line2D object at 0x...>]
    """

    alias_map = {
        "ms": "markersize",
        "mew": "markeredgewidth",
        "ls": "linestyle",
        "lw": "linewidth",
        "c": "color",
        "mec": "markeredgecolor",
        "mfc": "markerfacecolor",
    }

    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    AliasValidator(alias_map, passed_params).validate()
    class_params: dict[str, Any] = CreateClassParams(passed_params).get_class_params()

    _line = Line(
        class_params["ax"],
        class_params["x"],
        class_params["y"],
        class_params["color"],
        class_params["marker"],
        class_params["markersize"],
        class_params["markeredgewidth"],
        class_params["markeredgecolor"],
        class_params["markerfacecolor"],
        class_params["linestyle"],
        class_params["linewidth"],
        class_params["alpha"],
        class_params["alpha_mfc"],
        class_params["label"],
        *class_params["args"],
        **class_params["kwargs"],
    )

    return _line.plot()
