from typing import Any

import numpy as np
from matplotlib import colors
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.typing import ColorType
from numpy.typing import ArrayLike, NDArray

from ..base.base import CreateClassParams, ParamsGetter, bind_passed_params
from ..base.base_alias_validator import AliasValidator
from ..figure.axes_range_base import AxesRangeSingleton
from .line_base import AutoColor, NumLines

__all__: list[str] = ["scatter"]


class Scatter:
    """
    A class for creating scatter plots on a specified Matplotlib axis.

    Parameters
    --------------------
    ax : matplotlib.axes.Axes
        The target axis for the scatter
    x : ArrayLike
        The x-coordinates of the scatter points.
    y : ArrayLike
        The y-coordinates of the scatter points.
    color : ColorType or None, optional
        Color of the points. If `None`, a default color from the axis's cycle is used (default is `None`).
    size : int or float, optional
        Size of the scatter points (default is 1).
    alpha : int or float, optional
        Opacity of the scatter points (default is 1).
    **kwargs : Any
        Additional keyword arguments passed to the `scatter` method of Matplotlib's `Axes`.

    Attributes
    --------------------
    x : numpy.ndarray
        The x-coordinates as a NumPy array.
    y : numpy.ndarray
        The y-coordinates as a NumPy array.

    Methods
    --------------------
    get_color() -> ColorType
        Determines the color for the scatter points, either from the user input or the axis's color cycle.
    plot() -> matplotlib.collections.PathCollection
        Creates and plots the scatter points on the axis.

    Examples
    --------------------
    >>> x = [1, 2, 3, 4]
    >>> y = [10, 20, 15, 25]
    >>> scatter = Scatter(ax=ax, x=x, y=y, color="blue", size=10, alpha=0.5)
    >>> scatter.plot()
    """

    def __init__(
        self,
        ax: Axes,
        x: ArrayLike,
        y: ArrayLike,
        color: ColorType | None = None,
        size: int | float = 1,
        alpha: int | float = 1,
        **kwargs: Any,
    ) -> None:
        self.ax: Axes = ax

        self._x: ArrayLike = x
        self._y: ArrayLike = y
        self._color: ColorType | None = color
        self.size: int | float = size
        self.alpha: int | float = alpha
        self.kwargs: Any = kwargs

        self.x: NDArray[Any] = np.array(self._x)
        self.y: NDArray[Any] = np.array(self._y)

        self.color = self.get_color()

    def get_color(self) -> ColorType:
        """
        Determines the color for the scatter points.

        If a color is not explicitly provided, it retrieves a default color from the
        axis's color cycle.

        Returns
        --------------------
        ColorType
            The resolved color for the scatter points.

        Notes
        --------------------
        The method ensures compatibility with Matplotlib's color representation, converting
        NumPy arrays to hexadecimal strings if needed.

        Examples
        --------------------
        >>> scatter = Scatter(ax=ax, x=[1, 2], y=[3, 4])
        >>> scatter.get_color()
        """
        cycle_color: NDArray | str = AutoColor(self.ax).get_color()
        if isinstance(cycle_color, np.ndarray):
            cycle_color = colors.to_hex(
                tuple(cycle_color)
            )  # convert numpy array to tuple

        default_color: ColorType = cycle_color if self._color is None else self._color
        return default_color

    @NumLines.count
    @AxesRangeSingleton.update
    def plot(self) -> PathCollection:
        """
        Plots the scatter points on the specified axis.

        This method creates a scatter plot using the provided x, y, color, size, and alpha values.

        Returns
        --------------------
        matplotlib.collections.PathCollection
            The scatter plot as a PathCollection object.

        Notes
        --------------------
        - This method is decorated with `@NumLines.count` to track the number of scatter calls on the axis.
        - It is also decorated with `@AxesRangeSingleton.update` to update the axis range with the scatter data.

        Examples
        --------------------
        >>> scatter = Scatter(ax=ax, x=[1, 2, 3], y=[4, 5, 6], size=50, alpha=0.8)
        >>> scatter.plot()
        <matplotlib.collections.PathCollection>
        """
        _plot = self.ax.scatter(
            self.x,
            self.y,
            s=self.size,
            c=self.color,
            alpha=self.alpha,
            **self.kwargs,
        )
        return _plot


@bind_passed_params()
def scatter(
    ax: Axes,
    x: ArrayLike,
    y: ArrayLike,
    color: ColorType | None = None,
    size: int | float = 1,
    alpha: int | float = 1,
    **kwargs: Any,
) -> PathCollection:
    """
    Creates a scatter plot on the specified axis.

    This function uses the `Scatter` class to generate a scatter plot with customizable
    size, color, and transparency.

    Parameters
    --------------------
    ax : matplotlib.axes.Axes
        The target axis for the scatter.
    x : ArrayLike
        The x-coordinates of the scatter points.
    y : ArrayLike
        The y-coordinates of the scatter points.
    color : ColorType or None, optional
        Color of the points. If `None`, a default color from the axis's cycle is used (default is `None`).
    size : int or float, optional
        Size of the scatter points (default is 1).
    alpha : int or float, optional
        Opacity of the scatter points (default is 1).
    **kwargs : Any
        Additional keyword arguments passed to the `scatter` method of Matplotlib's `Axes`.

    Notes
    --------------------
    - This function utilizes the `ParamsGetter` to retrieve bound parameters and the `CreateClassParams` class to handle the merging of default, configuration, and passed parameters.
    - Alias validation is performed using the `AliasValidator` class.

        - 's' (size)
        - 'c' (color)

    Returns
    --------------------
    matplotlib.collections.PathCollection
        The scatter plot as a PathCollection object.

    Examples
    --------------------
    >>> import gsplot as gs
    >>> x = [1, 2, 3, 4]
    >>> y = [10, 20, 15, 25]
    >>> gs.scatter(ax=ax, x=x, y=y, color="red", size=20, alpha=0.8)
    <matplotlib.collections.PathCollection>
    """
    alias_map = {
        "s": "size",
        "c": "color",
    }

    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    AliasValidator(alias_map, passed_params).validate()
    class_params: dict[str, Any] = CreateClassParams(passed_params).get_class_params()

    _scatter = Scatter(
        class_params["ax"],
        class_params["x"],
        class_params["y"],
        class_params["color"],
        class_params["size"],
        class_params["alpha"],
        **class_params["kwargs"],
    )
    return _scatter.plot()
