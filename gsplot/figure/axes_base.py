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


# class AxesResolver:
#     """
#     Resolves an axis target to a Matplotlib `Axes` object or its index.
#
#     This class provides a mechanism to convert an axis target, which can be either
#     an integer (index of the axis) or an `Axes` object, into a consistent representation
#     including the corresponding `Axes` object and its index within the current figure.
#
#     Parameters
#     --------------------
#     axis_target : int or matplotlib.axes.Axes
#         The target axis to resolve. Can be an integer representing the index of the
#         axis in the current figure or a specific `Axes` object.
#
#     Attributes
#     --------------------
#     axis_target : int or matplotlib.axes.Axes
#         The input target axis (as provided by the user).
#     _axis_index : int or None
#         The resolved index of the target axis in the current figure.
#     _axis : matplotlib.axes.Axes or None
#         The resolved `Axes` object corresponding to the target.
#
#     Methods
#     --------------------
#     _resolve_type()
#         Resolves the type of the axis target and retrieves the corresponding
#         `Axes` object and its index.
#     axis_index
#         Returns the resolved index of the axis.
#     axis
#         Returns the resolved `Axes` object.
#
#     Raises
#     --------------------
#     IndexError
#         If the provided axis index is out of range for the current figure.
#     ValueError
#         If the axis target is neither an integer nor an `Axes` object.
#
#     Examples
#     --------------------
#     >>> import matplotlib.pyplot as plt
#     >>> fig, axs = plt.subplots(2, 2)
#     >>> resolver = AxesResolver(1)  # Resolves the second axis (index 1)
#     >>> print(resolver.axis)
#     AxesSubplot(0.5,0.5;0.352273x0.352273)
#
#     >>> resolver = AxesResolver(axs[0, 0])  # Resolves an Axes object directly
#     >>> print(resolver.axis_index)
#     0
#     """
#
#     def __init__(self, axis_target: int | Axes) -> None:
#         self.axis_target: int | Axes = axis_target
#
#         self._axis_index: int | None = None
#         self._axis: Axes | None = None
#
#         self._resolve_type()
#
#     def _resolve_type(self) -> None:
#         """
#         Resolves the type of the axis target and retrieves the corresponding
#         `Axes` object and its index.
#
#         Raises
#         --------------------
#         IndexError
#             If the provided axis index is out of range for the current figure.
#         ValueError
#             If the axis target is neither an integer nor an `Axes` object.
#         """
#
#         def ordinal_suffix(n: int) -> str:
#             if 11 <= n % 100 <= 13:
#                 suffix = "th"
#             else:
#                 suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
#             return f"{n}{suffix}"
#
#         if isinstance(self.axis_target, int):
#             self._axis_index = self.axis_target
#             axes = plt.gcf().axes
#             try:
#                 self._axis = axes[self._axis_index]
#             except IndexError:
#                 error_message = f"Axes out of range: {self._axis_index} => Number of axes: {len(axes)}, but requested {ordinal_suffix(self._axis_index + 1)} axis."
#                 raise IndexError(error_message)
#         elif isinstance(self.axis_target, Axes):
#             self._axis = self.axis_target
#             if self.axis_target in plt.gcf().axes:
#                 self._axis_index = plt.gcf().axes.index(self._axis)
#             else:
#                 # Add the axis to the current figure if it is not present
#                 plt.gcf().add_axes(self._axis)
#                 self._axis_index = len(plt.gcf().axes) - 1
#         else:
#             raise ValueError(
#                 "Invalid axis target. Please provide an integer or Axes object."
#             )
#
#     @property
#     def axis_index(self) -> int:
#         """
#         Returns the resolved index of the target axis.
#
#         Returns
#         --------------------
#         int
#             The index of the resolved axis.
#
#         Raises
#         --------------------
#         ValueError
#             If the axis index is not resolved.
#         """
#         if isinstance(self._axis_index, int):
#             return self._axis_index
#         else:
#             raise ValueError("Axis index not resolved. Please check the AxisResolver")
#
#     @property
#     def axis(self) -> Axes:
#         """
#         Returns the resolved `Axes` object.
#
#         Returns
#         --------------------
#         matplotlib.axes.Axes
#             The resolved `Axes` object.
#
#         Raises
#         --------------------
#         ValueError
#             If the axis is not resolved.
#         """
#         if isinstance(self._axis, Axes):
#             return self._axis
#         else:
#             raise ValueError("Axis not resolced. Please check the AxisResolver")


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
