import numpy as np
from numpy.typing import NDArray
from matplotlib.axes import Axes
from matplotlib.colors import Normalize
from matplotlib.collections import LineCollection
from typing import List, Union, Any, Dict


from ..params.params import Params
from ..base.base import AttributeSetter
from ..base.base_passed_args import get_passed_args
from ..figure.axes_base import AxesSingleton, AxesRangeSingleton, AxisLayout
from ..style.legend_colormap import LegendColormap


class LineColormap:
    """
    A class for plotting lines with color maps on a matplotlib axis.

    The `LineColormap` class is designed to plot lines where the color varies along the line according to a colormap.
    It supports different line styles and patterns, allowing for complex visualizations.

    Parameters
    ----------
    axis_index : int
        The index of the axis on which to plot the line.
    xdata : Union[List[float, int], np.ndarray]
        The data for the x-axis.
    ydata : Union[List[float, int], np.ndarray]
        The data for the y-axis.
    cmapdata : Union[List[float, int], np.ndarray]
        The data to be used for the colormap.
    cmap : str, optional
        The colormap to use (default is "viridis").
    linewidth : Union[int, float], optional
        The width of the line (default is 1).
    linestyle : str, optional
        The style of the line (default is "solid").
    linepattern : Optional[List[Union[float, int]]], optional
        A list defining the pattern of dashes and gaps (default is None).
    label : Optional[str], optional
        The label for the line (default is None).
    num_points : int, optional
        The number of points to use for plotting (default is 1000).
    passed_variables : Dict[str, Any], optional
        Additional variables passed to the line plotting functions (default is {}).
    *args : Any
        Additional positional arguments.
    **kwargs : Any
        Additional keyword arguments.

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
    cmapdata : np.ndarray
        The data used for the colormap.

    Methods
    -------
    plot_line_colormap() -> None
        Plots the line using the specified colormap and line style.
    """

    def __init__(
        self,
        axis_index: int,
        xdata: Union[List[float | int], np.ndarray],
        ydata: Union[List[float | int], np.ndarray],
        cmapdata: Union[List[float | int], np.ndarray],
        cmap: str = "viridis",
        linewidth: int | float = 1,
        linestyle: str = "solid",
        linepattern: None | List[float | int] = None,
        label: None | str = None,
        num_points: int = 1000,
        passed_variables: Dict[str, Any] = {},
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.axis_index: int = axis_index
        self.__axes: AxesSingleton = AxesSingleton()
        self._axis: Axes = self.__axes.get_axis(self.axis_index)

        self._xdata: Union[List[float | int], np.ndarray] = xdata
        self._ydata: Union[List[float | int], np.ndarray] = ydata
        self._cmapdata: Union[List[float | int], np.ndarray] = cmapdata
        self.cmap: str = cmap
        self.linewidth: int | float = linewidth

        self.linestyle: str = linestyle
        self.linepattern: None | List[float | int] = linepattern
        self.label: None | str = label
        self.num_points: int = num_points
        self.passed_variables: Dict[str, Any] = passed_variables
        self.args: Any = args
        self.kwargs: Any = kwargs

        self.DEFAULT_PATTERN: None | List[float | int] = None

        attributer = AttributeSetter()
        self.kwargs_params = attributer.set_attributes(
            self, locals(), key="line_colormap"
        )

        self.xdata: np.ndarray = np.array(self._xdata)
        self.ydata: np.ndarray = np.array(self._ydata)
        self.cmapdata: np.ndarray = np.array(self._cmapdata)

        self._handle_kwargs()

        self._check_linestyle()

        if self.label is not None:
            self._set_legend()

    def _check_linestyle(self) -> None:
        """
        Validates and sets the line style for the plot.

        Raises
        ------
        ValueError
            If an invalid line style is specified.
        """

        # Define the allowed line styles
        ls_dict = {
            "solid": "solid",
            "dashed": "dashed",
            "-": "solid",
            "--": "dashed",
        }

        # Check if the specified line style is allowed
        if self.linestyle not in ls_dict:
            raise ValueError(
                f"Invalid linestyle '{self.linestyle}'. Allowed values are {list(ls_dict.keys())}."
            )

        setattr(self, "linestyle", ls_dict[self.linestyle])

    def _check_linepattern(self, linepattern: None | List[float | int]) -> NDArray[Any]:
        """
        Validates and converts the line pattern to a NumPy array.

        Parameters
        ----------
        linepattern : Optional[List[Union[float, int]]]
            The pattern of dashes and gaps for the line.

        Returns
        -------
        np.ndarray
            The validated line pattern as a NumPy array.

        Raises
        ------
        ValueError
            If the line pattern is invalid.
        """

        if linepattern is not None:
            if not isinstance(linepattern, (list, tuple)) or len(linepattern) != 2:
                raise ValueError(
                    "Invalid linepattern. It must be a list or tuple of length 2."
                )

        linepattern = self.DEFAULT_PATTERN if linepattern is None else linepattern
        _linepattern: NDArray[Any] = np.array(linepattern)
        return _linepattern

    # TODO: Move this function to base directory
    def _handle_kwargs(self) -> None:
        """
        Processes and validates keyword arguments for the line plot.

        Raises
        ------
        ValueError
            If duplicate keys are found in the configuration or passed arguments.
        """

        alias_map = {
            "lw": "linewidth",
            "ls": "linestyle",
        }

        # ╭──────────────────────────────────────────────────────────╮
        # │ check duplicate keys in config file                      │
        # ╰──────────────────────────────────────────────────────────╯
        params = Params().get_item("line_colormap")

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

    def plot_line_colormap(self) -> None:
        """
        Plots the line using the specified colormap and line style.

        This method handles different line styles, such as solid and dashed lines,
        and applies the colormap to the line.
        """

        # Linestyle section
        if self.linestyle == "solid":
            LineColormapSolid(
                self.axis_index,
                self.xdata,
                self.ydata,
                self.cmapdata,
                self.cmap,
                self.linewidth,
                self.num_points,
            ).plot_line_colormap_solid()
            pass
        elif self.linestyle == "dashed":
            # unit is inches
            self.DEFAULT_PATTERN = [0.1, 0.1]
            self.length_solid, self.length_gap = self._check_linepattern(
                self.linepattern
            )

            LineColormapDashed(
                self.axis_index,
                self.xdata,
                self.ydata,
                self.cmapdata,
                self.cmap,
                self.linewidth,
                self.length_solid,
                self.length_gap,
            ).plot_dash_colormap()

    def _set_legend(self) -> None:
        """
        Sets the legend for the colormap line.

        This method adjusts the legend based on the number of points in the colormap data.
        """

        if self.num_points == 0:
            NUM_STRIPES = len(self.cmapdata)
        else:
            NUM_STRIPES = self.num_points

        LegendColormap(
            self.axis_index,
            self.cmap,
            self.label,
            NUM_STRIPES,
            **self._kwargs,
        ).add_legend_colormap()


# !TODO:  check the statement of num_points
@get_passed_args
def line_colormap(
    axis_index: int,
    xdata: Union[List[float], np.ndarray],
    ydata: Union[List[float], np.ndarray],
    cmapdata: Union[List[float], np.ndarray],
    cmap: str = "viridis",
    linewidth: int | float = 1,
    linestyle: str = "solid",
    linepattern: None | List[float | int] = None,
    label: None | str = None,
    num_points: int = 1000,
    *args,
    **kwargs,
) -> None:
    """
    Plots a line on a specified matplotlib axis with a colormap applied.

    This function uses the `LineColormap` class to create a line plot where the color varies
    along the line according to a specified colormap. It supports different line styles, patterns,
    and other customization options.

    Parameters
    ----------
    axis_index : int
        The index of the axis on which to plot the line.
    xdata : Union[List[float], np.ndarray]
        The data for the x-axis.
    ydata : Union[List[float], np.ndarray]
        The data for the y-axis.
    cmapdata : Union[List[float], np.ndarray]
        The data to be used for the colormap.
    cmap : str, optional
        The colormap to use (default is "viridis").
    linewidth : Union[int, float], optional
        The width of the line (default is 1).
    linestyle : str, optional
        The style of the line (default is "solid").
    linepattern : Optional[List[Union[float, int]]], optional
        A list defining the pattern of dashes and gaps (default is None).
    label : Optional[str], optional
        The label for the line (default is None).
    num_points : int, optional
        The number of points to use for plotting (default is 1000).
        If set to 0, the number of stripes in the colormap data will be used.
    *args : Any
        Additional positional arguments passed to the colormap plotting function.
    **kwargs : Any
        Additional keyword arguments passed to the colormap plotting function.

    Returns
    -------
    None

    Notes
    -----
    The `num_points` parameter is critical in determining the resolution of the plotted line. If `num_points` is 0,
    the function will use the number of stripes in `cmapdata` as the number of points.
    """

    passed_variables = line_colormap.passed_variables  # type: ignore
    LineColormap(
        axis_index,
        xdata,
        ydata,
        cmapdata,
        cmap,
        linewidth,
        linestyle,
        linepattern,
        label,
        num_points,
        passed_variables,
        *args,
        **kwargs,
    ).plot_line_colormap()


class LineColormapBase:
    """
    A base class for creating line segments and color maps for line plotting.

    The `LineColormapBase` class provides utility functions for creating line segments
    and generating color maps that can be used for line plots with varying colors along the line.

    Methods
    -------
    _create_segment(xdata: NDArray[Any], ydata: NDArray[Any]) -> NDArray[np.float64]
        Creates line segments from x and y data points for plotting.
    _create_cmap(cmapdata: NDArray[Any]) -> Normalize
        Creates a normalization object for mapping data points to colors.
    """

    def _create_segment(
        self, xdata: NDArray[Any], ydata: NDArray[Any]
    ) -> NDArray[np.float64]:
        """
        Creates line segments from x and y data points for plotting.

        Parameters
        ----------
        xdata : NDArray[Any]
            The x-axis data points.
        ydata : NDArray[Any]
            The y-axis data points.

        Returns
        -------
        NDArray[np.float64]
            An array of line segments, each represented as a pair of points (x, y).
        """

        # ╭──────────────────────────────────────────────────────────╮
        # │ Create a set of line segments so that we can color them  │
        # │ individually                                             │
        # │ This creates the points as an N x 1 x 2 array so that    │
        # │ we can stack points                                      │
        # │ together easily to get the segments. The segments array  │
        # │ for line collection                                      │
        # │ needs to be (numlines) x (points per line) x 2 (for x    │
        # │ and y)                                                   │
        # ╰──────────────────────────────────────────────────────────╯
        points = np.array([xdata, ydata], dtype=np.float64).T.reshape(-1, 1, 2)
        segments: NDArray[np.float64] = np.concatenate(
            [points[:-1], points[1:]], axis=1
        )
        return segments

    def _create_cmap(self, cmapdata: NDArray[Any]) -> Normalize:
        """
        Creates a normalization object for mapping data points to colors.

        Parameters
        ----------
        cmapdata : NDArray[Any]
            The data points to be used for creating the colormap.

        Returns
        -------
        Normalize
            A normalization object that maps the data points to the colormap.
        """

        # Create a continuous norm to map from data points to colors
        norm = Normalize(cmapdata.min(), cmapdata.max())
        return norm


class LineColormapSolid:
    """
    A class for plotting a solid line with a colormap applied along its length.

    The `LineColormapSolid` class is responsible for plotting a solid line where the color
    varies along the line according to the provided colormap data. It supports interpolation
    of the line points to create a smooth gradient effect.

    Parameters
    ----------
    axis_index : int
        The index of the axis on which to plot the line.
    xdata : np.ndarray
        The data for the x-axis.
    ydata : np.ndarray
        The data for the y-axis.
    cmapdata : np.ndarray
        The data to be used for the colormap.
    cmap : str
        The colormap to use (default is "viridis").
    linewidth : Union[int, float]
        The width of the line (default is 1).
    num_points : int
        The number of points to interpolate for the line (default is 1000).

    Methods
    -------
    normal_interpolate_points(num_points: int) -> tuple
        Interpolates the x, y, and colormap data points to create a smooth line.
    plot_line_colormap_solid() -> None
        Plots the solid line with the colormap applied.
    """

    def __init__(
        self,
        axis_index: int,
        xdata: np.ndarray,
        ydata: np.ndarray,
        cmapdata: np.ndarray,
        cmap: str,
        linewidth: int | float,
        num_points: int,
    ) -> None:
        self.axis_index: int = axis_index
        self.__axes: AxesSingleton = AxesSingleton()
        self.axis: Axes = self.__axes.axes[self.axis_index]

        self.xdata: np.ndarray = xdata
        self.ydata: np.ndarray = ydata
        self.cmapdata: np.ndarray = cmapdata

        self.cmap: str = cmap
        self.linewidth: int | float = linewidth
        self.num_points: int = num_points

    def normal_interpolate_points(self, num_points: int) -> tuple:
        """
        Interpolates the x, y, and colormap data points to create a smooth line.

        This method interpolates the data points to create a smooth gradient along the line,
        based on the specified number of points.

        Parameters
        ----------
        num_points : int
            The number of points to interpolate along the line.

        Returns
        -------
        tuple
            A tuple containing the interpolated x, y, and colormap data.
        """

        xdiff = np.diff(self.xdata)
        ydiff = np.diff(self.ydata)
        distances = np.sqrt(xdiff**2 + ydiff**2)
        cumulative_distances = np.insert(np.cumsum(distances), 0, 0)
        interpolated_distances = np.linspace(0, cumulative_distances[-1], num_points)

        x_interpolated = np.interp(
            interpolated_distances, cumulative_distances, self.xdata
        )
        y_interpolated = np.interp(
            interpolated_distances, cumulative_distances, self.ydata
        )

        # Interpolate cmapdata
        cmap_interpolated = np.interp(
            interpolated_distances, cumulative_distances, self.cmapdata
        )

        return x_interpolated, y_interpolated, cmap_interpolated

    @AxesRangeSingleton.update
    def plot_line_colormap_solid(self) -> None:
        """
        Plots the solid line with the colormap applied.

        This method creates the line segments, applies the colormap, and adds the line
        collection to the specified axis.

        Returns
        -------
        None
        """

        if self.num_points != 0:
            self.xdata, self.ydata, self.cmapdata = self.normal_interpolate_points(
                self.num_points
            )
        segments: NDArray[np.float64] = LineColormapBase()._create_segment(
            self.xdata, self.ydata
        )
        norm = LineColormapBase()._create_cmap(self.cmapdata)

        lc = LineCollection(segments.tolist(), cmap=self.cmap, norm=norm)
        lc.set_array(self.cmapdata)
        lc.set_linewidth(self.linewidth)
        self.axis.add_collection(lc)


class LineColormapDashed:
    """
    A class for plotting a dashed line with a colormap applied along its length.

    The `LineColormapDashed` class is responsible for plotting a dashed line where the color
    varies along the line according to the provided colormap data. It accounts for the scaling
    of the line based on the axis dimensions and interpolates points to create a uniform dashed pattern.

    Parameters
    ----------
    axis_index : int
        The index of the axis on which to plot the line.
    xdata : np.ndarray
        The data for the x-axis.
    ydata : np.ndarray
        The data for the y-axis.
    cmapdata : np.ndarray
        The data to be used for the colormap.
    cmap : str
        The colormap to use (default is "viridis").
    linewidth : Union[int, float]
        The width of the line (default is 1).
    length_solid : Union[int, float]
        The length of the solid part of the dash (default is 1).
    length_gap : Union[int, float]
        The length of the gap between dashes (default is 1).
    xspan : np.ndarray, optional
        The span of the x-axis data (default is calculated from `xdata`).
    yspan : np.ndarray, optional
        The span of the y-axis data (default is calculated from `ydata`).

    Methods
    -------
    normal_interpolate_points(num_points: int) -> tuple
        Interpolates the x, y, and colormap data points to create a smooth line.
    plot_dash_colormap() -> None
        Plots the dashed line with the colormap applied.
    """

    def __init__(
        self,
        axis_index: int,
        xdata: np.ndarray,
        ydata: np.ndarray,
        cmapdata: np.ndarray,
        cmap: str,
        linewidth: int | float,
        length_solid: int | float,
        length_gap: int | float,
        xspan=None,
        yspan=None,
    ) -> None:
        self.axis_index: int = axis_index
        self.__axes: AxesSingleton = AxesSingleton()
        self.axis: Axes = self.__axes.axes[self.axis_index]

        self.xdata: np.ndarray = xdata
        self.ydata: np.ndarray = ydata
        self.cmapdata: np.ndarray = cmapdata

        self.cmap: str = cmap
        self.linewidth: int | float = linewidth
        self.length_solid: int | float = length_solid
        self.length_gap: int | float = length_gap

        xspan_data, yspan_data = self._get_data_span()

        self.xspan = xspan_data if xspan is None else xspan
        self.yspan = yspan_data if yspan is None else yspan

        AxisLayout(self.axis_index).get_axis_size()

        # unit is inches
        self.xaxis_inches, self.yaxis_inches = AxisLayout(
            self.axis_index
        ).get_axis_size_inches()

        SCALE_FACTOR = 1

        self.xscale = self.xaxis_inches / (self.xspan * SCALE_FACTOR)
        self.yscale = self.yaxis_inches / (self.yspan * SCALE_FACTOR)

        self._create_uniform_coordinates()

    def normal_interpolate_points(self, num_points: int) -> tuple:
        """
        Interpolates the x, y, and colormap data points to create a smooth line.

        This method interpolates the data points to create a smooth gradient along the line,
        based on the specified number of points.

        Parameters
        ----------
        num_points : int
            The number of points to interpolate along the line.

        Returns
        -------
        tuple
            A tuple containing the interpolated x, y, and colormap data.
        """

        xdiff = np.diff(self.xdata)
        ydiff = np.diff(self.ydata)
        distances = np.sqrt(xdiff**2 + ydiff**2)
        cumulative_distances = np.insert(np.cumsum(distances), 0, 0)
        interpolated_distances = np.linspace(0, cumulative_distances[-1], num_points)

        x_interpolated = np.interp(
            interpolated_distances, cumulative_distances, self.xdata
        )
        y_interpolated = np.interp(
            interpolated_distances, cumulative_distances, self.ydata
        )

        # Interpolate cmapdata
        cmap_interpolated = np.interp(
            interpolated_distances, cumulative_distances, self.cmapdata
        )

        return x_interpolated, y_interpolated, cmap_interpolated

    def _get_data_span(self) -> np.ndarray:
        """
        Calculates the span (range) of the x and y data.

        This method computes the difference between the maximum and minimum values
        of the x and y data, returning the span of each.

        Returns
        -------
        np.ndarray
            An array containing the span of the x and y data.
        """

        xmax, xmin = np.max(self.xdata), np.min(self.xdata)
        ymax, ymin = np.max(self.ydata), np.min(self.ydata)
        xspan = xmax - xmin
        yspan = ymax - ymin
        return np.array([xspan, yspan])

    def _create_uniform_coordinates(self) -> None:
        """
        Creates uniform coordinates for the dashed line based on axis scaling.

        This method scales the x and y data according to the axis dimensions, interpolates the
        points, and prepares the coordinates for plotting a uniform dashed line.
        """

        self.scaled_xdata = self.xdata * self.xscale
        self.scaled_ydata = self.ydata * self.yscale

        self.scaled_xdiff = np.diff(self.scaled_xdata)
        self.scaled_ydiff = np.diff(self.scaled_ydata)
        self.scaled_distances = np.sqrt(self.scaled_xdiff**2 + self.scaled_ydiff**2)
        self.scaled_total_distances = np.sum(self.scaled_distances)

        FACTOR = 5
        NUM_POINTS = int(self.scaled_total_distances * FACTOR // self.length_solid)

        self.x_interpolated, self.y_interpolated, self.cmap_interpolated = (
            self.normal_interpolate_points(NUM_POINTS)
        )

        self.scaled_inter_xdiff = np.gradient(self.x_interpolated * self.xscale)
        self.scaled_inter_ydiff = np.gradient(self.y_interpolated * self.yscale)
        self.scaled_inter_distances = np.sqrt(
            self.scaled_inter_xdiff**2 + self.scaled_inter_ydiff**2
        )

    @AxesRangeSingleton.update
    def plot_dash_colormap(self) -> None:
        """
        Plots the dashed line with the colormap applied.

        This method creates the dashed line segments, applies the colormap, and adds the line
        collection to the specified axis.

        Returns
        -------
        None
        """

        current_length = 0
        draw_dash = True
        idx_start = 0

        norm = LineColormapBase()._create_cmap(self.cmapdata)

        for i in range(len(self.x_interpolated) - 1):
            current_length += self.scaled_inter_distances[i]

            if draw_dash:
                if current_length >= self.length_solid:
                    segments = LineColormapBase()._create_segment(
                        self.x_interpolated[idx_start : i + 1],
                        self.y_interpolated[idx_start : i + 1],
                    )

                    lc = LineCollection(
                        segments.tolist(),
                        cmap=self.cmap,
                        norm=norm,
                    )
                    lc.set_array(self.cmap_interpolated[idx_start : i + 1])
                    lc.set_linewidth(self.linewidth)
                    lc.set_linestyle("solid")
                    self.axis.add_collection(lc)

                    draw_dash = False
                    current_length = 0
                    idx_start = i
            else:
                if current_length >= self.length_gap:
                    draw_dash = True
                    current_length = 0
                    idx_start = i

            # at last with the last point if draw_dash is True
            if i == len(self.x_interpolated) - 2 and draw_dash:
                segments = LineColormapBase()._create_segment(
                    self.x_interpolated[idx_start:],
                    self.y_interpolated[idx_start:],
                )

                lc = LineCollection(
                    segments.tolist(),
                    cmap=self.cmap,
                    norm=norm,
                )
                lc.set_array(self.cmap_interpolated[idx_start:])
                lc.set_linewidth(self.linewidth)
                lc.set_linestyle("solid")
                self.axis.add_collection(lc)
