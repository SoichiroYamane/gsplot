import inspect
import numbers
import numpy as np
from matplotlib import colors
from matplotlib.typing import ColorType
from functools import update_wrapper
from typing import Union, Any, List, Dict, Callable
from typing_extensions import TypedDict

from ..params.params import Params
from ..base.base import AttributeSetter
from ..figure.axes_base import AxesSingleton, AxesRangeSingleton
from .line_base import NumLines
from .line_base import AutoColor


class WrapperWithAttributes(TypedDict):
    passed_variables: dict[str, Any]


class GetPassedArgs:
    def __init__(self, func) -> None:
        update_wrapper(self, func)

        self.func = func
        self.passed_variables: Dict[str, Any] = {}

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        sig = inspect.signature(self.func)
        bound_args = sig.bind_partial(*args, **kwargs)
        bound_args.apply_defaults()
        self.passed_variables = {
            k: v
            for k, v in bound_args.arguments.items()
            if not isinstance(v, np.ndarray)
            and (v != sig.parameters[k].default)
            or (
                isinstance(v, np.ndarray) and not (v == sig.parameters[k].default).all()
            )
            or k in kwargs
        }
        return self.func(*args, **kwargs)


def get_passed_args(f: Callable) -> Callable:
    return GetPassedArgs(f)


class Plot:
    def __init__(
        self,
        axis_index: int,
        xdata: Union[List[float], np.ndarray],
        ydata: Union[List[float], np.ndarray],
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
        self.xdata: np.ndarray = np.array(xdata)
        self.ydata: np.ndarray = np.array(ydata)

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

        self.__axes = AxesSingleton()
        self._axis = self.__axes.axes

        if not 0 <= self.axis_index < len(self._axis):
            raise IndexError(
                f"axis_index {self.axis_index} is out of range. Valid axis indices are from 0 to {len(self._axis)-1}."
            )
        self.axis = self._axis[self.axis_index]

    def _handle_kwargs(self) -> None:
        alias_map = {
            "ms": "markersize",
            "mew": "markeredgewidth",
            "ls": "linestyle",
            "lw": "linewidth",
            "c": "color",
            "mec": "markeredgecolor",
            "mfc": "markerfacecolor",
        }

        # check duplicate keys in config file
        params = Params().get_item("plot")

        for alias, key in alias_map.items():
            if alias in params:
                if key in params:
                    raise ValueError(f"Both '{alias}' and '{key}' are in params.")

        #######################################
        # check duplicate keys on passed_args#
        # get default values from passed_args
        _ignore_key_list = ["axis_index", "xdata", "ydata", "args", "kwargs"]
        _passed_variables_default = self.passed_variables.copy()
        for key in _ignore_key_list:
            del _passed_variables_default[key]

        # check duplicate key in passed_variables
        for alias, key in alias_map.items():
            if alias in self.kwargs:
                if key in _passed_variables_default:
                    raise ValueError(f"Both '{alias}' and '{key}' are in kwargs.")
                _passed_variables_default[key] = self.kwargs[alias]
                del self.kwargs[alias]

        #######################################
        # decompose _kwargs_params
        _params_defaults = {}
        for alias, key in alias_map.items():
            if alias in self.kwargs_params:
                _params_defaults[key] = self.kwargs_params[alias]
                del self.kwargs_params[alias]

        #######################################
        # concatenate kwargs from passed_args and config file
        _default = _params_defaults.copy()
        _default.update(_passed_variables_default)

        _kwargs = self.kwargs_params.copy()
        _kwargs.update(self.kwargs)

        self._kwargs = _kwargs

        # set _default values as instances
        for key, value in _default.items():
            setattr(self, key, value)

    # def _set_colors(self) -> None:
    #     cycle_color = AutoColor(self.axis_index).get_color()
    #     if isinstance(cycle_color, np.ndarray):
    #         cycle_color = colors.to_hex(
    #             tuple(cycle_color)
    #         )  # convert numpy array to tuple
    #     default_color = cycle_color if self.color is None else self.color
    #
    #     self._color = self._modify_color_alpha(default_color, self.alpha_all)
    #     self._color_mec = self._modify_color_alpha(
    #         self.markeredgecolor if self.markeredgecolor is not None else default_color,
    #         self.alpha_all,
    #     )
    #     self._color_mfc = self._modify_color_alpha(
    #         self.markerfacecolor if self.markerfacecolor is not None else default_color,
    #         self.alpha * self.alpha_all,
    #     )

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
        self._handle_kwargs()
        self._set_colors()
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
def plot(
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
    Plot function with the following parameters:

    axis_index: The index of the axis on which to plot the data.
    xdata, ydata: The data to be plotted. These can be lists or numpy arrays.
    color: The color of the plot. If not specified, a default color will be used.
    marker: The marker style. Default is 'o'.
    markersize: The size of the markers. Default is 7.0.
    markeredgewidth: The width of the marker edges. Default is 1.5.
    markeredgecolor: The color of the marker edge. If not specified, a default color will be used.
    markerfacecolor: The color of the marker face. If not specified, a default color will be used.
    linestyle: The style of the line. Default is '--'.
    linewidth: The width of the line. Default is 1.0.
    alpha: The alpha blending value, between 0 (transparent) and 1 (opaque). Default is 0.2.
    alpha_all: The alpha blending value for all elements. Default is 1.0.
    label: The label for the plot. If not specified, no label will be added.
    *args, **kwargs: Additional arguments and keyword arguments to be passed to the function.
    """

    passed_variables = plot.passed_variables  # type: ignore

    line = Plot(
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

    line.plot()
