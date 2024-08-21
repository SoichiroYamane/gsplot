import numbers
import numpy as np
from matplotlib import colors
from matplotlib.typing import ColorType
from typing import Union, Any, List, Dict

from ..params.params import Params
from ..base.base import AttributeSetter
from ..base.base_passed_args import get_passed_args
from ..figure.axes_base import AxesSingleton, AxesRangeSingleton
from .line_base import NumLines
from .line_base import AutoColor


class Line:
    """
    A class for creating and plotting a line on a specified matplotlib axis.

    Parameters
    ----------
    axis_index : int
        The index of the axis on which to plot the line.
    xdata : Union[List[float, int], np.ndarray]
        The data for the x-axis.
    ydata : Union[List[float, int], np.ndarray]
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
    passed_variables : Dict[str, Any], optional
        A dictionary of passed variables, typically used for internal tracking (default is {}).
    *args : Any
        Additional positional arguments passed to the matplotlib plot function.
    **kwargs : Any
        Additional keyword arguments passed to the matplotlib plot function.

    Attributes
    ----------
    axis : Axes
        The matplotlib axis on which the line is plotted.
    kwargs_params : Dict[str, Any]
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
        axis_index: int,
        xdata: Union[List[float | int], np.ndarray],
        ydata: Union[List[float | int], np.ndarray],
        color: Union[ColorType, None] = None,
        marker: Any = "o",
        markersize: Union[float, int] = 7.0,
        markeredgewidth: Union[float, int] = 1.5,
        markeredgecolor: Union[ColorType, None] = None,
        markerfacecolor: Union[ColorType, None] = None,
        linestyle: Any = "--",
        linewidth: Union[float, int] = 1.0,
        alpha: Union[float, int] = 0.2,
        alpha_all: Union[float, int] = 1.0,
        label: Union[str, None] = None,
        passed_variables: Dict[str, Any] = {},
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.axis_index: int = axis_index

        self._xdata: Union[List[float | int], np.ndarray] = xdata
        self._ydata: Union[List[float | int], np.ndarray] = ydata

        self.color: Union[ColorType, None] = color
        self.marker: Any = marker
        self.markersize: float | int = markersize
        self.markeredgewidth: float | int = markeredgewidth
        self.markeredgecolor: Union[ColorType, None] = markeredgecolor
        self.markerfacecolor: Union[ColorType, None] = markerfacecolor
        self.linestyle: Any = linestyle
        self.linewidth: float | int = linewidth
        self.alpha: float | int = alpha
        self.alpha_all: float | int = alpha_all
        self.label: Union[str, None] = label
        self.passed_variables: Dict[str, Any] = passed_variables
        self.args: Any = args
        self.kwargs: Any = kwargs

        attributer = AttributeSetter()
        self.kwargs_params = attributer.set_attributes(self, locals(), key="line")

        self.xdata: np.ndarray = np.array(self._xdata)
        self.ydata: np.ndarray = np.array(self._ydata)

        self._handle_kwargs()
        self._set_colors()

        self.__axes = AxesSingleton()
        self._axis = self.__axes.axes

        if not 0 <= self.axis_index < len(self._axis):
            raise IndexError(
                f"axis_index {self.axis_index} is out of range. Valid axis indices are from 0 to {len(self._axis)-1}."
            )
        self.axis = self._axis[self.axis_index]

    # TODO: Move this function to base directory
    def _handle_kwargs(self) -> None:
        """
        Handles and processes keyword arguments, including resolving alias conflicts and merging defaults.

        Raises
        ------
        ValueError
            If duplicate keys are found in the configuration or passed arguments.
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

        # ╭──────────────────────────────────────────────────────────╮
        # │ check duplicate keys in config file                      │
        # ╰──────────────────────────────────────────────────────────╯
        params = Params().get_item("line")

        for alias, key in alias_map.items():
            if alias in params:
                if key in params:
                    raise ValueError(f"Both '{alias}' and '{key}' are in params.")

        # ╭──────────────────────────────────────────────────────────╮
        # │ check duplicate keys on passed_args#                     │
        # │ get default values from passed_args                      │
        # ╰──────────────────────────────────────────────────────────╯
        _ignore_key_list = ["axis_index", "xdata", "ydata", "args", "kwargs"]
        _passed_variables_default = self.passed_variables.copy()
        for key in _ignore_key_list:
            del _passed_variables_default[key]

        # ╭──────────────────────────────────────────────────────────╮
        # │ check duplicate key in passed_variables                  │
        # ╰──────────────────────────────────────────────────────────╯
        for alias, key in alias_map.items():
            if alias in self.kwargs:
                if key in _passed_variables_default:
                    raise ValueError(f"Both '{alias}' and '{key}' are in kwargs.")
                _passed_variables_default[key] = self.kwargs[alias]
                del self.kwargs[alias]

        # ╭──────────────────────────────────────────────────────────╮
        # │ decompose _kwargs_params                                 │
        # ╰──────────────────────────────────────────────────────────╯
        _params_defaults = {}
        for alias, key in alias_map.items():
            if alias in self.kwargs_params:
                _params_defaults[key] = self.kwargs_params[alias]
                del self.kwargs_params[alias]

        # ╭──────────────────────────────────────────────────────────╮
        # │ concatenate kwargs from passed_args and config file      │
        # ╰──────────────────────────────────────────────────────────╯
        _default = _params_defaults.copy()
        _default.update(_passed_variables_default)

        _kwargs = self.kwargs_params.copy()
        _kwargs.update(self.kwargs)

        self._kwargs = _kwargs

        # ╭──────────────────────────────────────────────────────────╮
        # │ set _default values as instances                         │
        # ╰──────────────────────────────────────────────────────────╯
        for key, value in _default.items():
            setattr(self, key, value)

    def _set_colors(self) -> None:
        """
        Sets the colors for the line, marker edges, and marker faces, including applying alpha transparency.
        """

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
        """
        Modifies the alpha transparency of the provided color.

        Parameters
        ----------
        color : ColorType
            The color to modify.
        alpha : Union[float, int, None]
            The alpha transparency to apply.

        Returns
        -------
        tuple
            A tuple representing the RGBA color with the modified alpha.

        Raises
        ------
        ValueError
            If either the color or alpha is not provided, or if alpha is not a real number.
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
    def plot(self):
        """
        Plots the line on the specified axis.

        This method uses the matplotlib `plot` function to draw the line on the axis specified
        by `axis_index`. It applies various styles such as color, marker, linestyle, and others
        that were configured during the initialization of the `Line` object.

        The method is decorated with `NumLines.count` to track the number of lines plotted,
        and with `AxesRangeSingleton.update` to update the axis range based on the plotted data.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Notes
        -----
        This method is designed to be called automatically when plotting a line. It should not
        need to be called directly in most use cases.
        """

        self.axis.plot(
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
            *self.args,
            **self._kwargs,
        )


@get_passed_args
def line(
    axis_index: int,
    xdata: Union[List[float], np.ndarray],
    ydata: Union[List[float], np.ndarray],
    color: Union[str, None] = None,
    marker: Any = "o",
    markersize: Union[float, int] = 7.0,
    markeredgewidth: Union[float, int] = 1.5,
    markeredgecolor: Union[str, None] = None,
    markerfacecolor: Union[str, None] = None,
    linestyle: Any = "--",
    linewidth: Union[float, int] = 1.0,
    alpha: Union[float, int] = 0.2,
    alpha_all: Union[float, int] = 1.0,
    label: Union[str, None] = None,
    *args: Any,
    **kwargs: Any,
):
    """
    Plots a line on a specified matplotlib axis.

    This function creates a `Line` object and plots it on the specified axis. It supports various
    customization options for the line's appearance, such as color, marker style, line style, and transparency.

    Parameters
    ----------
    axis_index : int
        The index of the axis on which to plot the line.
    xdata : Union[List[float], np.ndarray]
        The data for the x-axis.
    ydata : Union[List[float], np.ndarray]
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
    passed_variables = line.passed_variables  # type: ignore

    _line = Line(
        axis_index,
        xdata,
        ydata,
        color,
        marker,
        markersize,
        markeredgewidth,
        markeredgecolor,
        markerfacecolor,
        linestyle,
        linewidth,
        alpha,
        alpha_all,
        label,
        passed_variables,
        *args,
        **kwargs,
    )

    _line.plot()
