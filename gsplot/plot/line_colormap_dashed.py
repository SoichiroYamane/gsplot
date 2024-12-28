from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection
from numpy.typing import ArrayLike, NDArray

from ..base.base import CreateClassParams, ParamsGetter, bind_passed_params
from ..base.base_alias_validator import AliasValidator
from ..figure.axes_base import AxisLayout
from ..figure.axes_range_base import AxesRangeSingleton
from ..style.legend_colormap import LegendColormap
from .line_colormap_base import LineColormapBase

__all__: list[str] = ["line_colormap_dashed"]


class LineColormapDashed:
    """
    A class for creating and plotting dashed lines with colormap interpolation.

    This class plots a dashed line with varying colors based on a provided colormap
    and associated data. It supports interpolation, axis scaling, and flexible dash patterns.

    Parameters
    --------------------
    ax : matplotlib.axes.Axes
        The target axis where the line will be plotted.
    x : ArrayLike
        The x-coordinates of the line data.
    y : ArrayLike
        The y-coordinates of the line data.
    cmapdata : ArrayLike
        Data used for mapping the colormap to the line.
    cmap : str, optional
        The name of the Matplotlib colormap to use (default is "viridis").
    linewidth : int or float, optional
        The width of the line (default is 1).
    line_pattern : tuple[float, float], optional
        The pattern of solid and gap lengths for the dashed line (default is (10, 10)).
    label : str or None, optional
        The label for the line, used in legends (default is None).
    xspan : int or float or None, optional
        The span of the x-axis data for scaling (default is None).
    yspan : int or float or None, optional
        The span of the y-axis data for scaling (default is None).
    **kwargs : Any
        Additional keyword arguments passed to `LegendColormap`.

    Methods
    --------------------
    add_legend_colormap()
        Adds a legend for the colormap to the target axis.
    verify_line_pattern()
        Validates and adjusts the line pattern for solid and gap lengths.
    get_data_span()
        Calculates the span of the x and y data.
    get_scales()
        Retrieves scaling factors for the x and y axes based on figure and axis sizes.
    get_interpolated_data(interpolation_points)
        Interpolates the line and colormap data to create smooth segments.
    plot()
        Plots the dashed line with the interpolated colormap.

    Examples
    --------------------
    >>> x = np.linspace(0, 10, 100)
    >>> y = np.sin(x)
    >>> cmapdata = np.linspace(0, 1, 100)
    >>> dashed_line = LineColormapDashed(0, x, y, cmapdata, line_pattern=(5, 5))
    >>> lc_list = dashed_line.plot()
    >>> print(len(lc_list))
    10  # Number of dashed line segments
    """

    def __init__(
        self,
        ax: Axes,
        x: ArrayLike,
        y: ArrayLike,
        cmapdata: ArrayLike,
        cmap: str = "viridis",
        linewidth: int | float = 1,
        line_pattern: tuple[int | float, int | float] = (10, 10),
        label: str | None = None,
        xspan: int | float | None = None,
        yspan: int | float | None = None,
        **kwargs: Any,
    ) -> None:

        self.ax: Axes = ax

        self._x: ArrayLike = x
        self._y: ArrayLike = y
        self._cmapdata: ArrayLike = cmapdata
        self.cmap: str = cmap
        self.linewidth = linewidth
        self.line_pattern: tuple[int | float, int | float] = line_pattern
        self.label: str | None = label
        self._xspan: int | float | None = xspan
        self._yspan: int | float | None = yspan
        self.kwargs: Any = kwargs

        self.x: NDArray[Any] = np.array(self._x)
        self.y: NDArray[Any] = np.array(self._y)
        self.cmapdata: NDArray[Any] = np.array(self._cmapdata)

        if self.label is not None:
            self.add_legend_colormap()

        self.xspan: float = (
            self.get_data_span()[0] if self._xspan is None else self._xspan
        )
        self.yspan: float = (
            self.get_data_span()[1] if self._yspan is None else self._yspan
        )

        self.fig = plt.gcf()

        self.verify_line_pattern()

        self._calculate_uniform_coordinates()

    def add_legend_colormap(self) -> None:
        """
        Adds a legend entry for the colormap associated with the dashed line.

        This method creates a legend entry that represents the colormap used in the dashed
        line plot. The legend is customized with a specified number of stripes.

        Parameters
        --------------------
        None

        Returns
        --------------------
        None

        Examples
        --------------------
        >>> line = LineColormapDashed(ax=ax, x=[0, 1, 2], y=[1, 2, 3], cmapdata=[0.1, 0.5, 1.0])
        >>> line.add_legend_colormap()
        """
        LegendColormap(
            self.ax,
            self.cmap,
            self.label,
            num_stripes=len(self.cmapdata),
            **self.kwargs,
        ).axis_patch()

    def verify_line_pattern(self) -> None:
        """
        Verifies and adjusts the line pattern for the dashed line.

        This method ensures that the provided `line_pattern` parameter is a tuple of exactly
        two elements (solid and gap lengths). It also adjusts the solid line length to account
        for the projected `capstyle`.

        Parameters
        --------------------
        None

        Returns
        --------------------
        None

        Raises
        --------------------
        ValueError
            If the `line_pattern` is not a tuple with exactly two elements.

        Examples
        --------------------
        >>> line = LineColormapDashed(ax=ax, x=[0, 1], y=[1, 2], cmapdata=[0.1, 0.2])
        >>> line.verify_line_pattern()
        """
        if len(self.line_pattern) != 2:
            raise ValueError(
                f"Line pattern must be a tuple with two elements, not {len(self.line_pattern)}."
            )

        self.length_solid: int | float = self.line_pattern[0]
        self.length_gap: int | float = self.line_pattern[1]

        # Due to projecting capstyle, the solid line must be shrinked by half of the linewidth
        self.length_solid = np.abs(self.length_solid - self.linewidth / 2)

    def get_data_span(self) -> NDArray[np.float64]:
        """
        Calculates the span of the x and y data.

        This method determines the range of the x and y coordinates and calculates
        their respective spans.

        Parameters
        --------------------
        None

        Returns
        --------------------
        numpy.ndarray
            A 1D array containing the spans of the x and y data as `[xspan, yspan]`.

        Examples
        --------------------
        >>> line = LineColormapDashed(ax=ax, x=[0, 1, 2], y=[1, 2, 3], cmapdata=[0.1, 0.5, 1.0])
        >>> spans = line.get_data_span()
        >>> print(spans)
        array([2.0, 2.0])
        """

        xmax, xmin = np.max(self.x), np.min(self.x)
        ymax, ymin = np.max(self.y), np.min(self.y)
        xspan = xmax - xmin
        yspan = ymax - ymin
        return np.array([xspan, yspan])

    def get_scales(self) -> tuple[float, float]:
        """
        Computes scaling factors for the x and y axes based on the figure and axis sizes.

        This method calculates how the x and y data should be scaled to match the
        current figure and axis dimensions.

        Parameters
        --------------------
        None

        Returns
        --------------------
        tuple[float, float]
            A tuple containing the scaling factors for the x and y axes.

        Examples
        --------------------
        >>> line = LineColormapDashed(ax=ax, x=[0, 1, 2], y=[1, 2, 3], cmapdata=[0.1, 0.5, 1.0])
        >>> xscale, yscale = line.get_scales()
        >>> print(xscale, yscale)
        100.0 150.0  # Example output
        """
        canvas_width, canvas_height = self.fig.canvas.get_width_height()
        # get axis size
        axis_width, axis_height = AxisLayout(self.ax).get_axis_size()

        xscale: float
        yscale: float
        if self.xspan == 0:
            xscale = 1.0
        else:
            xscale = (canvas_width / self.xspan) * (axis_width)
        if self.yspan == 0:
            yscale = 1.0
        else:
            yscale = canvas_height / self.yspan * (axis_height)
        return xscale, yscale

    def get_interpolated_data(self, interpolation_points: int) -> tuple:
        """
        Interpolates the x, y, and colormap data to ensure uniform dash spacing.

        This method calculates evenly spaced points along the input x and y data
        and interpolates the colormap data accordingly.

        Parameters
        --------------------
        interpolation_points : int
            The number of points to interpolate.

        Returns
        --------------------
        tuple
            A tuple containing the interpolated x, y, and colormap data arrays.

        Examples
        --------------------
        >>> line = LineColormapDashed(ax=ax, x=[0, 1, 2], y=[1, 2, 3], cmapdata=[0.1, 0.5, 1.0])
        >>> x_interp, y_interp, cmap_interp = line.get_interpolated_data(100)
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

    def _calculate_uniform_coordinates(self) -> None:
        """
        Interpolates the x, y, and colormap data to ensure uniform dash spacing.

        This method calculates evenly spaced points along the input x and y data
        and interpolates the colormap data accordingly.

        Parameters
        --------------------
        interpolation_points : int
            The number of points to interpolate.

        Returns
        --------------------
        tuple
            A tuple containing the interpolated x, y, and colormap data arrays.

        Examples
        --------------------
        >>> line = LineColormapDashed(ax=ax, x=[0, 1, 2], y=[1, 2, 3], cmapdata=[0.1, 0.5, 1.0])
        >>> x_interp, y_interp, cmap_interp = line.get_interpolated_data(100)
        """

        xscale, yscale = self.get_scales()
        self.scaled_x = self.x * xscale
        self.scaled_y = self.y * yscale

        self.scaled_xdiff = np.diff(self.scaled_x)
        self.scaled_ydiff = np.diff(self.scaled_y)

        self.scaled_xdiff = np.nan_to_num(np.diff(self.scaled_x), nan=0.0)
        self.scaled_ydiff = np.nan_to_num(np.diff(self.scaled_y), nan=0.0)

        self.scaled_distances = np.sqrt(self.scaled_xdiff**2 + self.scaled_ydiff**2)
        self.scaled_total_distances = np.sum(self.scaled_distances)

        FACTOR = 5
        INTERPOLATION_POINTS = int(
            self.scaled_total_distances * FACTOR // self.length_solid
        )

        self.x_interpolated, self.y_interpolated, self.cmap_interpolated = (
            self.get_interpolated_data(INTERPOLATION_POINTS)
        )

        self.scaled_inter_xdiff = np.gradient(self.x_interpolated * xscale)
        self.scaled_inter_ydiff = np.gradient(self.y_interpolated * yscale)
        self.scaled_inter_distances = np.sqrt(
            self.scaled_inter_xdiff**2 + self.scaled_inter_ydiff**2
        )

    @AxesRangeSingleton.update
    def plot(self) -> list[LineCollection]:
        """
        Plots the dashed line with a colormap applied to individual segments.

        This method creates dashed line segments by iterating over the interpolated
        coordinates and adding `LineCollection` objects to the target axis. Each
        dash segment is colored based on the provided colormap data.

        Parameters
        --------------------
        None

        Returns
        --------------------
        list[matplotlib.collections.LineCollection]
            A list of `LineCollection` objects representing the plotted dashed line segments.

        Notes
        --------------------
        - This method is decorated with `@AxesRangeSingleton.update` to update the axis range
        singleton with the plotted data.
        - The method uses `LineColormapBase` for creating line segments and normalizing the
        colormap data.

        Raises
        --------------------
        ValueError
            If the input data or configuration parameters are invalid.

        Examples
        --------------------
        >>> x = [0, 1, 2, 3, 4]
        >>> y = [1, 3, 2, 5, 4]
        >>> cmapdata = [0.1, 0.3, 0.6, 0.9, 1.0]
        >>> line = LineColormapDashed(ax=ax, x=x, y=y, cmapdata=cmapdata)
        >>> lc_list = line.plot()
        """
        current_length = 0
        draw_dash = True
        idx_start = 0

        norm = LineColormapBase()._create_cmap(self.cmapdata)

        lc_list: list[LineCollection] = []
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
                        capstyle="projecting",
                    )
                    lc.set_array(self.cmap_interpolated[idx_start : i + 1])
                    lc.set_linewidth(self.linewidth)
                    lc.set_linestyle("solid")
                    self.ax.add_collection(lc)

                    lc_list.append(lc)

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

                self.ax.add_collection(lc)

                lc_list.append(lc)

        return lc_list


@bind_passed_params()
def line_colormap_dashed(
    ax: Axes,
    x: ArrayLike,
    y: ArrayLike,
    cmapdata: ArrayLike,
    cmap: str = "viridis",
    linewidth: int | float = 1,
    line_pattern: tuple[float, float] = (10, 10),
    label: str | None = None,
    xspan: int | float | None = None,
    yspan: int | float | None = None,
    **kwargs: Any,
) -> list[LineCollection]:
    """
    A convenience function to plot dashed lines with a colormap applied to individual segments.

    This function wraps the `LineColormapDashed` class for ease of use. It handles axis
    resolution, alias validation, and parameter merging automatically.

    Parameters
    --------------------
    ax : matplotlib.axes.Axes
        The target axis where the line will be plotted.
    x : ArrayLike
        The x-coordinates of the line.
    y : ArrayLike
        The y-coordinates of the line.
    cmapdata : ArrayLike
        The data used for coloring the line segments. Values will be normalized to map to colors.
    cmap : str, optional
        The name of the colormap to use (default is "viridis").
    linewidth : int or float, optional
        The width of the line (default is 1).
    line_pattern : tuple[float, float], optional
        A tuple specifying the lengths of solid and gap segments in the dash pattern (default is (10, 10)).
    label : str or None, optional
        The label for the line, used in legends (default is `None`).
    xspan : float or None, optional
        The span of x-coordinates for scaling, calculated automatically if `None` (default is `None`).
    yspan : float or None, optional
        The span of y-coordinates for scaling, calculated automatically if `None` (default is `None`).
    **kwargs : Any
        Additional keyword arguments passed to Matplotlib functions.

    Notes
    --------------------
    - This function utilizes the `ParamsGetter` to retrieve bound parameters and the `CreateClassParams` class to handle the merging of default, configuration, and passed parameters.
    - Alias validation is performed using the `AliasValidator` class.

        - `lw` for `linewidth`

    Returns
    --------------------
    list[matplotlib.collections.LineCollection]
        A list of `LineCollection` objects representing the plotted dashed line.

    Examples
    --------------------
    >>> import gsplot as gs
    >>> x = [0, 1, 2, 3]
    >>> y = [1, 2, 3, 4]
    >>> cmapdata = [0.1, 0.4, 0.6, 0.9]
    >>> line_collections = gs.line_colormap_dashed(ax, x, y, cmapdata, line_pattern=(5, 5))
    """
    alias_map = {
        "lw": "linewidth",
    }

    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    AliasValidator(alias_map, passed_params).validate()
    class_params = CreateClassParams(passed_params).get_class_params()

    _line_colormap_dashed: LineColormapDashed = LineColormapDashed(
        class_params["ax"],
        class_params["x"],
        class_params["y"],
        class_params["cmapdata"],
        class_params["cmap"],
        class_params["linewidth"],
        class_params["line_pattern"],
        class_params["label"],
        class_params["xspan"],
        class_params["yspan"],
        **class_params["kwargs"],
    )
    return _line_colormap_dashed.plot()
