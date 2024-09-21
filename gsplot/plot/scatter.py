from typing import List, Union, Any, Dict
import numpy as np
from matplotlib import colors
from matplotlib.axes import Axes
from matplotlib.typing import ColorType


from ..config.config import Config
from ..base.base import AttributeSetter
from ..base.base_passed_args import get_passed_args
from ..figure.axes import AxesSingleton, AxesRangeSingleton
from .line_base import NumLines
from .line_base import AutoColor


class Scatter:
    """
    A class for creating and plotting scatter plots on a specified matplotlib axis.

    The `Scatter` class handles the creation of scatter plots with various customizable
    parameters such as color, size, and transparency. It supports configuration via
    passed arguments and integrates with existing plot settings.

    Parameters
    ----------
    axis_index : int
        The index of the axis on which to plot the scatter plot.
    xdata : Union[list[float, int], np.ndarray]
        The data for the x-axis.
    ydata : Union[list[float, int], np.ndarray]
        The data for the y-axis.
    color : Union[ColorType, None], optional
        The color of the scatter points (default is None, which uses the color cycle).
    size : Union[float, int], optional
        The size of the scatter points (default is 1).
    alpha : Union[float, int], optional
        The transparency of the scatter points (default is 1).
    passed_variables : dict[str, Any], optional
        A dictionary of additional variables passed to the scatter plot (default is an empty dictionary).
    *args : Any
        Additional positional arguments passed to the matplotlib scatter function.
    **kwargs : Any
        Additional keyword arguments passed to the matplotlib scatter function.

    Methods
    -------
    plot() -> None
        Plots the scatter plot on the specified axis.
    """

    def __init__(
        self,
        axis_index: int,
        xdata: Union[list[float | int], np.ndarray],
        ydata: Union[list[float | int], np.ndarray],
        color: Union[ColorType, None] = None,
        size: float | int = 1,
        alpha: float | int = 1,
        passed_variables: dict[str, Any] = {},
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.axis_index: int = axis_index
        self._xdata: Union[list[float | int], np.ndarray] = xdata
        self._ydata: Union[list[float | int], np.ndarray] = ydata
        self.color: Union[ColorType, None] = color
        self.size: float | int = size
        self.alpha: float | int = alpha
        self.passed_variables: dict[str, Any] = passed_variables
        self.args: Any = args
        self.kwargs: Any = kwargs

        attributer = AttributeSetter()
        self.kwargs_params = attributer.set_attributes(self, locals(), key="scatter")

        self.xdata: np.ndarray = np.array(self._xdata)
        self.ydata: np.ndarray = np.array(self._ydata)

        self._handle_kwargs()
        self._set_colors()

        self.__axes: AxesSingleton = AxesSingleton()
        self._axes: list[Axes] = self.__axes.axes
        self.axis: Axes = self._axes[self.axis_index]

    # TODO: Move this function to base directory
    def _handle_kwargs(self) -> None:
        """
        Processes and validates keyword arguments for the scatter plot.

        Raises
        ------
        ValueError
            If duplicate keys are found in the configuration or passed arguments.
        """

        alias_map = {
            "s": "size",
            "c": "color",
        }

        # ╭──────────────────────────────────────────────────────────╮
        # │ check duplicate keys in config file                      │
        # ╰──────────────────────────────────────────────────────────╯
        params = Config().get_config_entry_option("scatter")

        for alias, key in alias_map.items():
            if alias in params:
                if key in params:
                    raise ValueError(f"Both '{alias}' and '{key}' are in params.")

        # ╭──────────────────────────────────────────────────────────╮
        # │ check duplicate keys on passed_args#                     │
        # │ get default values from passed_args                      │
        # ╰──────────────────────────────────────────────────────────╯
        _ignore_key_list = [
            "axis_index",
            "xdata",
            "ydata",
            "args",
            "kwargs",
        ]
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
        Sets the color for the scatter points, using the color cycle if no color is specified.
        """

        cycle_color: Union[np.ndarray, str] = AutoColor(self.axis_index).get_color()
        if isinstance(cycle_color, np.ndarray):
            cycle_color = colors.to_hex(
                tuple(cycle_color)
            )  # convert numpy array to tuple

        default_color: ColorType = cycle_color if self.color is None else self.color

        self._color: ColorType = default_color

    @NumLines.count
    @AxesRangeSingleton.update
    def plot(self) -> None:
        """
        Plots the scatter plot on the specified axis.

        This method uses the matplotlib `scatter` function to plot the points on the axis
        specified by `axis_index`. It applies the color, size, and transparency settings
        that were configured during initialization.

        Returns
        -------
        None
        """

        self.axis.scatter(
            self.xdata,
            self.ydata,
            s=self.size,
            c=self._color,
            alpha=self.alpha,
            **self._kwargs,
        )


# @get_passed_args
def scatter(
    axis_index: int,
    xdata: Union[list[float | int], np.ndarray],
    ydata: Union[list[float | int], np.ndarray],
    color: Union[ColorType, None] = None,
    size: float | int = 1,
    alpha: float | int = 1,
    *args: Any,
    **kwargs: Any,
) -> None:
    """
    Creates and plots a scatter plot on a specified matplotlib axis.

    This function uses the `Scatter` class to create a scatter plot with the specified
    data and customization options. It supports various parameters for color, size,
    and transparency, and allows for additional arguments to be passed directly to
    the matplotlib `scatter` function.

    Parameters
    ----------
    axis_index : int
        The index of the axis on which to plot the scatter plot.
    xdata : Union[list[float, int], np.ndarray]
        The data for the x-axis.
    ydata : Union[list[float, int], np.ndarray]
        The data for the y-axis.
    color : Union[ColorType, None], optional
        The color of the scatter points (default is None, which uses the color cycle).
    size : Union[float, int], optional
        The size of the scatter points (default is 1).
    alpha : Union[float, int], optional
        The transparency of the scatter points (default is 1).
    *args : Any
        Additional positional arguments passed to the matplotlib scatter function.
    **kwargs : Any
        Additional keyword arguments passed to the matplotlib scatter function.

    Returns
    -------
    None
    """

    passed_variables = scatter.passed_variables  # type: ignore

    Scatter(
        axis_index,
        xdata,
        ydata,
        color,
        size,
        alpha,
        passed_variables,
        *args,
        **kwargs,
    ).plot()
