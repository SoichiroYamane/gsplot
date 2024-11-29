import numpy as np
from numpy.typing import NDArray, ArrayLike
from matplotlib.axes import Axes
from matplotlib.colors import Normalize
from matplotlib.collections import LineCollection
from typing import Any, Literal


from .line_colormap_base import LineColormapBase
from ..base.base import bind_passed_params, ParamsGetter, CreateClassParams
from ..base.base_alias_validator import AliasValidator
from ..figure.axes_base import AxesResolver, AxesRangeSingleton, AxisLayout
from ..style.legend_colormap import LegendColormap


class LineColormapSolid:
    def __init__(
        self,
        axis_target: int | Axes,
        x: ArrayLike,
        y: ArrayLike,
        cmapdata: ArrayLike,
        cmap: str = "viridis",
        linewidth: int | float = 1,
        label: str | None = None,
        interpolation_points: int | None = None,
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
        self.label: str | None = label
        self.interpolation_points: int | None = interpolation_points

        self.kwargs: Any = kwargs

        self.x: NDArray = np.array(self._x)
        self.y: NDArray = np.array(self._y)
        self.cmapdata: NDArray = np.array(self._cmapdata)

        if self.label is not None:
            self.add_legend_colormap()

    def add_legend_colormap(self) -> None:
        if self.interpolation_points is None:
            NUM_STRIPES = len(self.cmapdata)
        else:
            NUM_STRIPES = self.interpolation_points

        LegendColormap(
            self.axis_index,
            self.cmap,
            self.label,
            NUM_STRIPES,
            **self.kwargs,
        ).add_legend_colormap()

    def normal_interpolate_points(self, interpolation_points: int) -> tuple:
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

    @AxesRangeSingleton.update
    def plot(self) -> list[LineCollection]:
        if self.interpolation_points is not None:
            self.x, self.y, self.cmapdata = self.normal_interpolate_points(
                self.interpolation_points
            )
        segments: NDArray[np.float64] = LineColormapBase()._create_segment(
            self.x, self.y
        )
        norm = LineColormapBase()._create_cmap(self.cmapdata)

        lc: LineCollection = LineCollection(
            segments.tolist(), cmap=self.cmap, norm=norm
        )
        lc.set_array(self.cmapdata)
        lc.set_linewidth(self.linewidth)
        self.axis.add_collection(lc)

        return [lc]


# TODO: modify the docstring
@bind_passed_params()
def line_colormap_solid(
    axis_target: int | Axes,
    x: ArrayLike,
    y: ArrayLike,
    cmapdata: ArrayLike,
    cmap: str = "viridis",
    linewidth: float | int = 1,
    label: str | None = None,
    interpolation_points: int | None = None,
    **kwargs: Any,
) -> list[LineCollection]:
    """
    Plot a solid line with a colormap applied based on data values.

    This function creates a line plot where the color of the line varies according
    to the provided `cmapdata` values. The line is a solid style, and additional
    customization such as interpolation of colors can be specified.

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
    linewidth : float or int, optional
        The width of the line. Default is 1.
    label : str or None, optional
        The label for the line, used in legends. Default is None.
    interpolation_points : int or None, optional
        The number of points to use for interpolating the colormap along the line.
        If None, no interpolation is applied. Default is None.
    **kwargs : Any
        Additional keyword arguments passed to the `LineCollection` creation process.

    Returns
    -------
    list[LineCollection]
        A list of `LineCollection` objects representing the plotted line segments
        with applied colormap.

    Notes
    -----
    - The line is styled as a solid line with colors mapped from the provided `cmapdata`.
    - The `AliasValidator` supports shorthand aliases like "lw" for "linewidth".
    - Interpolation can be used to smooth the color transitions along the line.

    Examples
    --------
    Plot a solid line with a colormap:

    >>> import numpy as np
    >>> x = np.linspace(0, 10, 100)
    >>> y = np.sin(x)
    >>> cmapdata = np.abs(y)  # Map colors based on the absolute value of y
    >>> line_colormap_solid(axis_target=0, x=x, y=y, cmapdata=cmapdata)

    Customize the line style and colormap:

    >>> line_colormap_solid(axis_target=0, x=x, y=y, cmapdata=cmapdata,
    ...                     cmap="plasma", linewidth=2)

    Use interpolation for smooth color transitions:

    >>> line_colormap_solid(axis_target=0, x=x, y=y, cmapdata=cmapdata,
    ...                     interpolation_points=200)
    """
    alias_map = {
        "lw": "linewidth",
    }

    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    AliasValidator(alias_map, passed_params).validate()
    class_params = CreateClassParams(passed_params).get_class_params()

    _line_colormap_solid: LineColormapSolid = LineColormapSolid(
        class_params["axis_target"],
        class_params["x"],
        class_params["y"],
        class_params["cmapdata"],
        class_params["cmap"],
        class_params["linewidth"],
        class_params["label"],
        class_params["interpolation_points"],
        **class_params["kwargs"],
    )
    return _line_colormap_solid.plot()
