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
from ..figure.axes_base import AxesRangeSingleton, AxesResolver
from .line_base import AutoColor, NumLines


class Line:

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
        alpha: int | float = 1.0,
        alpha_mfc: int | float = 0.2,
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
        self.alpha_mfc: int | float = alpha_mfc
        self.label: str | None = label
        self.args: Any = args
        self.kwargs: Any = kwargs

        # Ensure x and y data are NumPy arrays
        self.x: NDArray = np.array(self._x)
        self.y: NDArray = np.array(self._y)

        self.axis_index: int = AxesResolver(axis_target).axis_index
        self.axis: Axes = AxesResolver(axis_target).axis

        self._set_colors()

    def _set_colors(self) -> None:
        cycle_color: NDArray | str = AutoColor(self.axis_index).get_color()
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
        _plot = self.axis.plot(
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


# TODO: Modify docstring
@bind_passed_params()
def line(
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
    alpha: int | float = 1,
    alpha_mfc: int | float = 0.2,
    label: str | None = None,
    *args: Any,
    **kwargs: Any,
) -> list[Line2D]:
    """
    Plot a line with customized appearance on a specified axis.

    This function allows for creating and styling a line plot on a given Matplotlib
    axis. The appearance of the line, markers, and labels can be customized through
    various parameters. It supports alias validation for shorter parameter names.

    Parameters
    ----------
    axis_target : int or Axes
        The target axis where the line will be plotted. Can be an integer index of
        the axis or an `Axes` instance.
    x : ArrayLike
        The x-coordinates of the data points.
    y : ArrayLike
        The y-coordinates of the data points.
    color : ColorType or None, optional
        The color of the line. Accepts any valid Matplotlib color specification.
        Default is None.
    marker : MarkerType, optional
        The marker style for data points. Default is "o".
    markersize : int or float, optional
        The size of the markers. Default is 7.0.
    markeredgewidth : int or float, optional
        The width of the marker edges. Default is 1.5.
    markeredgecolor : ColorType or None, optional
        The color of the marker edges. Default is None.
    markerfacecolor : ColorType or None, optional
        The fill color of the markers. Default is None.
    linestyle : LineStyleType, optional
        The style of the line. Default is "--".
    linewidth : int or float, optional
        The width of the line. Default is 1.0.
    alpha : int or float, optional
        The transparency of the markers. Value should be between 0 (transparent)
        and 1 (opaque). Default is 0.2.
    alpha_all : int or float, optional
        The transparency of the entire line. Value should be between 0 and 1.
        Default is 1.0.
    label : str or None, optional
        The label for the line, used in legends. Default is None.
    *args : Any
        Additional positional arguments passed to the `plot` function.
    **kwargs : Any
        Additional keyword arguments for further customization.

    Returns
    -------
    list[Line2D]
        A list of `Line2D` objects representing the plotted line(s).

    Notes
    -----
    - This function uses the `Line` class for line plotting and customization.
    - Aliases for parameters (e.g., "ms" for "markersize", "ls" for "linestyle")
      are supported and validated through the `AliasValidator`.
    - Supports both explicit axis targeting via `Axes` and index-based axis selection.

    Examples
    --------
    Create a simple line plot:

    >>> line(axis_target=0, x=[0, 1, 2], y=[3, 4, 5])

    Customize line style and marker properties:

    >>> line(axis_target=0, x=[0, 1, 2], y=[3, 4, 5],
    ...      color="blue", linestyle="-.", marker="x", markersize=10)

    Use transparency for markers and the line:

    >>> line(axis_target=0, x=[0, 1, 2], y=[3, 4, 5],
    ...      alpha=0.5, alpha_all=0.8)

    Plot directly on a specified `Axes`:

    >>> import matplotlib.pyplot as plt
    >>> fig, ax = plt.subplots()
    >>> line(axis_target=ax, x=[0, 1, 2], y=[3, 4, 5])
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
        class_params["alpha_mfc"],
        class_params["label"],
        *class_params["args"],
        **class_params["kwargs"],
    )

    return _line.plot()
