from typing import Any, Literal

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
from numpy.typing import ArrayLike, NDArray

from ..base.base import CreateClassParams, ParamsGetter, bind_passed_params
from ..base.base_alias_validator import AliasValidator
from ..figure.axes_base import AxesRangeSingleton, AxesResolver, AxisLayout
from ..style.legend_colormap import LegendColormap
from .line_colormap_base import LineColormapBase


class LineColormapDashed:
    def __init__(
        self,
        axis_target: int | Axes,
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
        self.axis_target: int | Axes = axis_target

        self.axis_index: int = AxesResolver(axis_target).axis_index
        self.axis: Axes = AxesResolver(axis_target).axis

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

        self.x: NDArray = np.array(self._x)
        self.y: NDArray = np.array(self._y)
        self.cmapdata: NDArray = np.array(self._cmapdata)

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
        LegendColormap(
            self.axis_index,
            self.cmap,
            self.label,
            num_stripes=len(self.cmapdata),
            **self.kwargs,
        ).axis_patch()

    def verify_line_pattern(self) -> None:
        if len(self.line_pattern) != 2:
            raise ValueError(
                f"Line pattern must be a tuple with two elements, not {len(self.line_pattern)}."
            )

        self.length_solid: int | float = self.line_pattern[0]
        self.length_gap: int | float = self.line_pattern[1]

        # Due to projecting capstyle, the solid line must be shrinked by half of the linewidth
        self.length_solid = np.abs(self.length_solid - self.linewidth / 2)

    def get_data_span(self) -> NDArray:

        xmax, xmin = np.max(self.x), np.min(self.x)
        ymax, ymin = np.max(self.y), np.min(self.y)
        xspan = xmax - xmin
        yspan = ymax - ymin
        return np.array([xspan, yspan])

    def get_scales(self) -> tuple[float, float]:
        canvas_width, canvas_height = self.fig.canvas.get_width_height()
        # get axis size
        axis_width, axis_height = AxisLayout(self.axis_index).get_axis_size()

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
                    self.axis.add_collection(lc)

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

                self.axis.add_collection(lc)

                lc_list.append(lc)

        return lc_list


# TODO: modify the docstring
@bind_passed_params()
def line_colormap_dashed(
    axis_target: int | Axes,
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
    Plot a dashed line with a colormap applied based on data values.

    This function creates a line plot with a colormap applied to segments of the
    line, where the colors are determined by the `cmapdata` values. The line style
    can be customized to be dashed, and the plot can be confined to a specific span
    along the x- or y-axis.

    Parameters
    ----------
    axis_target : int or Axes
        The target axis where the line will be plotted. Can be an integer index of
        the axis or an `Axes` instance.
    x : ArrayLike
        The x-coordinates of the data points.
    y : ArrayLike
        The y-coordinates of the data points.
    cmapdata : ArrayLike
        The data values used to map colors to the line segments.
    cmap : str, optional
        The name of the colormap to use. Default is "viridis".
    linewidth : int or float, optional
        The width of the line. Default is 1.
    line_pattern : tuple[float, float], optional
        The pattern of dashes and gaps in the line, specified as a tuple of lengths
        (dash length, gap length). Default is (10, 10).
    label : str or None, optional
        The label for the line, used in legends. Default is None.
    xspan : int, float, or None, optional
        If specified, the x-axis range to restrict the plot to. Default is None.
    yspan : int, float, or None, optional
        If specified, the y-axis range to restrict the plot to. Default is None.
    **kwargs : Any
        Additional keyword arguments passed to the `LineCollection` creation process.

    Returns
    -------
    list[LineCollection]
        A list of `LineCollection` objects representing the plotted line segments
        with colormapped dashes.

    Notes
    -----
    - The line segments are colored based on the `cmapdata` values using the specified colormap.
    - The `AliasValidator` supports shorthand aliases like "lw" for "linewidth".
    - The dashed pattern can be adjusted with `line_pattern` to customize the appearance.

    Examples
    --------
    Plot a dashed line with a colormap:

    >>> import numpy as np
    >>> x = np.linspace(0, 10, 100)
    >>> y = np.sin(x)
    >>> cmapdata = np.abs(y)  # Map colors based on the absolute value of y
    >>> line_colormap_dashed(axis_target=0, x=x, y=y, cmapdata=cmapdata)

    Customize the line style and colormap:

    >>> line_colormap_dashed(axis_target=0, x=x, y=y, cmapdata=cmapdata,
    ...                      cmap="plasma", linewidth=2, line_pattern=(5, 5))

    Restrict the plot to a specific x-span:

    >>> line_colormap_dashed(axis_target=0, x=x, y=y, cmapdata=cmapdata,
    ...                      xspan=(2, 8))
    """
    alias_map = {
        "lw": "linewidth",
    }

    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    AliasValidator(alias_map, passed_params).validate()
    class_params = CreateClassParams(passed_params).get_class_params()

    _line_colormap_dashed: LineColormapDashed = LineColormapDashed(
        class_params["axis_target"],
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
