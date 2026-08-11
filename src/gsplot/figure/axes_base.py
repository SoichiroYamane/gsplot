from __future__ import annotations

from typing import Any, Callable, TypeVar

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.transforms import Bbox
from numpy.typing import NDArray

from .figure_tools import FigureLayout

F = TypeVar("F", bound=Callable[..., Any])

__all__: list[str] = []


class AxisLayout:
    """
    A utility class for managing axis layout properties in a Matplotlib figure.

    This class provides methods to retrieve an axis's position and size, both in
    normalized figure coordinates and in physical units (inches). It integrates
    with the `AxesResolver` and `FigureLayout` classes to ensure consistent layout
    calculations.

    Parameters
    --------------------
    ax : matplotlib.axes.Axes
        The target `Axes` object for which to manage the

    Attributes
    --------------------
    ax : matplotlib.axes.Axes
        The target `Axes` object for which to manage the layout.
    fig_size : numpy.ndarray
        The size of the figure in inches as a NumPy array.

    Methods
    --------------------
    get_axis_position()
        Returns the position of the axis in normalized figure coordinates.
    get_axis_size()
        Returns the size of the axis in normalized figure coordinates.
    get_axis_position_inches()
        Returns the position of the axis in physical units (inches).
    get_axis_size_inches()
        Returns the size of the axis in physical units (inches).

    Examples
    --------------------
    >>> fig, ax = plt.subplots()
    >>> layout = AxisLayout(ax)
    >>> position = layout.get_axis_position()
    >>> size = layout.get_axis_size()
    >>> position_inches = layout.get_axis_position_inches()
    """

    def __init__(self, ax: Axes) -> None:
        self.ax: Axes = ax
        self.fig_size: NDArray[Any] = FigureLayout().get_figure_size()

    def get_axis_position(self) -> Bbox:
        """
        Retrieves the position of the axis in normalized figure coordinates.

        Returns
        --------------------
        matplotlib.transforms.Bbox
            The position of the axis as a bounding box in normalized coordinates.

        Examples
        --------------------
        >>> layout = AxisLayout(axis_index=0)
        >>> position = layout.get_axis_position()
        >>> print(position)
        Bbox(x0=0.1, y0=0.1, x1=0.9, y1=0.9)
        """
        axis_position = self.ax.get_position()
        return axis_position

    def get_axis_size(self) -> NDArray[Any]:
        """
        Retrieves the size of the axis in normalized figure coordinates.

        Returns
        --------------------
        numpy.ndarray
            The width and height of the axis as a NumPy array.

        Examples
        --------------------
        >>> layout = AxisLayout(axis_index=0)
        >>> size = layout.get_axis_size()
        >>> print(size)
        array([0.8, 0.8])
        """
        axis_position_size = np.array(self.get_axis_position().size)
        return axis_position_size

    def get_axis_position_inches(self) -> Bbox:
        """
        Retrieves the position of the axis in physical units (inches).

        Returns
        --------------------
        matplotlib.transforms.Bbox
            The position of the axis as a bounding box in inches.

        Examples
        --------------------
        >>> layout = AxisLayout(axis_index=0)
        >>> position_inches = layout.get_axis_position_inches()
        >>> print(position_inches)
        Bbox(x0=1.6, y0=1.6, x1=14.4, y1=14.4)
        """

        axis_position = self.get_axis_position()

        axis_position_inches = Bbox.from_bounds(
            axis_position.x0 * self.fig_size[0],
            axis_position.y0 * self.fig_size[1],
            axis_position.width * self.fig_size[0],
            axis_position.height * self.fig_size[1],
        )
        return axis_position_inches

    def get_axis_size_inches(self) -> NDArray[Any]:
        """
        Retrieves the size of the axis in physical units (inches).

        Returns
        --------------------
        numpy.ndarray
            The width and height of the axis in inches as a NumPy array.

        Examples
        --------------------
        >>> layout = AxisLayout(axis_index=0)
        >>> size_inches = layout.get_axis_size_inches()
        >>> print(size_inches)
        array([12.8, 12.8])
        """
        axis_position_size_inches = np.array(self.get_axis_position_inches().size)
        return axis_position_size_inches
