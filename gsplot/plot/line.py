import numbers
import numpy as np
from matplotlib import colors
from matplotlib.typing import ColorType, MarkerType, LineStyleType
from matplotlib.axes import Axes
from numpy.typing import ArrayLike
from typing import Union, Any
import time

from ..config.config import Config
from ..base.base import get_passed_params, ParamsGetter, CreateClassParams
from ..base.base_alias_validator import AliasValidator
from ..figure.axes_base import AxesResolver, AxesRangeSingleton
from .line_base import NumLines
from .line_base import AutoColor


class Line:
    """
    A class for creating and plotting a line on a specified matplotlib axis.

    Parameters
    ----------
    axis_index : int
        The index of the axis on which to plot the line.
    xdata : Union[list[float, int], np.ndarray]
        The data for the x-axis.
    ydata : Union[list[float, int], np.ndarray]
        The data for the y-axis.
    color : Union[ColorType, None], optional
        The color of the line (default is None, which uses the color cycle).
    marker : Any, optional
        The marker style (default is "o").
    markersize : Union[float, int], optional
        The size of the markers (default is 7.0).
    markeredgewidth : Union[float, int], optional
        The width of the marker edges (default is 1.5).
    markeredgecolor : Union[ColorType, None], optional
        The color of the marker edges (default is None).
    markerfacecolor : Union[ColorType, None], optional
        The color of the marker faces (default is None).
    linestyle : Any, optional
        The style of the line (default is "--").
    linewidth : Union[float, int], optional
        The width of the line (default is 1.0).
    alpha : Union[float, int], optional
        The transparency of the line (default is 0.2).
    alpha_all : Union[float, int], optional
        The overall transparency affecting all elements (default is 1.0).
    label : Union[str, None], optional
        The label for the line (default is None).
    passed_variables : dict[str, Any], optional
        A dictionary of passed variables, typically used for internal tracking (default is {}).
    *args : Any
        Additional positional arguments passed to the matplotlib plot function.
    **kwargs : Any
        Additional keyword arguments passed to the matplotlib plot function.

    Attributes
    ----------
    axis : Axes
        The matplotlib axis on which the line is plotted.
    kwargs_params : dict[str, Any]
        The final set of parameters after merging with configuration and passed arguments.
    xdata : np.ndarray
        The x-axis data as a NumPy array.
    ydata : np.ndarray
        The y-axis data as a NumPy array.

    Methods
    -------
    plot()
        Plots the line on the specified axis.
    """

    def __init__(
        self,
        axis_target: int | Axes,
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
        alpha: int | float = 0.2,
        alpha_all: int | float = 1.0,
        label: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.axis_target: int | Axes = axis_target

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
        self.alpha_all: int | float = alpha_all
        self.label: str | None = label
        self.args: Any = args
        self.kwargs: Any = kwargs

        # Ensure x and y data are NumPy arrays
        self.x: np.ndarray = np.array(self._x)
        self.y: np.ndarray = np.array(self._y)

        self.axis_index: int = AxesResolver(axis_target).axis_index
        self.axis: Axes = AxesResolver(axis_target).axis
        print(self.axis_index)
        print(self.axis)

        self._set_colors()

    def _set_colors(self) -> None:
        cycle_color: Union[np.ndarray, str] = AutoColor(self.axis_index).get_color()
        if isinstance(cycle_color, np.ndarray):
            cycle_color = colors.to_hex(
                tuple(cycle_color)
            )  # convert numpy array to tuple

        default_color: ColorType = cycle_color if self.color is None else self.color

        self._color = self._modify_color_alpha(default_color, self.alpha_all)
        self._color_mec = self._modify_color_alpha(
            self.markeredgecolor if self.markeredgecolor is not None else default_color,
            self.alpha_all,
        )
        self._color_mfc = self._modify_color_alpha(
            self.markerfacecolor if self.markerfacecolor is not None else default_color,
            self.alpha * self.alpha_all,
        )

    def _modify_color_alpha(
        self, color: ColorType, alpha: Union[float, int, None]
    ) -> tuple:

        if color is None or alpha is None:
            raise ValueError("Both color and alpha must be provided")

        if not isinstance(alpha, numbers.Real):
            raise ValueError("Alpha must be a float")

        rgb = list(colors.to_rgba(color))
        rgb[3] = float(alpha)
        return tuple(rgb)

    @NumLines.count
    @AxesRangeSingleton.update
    def plot(self):
        self.axis.plot(
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


@get_passed_params()
def line(
    axis_target,
    x,
    y,
    color=None,
    marker="o",
    markersize=7.0,
    markeredgewidth=1.5,
    markeredgecolor=None,
    markerfacecolor=None,
    linestyle="--",
    linewidth=1.0,
    alpha=0.2,
    alpha_all=1.0,
    label=None,
    *args,
    **kwargs,
):
    """
    Plots a line on a specified matplotlib axis.

    This function creates a `Line` object and plots it on the specified axis. It supports various
    customization options for the line's appearance, such as color, marker style, line style, and transparency.

    Parameters
    ----------
    axis : int
        The index of the axis on which to plot the line.
    xdata : Union[list[float], np.ndarray]
        The data for the x-axis.
    ydata : Union[list[float], np.ndarray]
        The data for the y-axis.
    color : Union[str, None], optional
        The color of the line (default is None, which uses the color cycle).
    marker : Any, optional
        The marker style (default is "o").
    markersize : Union[float, int], optional
        The size of the markers (default is 7.0).
    markeredgewidth : Union[float, int], optional
        The width of the marker edges (default is 1.5).
    markeredgecolor : Union[str, None], optional
        The color of the marker edges (default is None).
    markerfacecolor : Union[str, None], optional
        The color of the marker faces (default is None).
    linestyle : Any, optional
        The style of the line (default is "--").
    linewidth : Union[float, int], optional
        The width of the line (default is 1.0).
    alpha : Union[float, int], optional
        The transparency of the line (default is 0.2).
    alpha_all : Union[float, int], optional
        The overall transparency affecting all elements (default is 1.0).
    label : Union[str, None], optional
        The label for the line (default is None).
    *args : Any
        Additional positional arguments passed to the matplotlib plot function.
    **kwargs : Any
        Additional keyword arguments passed to the matplotlib plot function.

    Returns
    -------
    None

    Notes
    -----
    The function is decorated with `get_passed_args`, which allows it to track and manage the
    arguments passed to it. This is useful for handling configuration settings and defaults
    from other sources.
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

    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_params()
    AliasValidator(alias_map, passed_params).validate()
    class_params: dict[str, Any] = CreateClassParams(passed_params).get_class_params()

    _line = Line(
        class_params["axis_target"],
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
        class_params["alpha_all"],
        class_params["label"],
        *class_params["args"],
        **class_params["kwargs"],
    )

    _line.plot()
