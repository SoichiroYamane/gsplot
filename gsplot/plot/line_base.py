from __future__ import annotations

import threading
from typing import Any, Callable, TypeVar, cast

import numpy as np
from numpy.typing import NDArray

from ..color.colormap import Colormap

F = TypeVar("F", bound=Callable[..., Any])

__all__: list[str] = []


class NumLines:
    """
    A thread-safe singleton class to track the number of lines plotted on each axis.

    This class maintains a count of the number of lines plotted on specific axes in a
    Matplotlib figure. It uses a thread-safe singleton pattern to ensure a single instance
    across the application. It also provides a decorator to automatically increment the
    line count when a plotting function is called.

    Attributes
    --------------------
    num_lines : list[int]
        A list where each index represents an axis, and the value is the number of lines
        plotted on that axis.

    Methods
    --------------------
    num_lines_axis(axis_index)
        Retrieves the number of lines plotted on a specific axis.
    increment(axis_index)
        Increments the line count for a specific axis.
    count(func)
        A decorator to increment the line count whenever a plotting function is called.
    reset()
        Resets the singleton instance, clearing all line counts.

    Examples
    --------------------
    >>> num_lines = NumLines()
    >>> print(num_lines.num_lines_axis(0))
    0  # No lines plotted yet

    >>> num_lines.increment(0)  # Increment the count for axis 0
    >>> print(num_lines.num_lines_axis(0))
    1

    >>> @NumLines.count
    ... def plot_line(axis_index):
    ...     print(f"Plotting on axis {axis_index}")
    >>> plot_line(0)
    Plotting on axis 0
    >>> print(num_lines.num_lines_axis(0))
    2
    """

    _instance: NumLines | None = None
    _lock: threading.Lock = threading.Lock()  # Lock to ensure thread safety

    def __new__(cls) -> "NumLines":
        with cls._lock:  # Ensure thread safety
            if cls._instance is None:
                cls._instance = super(NumLines, cls).__new__(cls)
                cls._instance._initialize_num_lines()
        return cls._instance

    def _initialize_num_lines(self) -> None:
        """
        Initializes the line count to its default value ([0]).
        """
        # Explicitly initialize the instance variable with a type hint
        self._num_lines: list[int] = [0]

    def update_num_lines(self, axis_index: int) -> None:
        """
        Ensures the line count list is large enough to include the given axis index.

        Parameters
        --------------------
        axis_index : int
            The index of the axis to update.
        """
        length = len(self._num_lines)
        if axis_index + 1 > length:
            self._num_lines.extend([0] * (axis_index - length + 1))

    @property
    def num_lines(self) -> list[int]:
        """
        Retrieves the list of line counts for all axes.

        Returns
        --------------------
        list[int]
            The list of line counts, where each index corresponds to an axis.

        Examples
        --------------------
        >>> num_lines = NumLines()
        >>> print(num_lines.num_lines)
        [0]
        """
        return self._num_lines

    def num_lines_axis(self, axis_index: int) -> int:
        """
        Retrieves the number of lines plotted on a specific axis.

        Parameters
        --------------------
        axis_index : int
            The index of the axis.

        Returns
        --------------------
        int
            The number of lines plotted on the specified axis.

        Examples
        --------------------
        >>> num_lines = NumLines()
        >>> print(num_lines.num_lines_axis(0))
        0
        """
        self.update_num_lines(axis_index)
        return self._num_lines[axis_index]

    def increment(self, axis_index: int) -> None:
        """
        Increments the line count for a specific axis.

        Parameters
        --------------------
        axis_index : int
            The index of the axis.

        Examples
        --------------------
        >>> num_lines = NumLines()
        >>> num_lines.increment(0)
        >>> print(num_lines.num_lines_axis(0))
        1
        """
        self.update_num_lines(axis_index)
        self._num_lines[axis_index] += 1

    @classmethod
    def count(cls, func: F) -> F:
        """
        A decorator to increment the line count whenever a plotting function is called.

        Parameters
        --------------------
        func : Callable
            The function to decorate.

        Returns
        --------------------
        Callable
            The decorated function.

        Examples
        --------------------
        >>> @NumLines.count
        ... def plot_line(axis_index):
        ...     print(f"Plotting on axis {axis_index}")
        >>> plot_line(0)
        Plotting on axis 0
        >>> num_lines = NumLines()
        >>> print(num_lines.num_lines_axis(0))
        1
        """

        def wrapper(self, *args: Any, **kwargs: Any) -> Any:
            cls().increment(self.axis_index)
            result = func(self, *args, **kwargs)
            return result

        return cast(F, wrapper)

    @classmethod
    def reset(cls) -> None:
        """
        Resets the singleton instance, clearing all line counts.

        Examples
        --------------------
        >>> num_lines = NumLines()
        >>> num_lines.increment(0)
        >>> print(num_lines.num_lines_axis(0))
        1
        >>> NumLines.reset()
        >>> num_lines = NumLines()
        >>> print(num_lines.num_lines_axis(0))
        0
        """
        cls._instance = None


class AutoColor:
    """
    A utility class for generating colors automatically based on the axis index and line count.

    This class uses a predefined colormap and cycles through colors based on the number of lines
    already plotted on the target axis. The default colormap is "viridis", and it is divided
    into a specified number of discrete colors.

    Parameters
    --------------------
    axis_index : int
        The index of the target axis in the current figure.

    Attributes
    --------------------
    COLORMAP_LENGTH : int
        The number of discrete colors in the colormap (default is 5).
    CMAP : str
        The name of the Matplotlib colormap to use (default is "viridis").
    colormap : numpy.ndarray
        An array of RGB colors derived from the specified colormap.
    num_lines_axis : int
        The number of lines already plotted on the target axis.
    cycle_color_index : int
        The index of the color to use for the next line, calculated using modulo arithmetic.

    Methods
    --------------------
    get_color()
        Retrieves the next color from the colormap based on the current line count.

    Examples
    --------------------
    >>> auto_color = AutoColor(axis_index=0)
    >>> color = auto_color.get_color()
    >>> print(color)
    array([0.267004, 0.004874, 0.329415, 1.0])  # Example RGBA color from the colormap
    """

    def __init__(self, axis_index: int) -> None:
        self.COLORMAP_LENGTH: int = 5
        self.CMAP = "viridis"
        self.colormap: NDArray[Any] = Colormap(
            cmap=self.CMAP, N=self.COLORMAP_LENGTH
        ).get_split_cmap()

        self.num_lines_axis: int = NumLines().num_lines_axis(axis_index)
        self.cycle_color_index: int = self.num_lines_axis % self.COLORMAP_LENGTH

    def get_color(self) -> NDArray[Any]:
        """
        Retrieves the next color from the colormap based on the current line count.

        This method determines the appropriate color for the next line to be plotted
        on the target axis by cycling through the discrete colormap.

        Returns
        --------------------
        numpy.ndarray
            An array representing the RGBA color for the next line.

        Examples
        --------------------
        >>> auto_color = AutoColor(axis_index=0)
        >>> color = auto_color.get_color()
        >>> print(color)
        array([0.267004, 0.004874, 0.329415, 1.0])  # Example RGBA color
        """
        return np.array(self.colormap[self.cycle_color_index])
