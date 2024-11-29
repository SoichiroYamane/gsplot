from typing import Any
from numpy.typing import ArrayLike, NDArray
import numpy as np
from matplotlib import colors
from matplotlib.axes import Axes
from matplotlib.typing import ColorType
from matplotlib.collections import PathCollection


from .line_base import NumLines
from .line_base import AutoColor

from ..base.base import bind_passed_params, ParamsGetter, CreateClassParams
from ..base.base_alias_validator import AliasValidator
from ..figure.axes_base import AxesResolver, AxesRangeSingleton


class Scatter:
    def __init__(
        self,
        axis_target: int | Axes,
        x: ArrayLike,
        y: ArrayLike,
        color: ColorType | None = None,
        size: int | float = 1,
        alpha: int | float = 1,
        **kwargs: Any,
    ) -> None:
        self.axis_target: int | Axes = axis_target

        self.axis_index: int = AxesResolver(self.axis_target).axis_index
        self.axis: Axes = AxesResolver(self.axis_target).axis

        self._x: ArrayLike = x
        self._y: ArrayLike = y
        self._color: ColorType | None = color
        self.size: int | float = size
        self.alpha: int | float = alpha
        self.kwargs: Any = kwargs

        self.x: NDArray[Any] = np.array(self._x)
        self.y: NDArray[Any] = np.array(self._y)

    def get_color(self) -> ColorType:

        cycle_color: NDArray | str = AutoColor(self.axis_index).get_color()
        if isinstance(cycle_color, np.ndarray):
            cycle_color = colors.to_hex(
                tuple(cycle_color)
            )  # convert numpy array to tuple

        default_color: ColorType = cycle_color if self._color is None else self._color
        return default_color

    @NumLines.count
    @AxesRangeSingleton.update
    def plot(self) -> PathCollection:
        _plot = self.axis.scatter(
            self.x,
            self.y,
            s=self.size,
            c=self.get_color(),
            alpha=self.alpha,
            **self.kwargs,
        )
        return _plot


# TODO: modify the docstring
@bind_passed_params()
def scatter(
    axis_target: int | Axes,
    x: ArrayLike,
    y: ArrayLike,
    color: ColorType | None = None,
    size: int | float = 1,
    alpha: int | float = 1,
    **kwargs: Any,
) -> PathCollection:
    """
    Create a scatter plot with customizable appearance.

    This function creates a scatter plot on a specified axis using x and y
    coordinates. The size, color, and transparency of the points can be customized.

    Parameters
    ----------
    axis_target : int or Axes
        The target axis where the scatter plot will be created. Can be an integer
        index of the axis or an `Axes` instance.
    x : ArrayLike
        The x-coordinates of the data points.
    y : ArrayLike
        The y-coordinates of the data points.
    color : ColorType or None, optional
        The color of the points. Accepts any valid Matplotlib color specification.
        Default is None.
    size : int or float, optional
        The size of the points. Default is 1.
    alpha : int or float, optional
        The transparency of the points. Value should be between 0 (transparent) and 1
        (opaque). Default is 1.
    **kwargs : Any
        Additional keyword arguments passed to the `Scatter` class for further
        customization.

    Returns
    -------
    PathCollection
        A Matplotlib `PathCollection` object representing the scatter plot.

    Notes
    -----
    - This function uses the `Scatter` class for plotting and customization.
    - Aliases for parameters are supported (e.g., "s" for "size" and "c" for "color").
    - Additional keyword arguments can be used to customize the scatter plot further,
      such as edge colors or colormap settings.

    Examples
    --------
    Create a basic scatter plot:

    >>> scatter(axis_target=0, x=[1, 2, 3], y=[4, 5, 6])

    Customize the color and size of points:

    >>> scatter(axis_target=0, x=[1, 2, 3], y=[4, 5, 6],
    ...         color="red", size=10)

    Add transparency to points:

    >>> scatter(axis_target=0, x=[1, 2, 3], y=[4, 5, 6],
    ...         alpha=0.5)

    Pass additional keyword arguments:

    >>> scatter(axis_target=0, x=[1, 2, 3], y=[4, 5, 6],
    ...         edgecolors="black", linewidth=0.5)
    """
    alias_map = {
        "s": "size",
        "c": "color",
    }

    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    AliasValidator(alias_map, passed_params).validate()
    class_params: dict[str, Any] = CreateClassParams(passed_params).get_class_params()

    _scatter = Scatter(
        class_params["axis_target"],
        class_params["x"],
        class_params["y"],
        class_params["color"],
        class_params["size"],
        class_params["alpha"],
        **class_params["kwargs"],
    )
    return _scatter.plot()
