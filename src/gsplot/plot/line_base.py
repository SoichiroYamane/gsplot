from __future__ import annotations

import threading
from typing import Any, Callable, TypeVar, cast

import numpy as np
from matplotlib.axes import Axes
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
        The number of lines plotted on each axis.

    Methods
    --------------------
    num_lines_axis(ax)
        Retrieves the number of lines plotted on a specific axis.
    increment(ax)
        Increments the line count for a specific axis.
    count(func)
        A decorator to increment the line count whenever a plotting function is called.
    reset()
        Resets the singleton instance, clearing all line counts.

    Examples
    --------------------
    >>> num_lines = NumLines()
    >>> print(num_lines.num_lines_axis(axs[0]))
    0
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
        Initializes the line count to its default dictionary ({}).
        """
        # Explicitly initialize the instance variable with a type hint
        self._num_lines_dict: dict[Axes, int] = {}

    @property
    def num_lines_dict(self) -> dict[Axes, int]:
        """
        Retrieves the dictionary containing the number of lines plotted on each axis.

        Returns
        --------------------
        dict[matplotlib.axes.Axes, int]
            A dictionary where each key is an axis and the value is the number of lines plotted.

        Examples
        --------------------
        >>> num_lines = NumLines()
        >>> print(num_lines.num_lines_dict)
        """
        return self._num_lines_dict

    def num_lines(self, ax: Axes) -> int:
        """
        Retrieves the number of lines plotted on a specific axis.

        Parameters
        --------------------
        ax : matplotlib.axes.Axes
            The axis to query.

        Returns
        --------------------
        int
            The number of lines plotted on the specified axis.

        Examples
        --------------------
        >>> num_lines = NumLines()
        >>> print(num_lines.num_lines_axis(axs[0]))
        """
        if ax not in self._num_lines_dict:
            self._num_lines_dict[ax] = 0
        return self._num_lines_dict[ax]

    def increment(self, ax: Axes) -> None:
        """
        Increments the line count for a specific axis.

        Parameters
        --------------------
        ax : matplotlib.axes.Axes
            The axis to increment.

        Examples
        --------------------
        >>> num_lines = NumLines()
        >>> num_lines.increment(axs[1])
        """
        if ax not in self._num_lines_dict:
            self._num_lines_dict[ax] = 0
        self._num_lines_dict[ax] += 1

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
        >>> def plot():
        >>>     print("Plotting")
        """

        def wrapper(self, *args: Any, **kwargs: Any) -> Any:
            cls().increment(self.ax)
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
    A utility class for generating colors automatically based on line count.

    This class uses a predefined colormap and cycles through colors based on the number of lines
    already plotted on the target axis. The default colormap is "viridis", and it is divided
    into a specified number of discrete colors.

    Parameters
    --------------------
    ax : matplotlib.axes.Axes
        The target `Axes` object for which to generate colors

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

    def __init__(self, ax) -> None:
        self.ax: Axes = ax
        self.COLORMAP_LENGTH: int = 5
        self.CMAP = "viridis"
        self.colormap: NDArray[Any] = Colormap(
            cmap=self.CMAP, N=self.COLORMAP_LENGTH
        ).get_split_cmap()

        _num_lines = NumLines()
        self.num_lines: int = _num_lines.num_lines(self.ax)

        self.cycle_color_index: int = self.num_lines % self.COLORMAP_LENGTH

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
        >>> auto_color = AutoColor(ax)
        >>> color = auto_color.get_color()
        >>> print(color)
        array([0.267004, 0.004874, 0.329415, 1.0])  # Example RGBA color
        """
        return np.array(self.colormap[self.cycle_color_index])
