from typing import List, Union, Any, Dict
import numpy as np
from matplotlib.axes import Axes

from ..config.config import Config
from ..base.base import AttributeSetter
from ..base.base_passed_args import get_passed_args
from ..figure.axes import AxesSingleton, AxesRangeSingleton
from ..style.legend_colormap import LegendColormap


class ScatterColormap:
    """
    A class for creating and plotting scatter plots with a colormap on a specified matplotlib axis.

    The `ScatterColormap` class is designed to create scatter plots where the color of each point is determined by a colormap.
    It supports various customization options such as size, colormap range, transparency, and labels.

    Parameters
    ----------
    axis_index : int
        The index of the axis on which to plot the scatter plot.
    xdata : Union[list[float, int], np.ndarray]
        The data for the x-axis.
    ydata : Union[list[float, int], np.ndarray]
        The data for the y-axis.
    cmapdata : Union[list[float, int], np.ndarray]
        The data to be used for the colormap.
    size : Union[float, int], optional
        The size of the scatter points (default is 1).
    cmap : str, optional
        The colormap to use (default is "viridis").
    vmin : Union[float, int], optional
        The minimum value for colormap normalization (default is 0).
    vmax : Union[float, int], optional
        The maximum value for colormap normalization (default is 1).
    alpha : Union[float, int], optional
        The transparency of the scatter points (default is 1).
    label : str, optional
        The label for the scatter plot (default is None).
    passed_variables : dict[str, Any], optional
        A dictionary of additional variables passed to the scatter plot (default is an empty dictionary).
    *args : Any
        Additional positional arguments passed to the matplotlib scatter function.
    **kwargs : Any
        Additional keyword arguments passed to the matplotlib scatter function.

    Methods
    -------
    plot() -> None
        Plots the scatter plot with the colormap applied.
    """

    def __init__(
        self,
        axis_index: int,
        xdata: Union[list[float | int], np.ndarray],
        ydata: Union[list[float | int], np.ndarray],
        cmapdata: Union[list[float | int], np.ndarray],
        size: float | int = 1,
        cmap: str = "viridis",
        vmin: float | int = 0,
        vmax: float | int = 1,
        alpha: float | int = 1,
        label: str | None = None,
        passed_variables: dict[str, Any] = {},
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.axis_index: int = axis_index
        self._xdata: Union[list[float | int], np.ndarray] = xdata
        self._ydata: Union[list[float | int], np.ndarray] = ydata
        self._cmapdata: Union[list[float | int], np.ndarray] = cmapdata
        self.size: float | int = size
        self.cmap: str = cmap
        self._vmin: float | int = vmin
        self._vmax: float | int = vmax
        self.alpha: float | int = alpha
        self.label: str | None = label
        self.passed_variables: dict[str, Any] = passed_variables
        self.args: Any = args
        self.kwargs: Any = kwargs

        attributer = AttributeSetter()
        self.kwargs_params = attributer.set_attributes(
            self, locals(), key="scatter_colormap"
        )

        self.xdata: np.ndarray = np.array(self._xdata)
        self.ydata: np.ndarray = np.array(self._ydata)
        self.cmapdata: np.ndarray = np.array(self._cmapdata)
        self.vmin: float = float(self._vmin)
        self.vmax: float = float(self._vmax)

        self.cmap_norm: np.ndarray = self._get_cmap_norm()

        self._handle_kwargs()

        self.__axes: AxesSingleton = AxesSingleton()
        self._axes: list[Axes] = self.__axes.axes
        self.axis: Axes = self._axes[self.axis_index]

    # TODO: Move this function to base directory
    def _handle_kwargs(self) -> None:
        """
        Processes and validates keyword arguments for the scatter plot with colormap.

        Raises
        ------
        ValueError
            If duplicate keys are found in the configuration or passed arguments.
        """

        alias_map = {
            "s": "size",
        }

        # ╭──────────────────────────────────────────────────────────╮
        # │ check duplicate keys in config file                      │
        # ╰──────────────────────────────────────────────────────────╯
        params = Config().get_config_entry_option("scatter_colormap")

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
            "cmapdata",
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

    def _get_cmap_norm(self) -> np.ndarray:
        """
        Normalizes the colormap data to a range between 0 and 1.

        Returns
        -------
        np.ndarray
            The normalized colormap data.
        """

        cmapdata_max = max(self.cmapdata)
        cmapdata_min = min(self.cmapdata)
        cmap_norm: np.ndarray = (self.cmapdata - cmapdata_min) / (
            cmapdata_max - cmapdata_min
        )
        return cmap_norm

    @AxesRangeSingleton.update
    def plot(self):
        """
        Plots the scatter plot with the colormap applied.

        This method uses the matplotlib `scatter` function to plot the points on the axis
        specified by `axis_index`. It applies the colormap, size, transparency, and label
        settings that were configured during initialization.

        Returns
        -------
        None
        """

        self.axis.scatter(
            x=self.xdata,
            y=self.ydata,
            s=self.size,
            c=self.cmap_norm,
            cmap=self.cmap,
            vmin=self.vmin,
            vmax=self.vmax,
            alpha=self.alpha,
            **self._kwargs,
        )

    #! Bad statement of args and kwargs
    # TODO: Fix this part
    def _set_legend(self):
        """
        Sets the legend for the colormap scatter plot.

        This method creates a legend that corresponds to the colormap used in the scatter plot.

        Returns
        -------
        None
        """

        NUM_STRIPES = 100
        if self.label is not None:
            LegendColormap(
                axis_index=self.axis_index,
                cmap=self.cmap,
                label=self.label,
                num_stripes=NUM_STRIPES,
            ).add_legend_colormap()


# @get_passed_args
def scatter_colormap(
    axis_index: int,
    xdata: Union[list[float | int], np.ndarray],
    ydata: Union[list[float | int], np.ndarray],
    cmapdata: Union[list[float | int], np.ndarray],
    size: float | int = 1,
    cmap: str = "viridis",
    vmin: float | int = 0,
    vmax: float | int = 1,
    alpha: float | int = 1,
    label: str | None = None,
    *args: Any,
    **kwargs: Any,
):
    """
    Creates and plots a scatter plot with a colormap on a specified matplotlib axis.

    This function uses the `ScatterColormap` class to create a scatter plot where the color
    of each point is determined by a colormap. It supports various parameters for size, colormap
    range, transparency, and labels, and allows for additional arguments to be passed directly
    to the matplotlib `scatter` function.

    Parameters
    ----------
    axis_index : int
        The index of the axis on which to plot the scatter plot.
    xdata : Union[list[float, int], np.ndarray]
        The data for the x-axis.
    ydata : Union[list[float, int], np.ndarray]
        The data for the y-axis.
    cmapdata : Union[list[float, int], np.ndarray]
        The data to be used for the colormap.
    size : Union[float, int], optional
        The size of the scatter points (default is 1).
    cmap : str, optional
        The colormap to use (default is "viridis").
    vmin : Union[float, int], optional
        The minimum value for colormap normalization (default is 0).
    vmax : Union[float, int], optional
        The maximum value for colormap normalization (default is 1).
    alpha : Union[float, int], optional
        The transparency of the scatter points (default is 1).
    label : Union[str, None], optional
        The label for the scatter plot (default is None).
    *args : Any
        Additional positional arguments passed to the matplotlib scatter function.
    **kwargs : Any
        Additional keyword arguments passed to the matplotlib scatter function.

    Returns
    -------
    None
    """

    _scatter_colormap = scatter_colormap.passed_variables  # type: ignore

    ScatterColormap(
        axis_index,
        xdata,
        ydata,
        cmapdata,
        size,
        cmap,
        vmin,
        vmax,
        alpha,
        label,
        _scatter_colormap,
        *args,
        **kwargs,
    ).plot()
