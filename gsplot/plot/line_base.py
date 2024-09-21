import numpy as np
from typing import List, Any, Optional

from ..color.colormap import Colormap


class NumLines:
    """
    A singleton class to track the number of lines plotted on each axis.

    The `NumLines` class manages and tracks the number of lines that have been plotted on
    various axes. It ensures that the count is accurate and consistent across different axes.

    Attributes
    ----------
    _instance : Optional[NumLines]
        The singleton instance of the `NumLines` class.
    _num_lines : list[int]
        A list that tracks the number of lines for each axis.

    Methods
    -------
    num_lines_axis(axis_index: int) -> int
        Returns the number of lines plotted on the specified axis.
    increment(axis_index: int) -> None
        Increments the line count for the specified axis.
    count(func: Any) -> Any
        A decorator that increments the line count before executing the wrapped function.
    reset() -> None
        Resets the singleton instance, clearing all counts.
    """

    _instance: Optional["NumLines"] = None

    def __new__(cls) -> "NumLines":
        if cls._instance is None:
            cls._instance = super(NumLines, cls).__new__(cls)
            cls._instance._initialize_num_lines()
        return cls._instance

    def _initialize_num_lines(self) -> None:
        """
        Initializes the line count list.

        This method sets up the internal list `_num_lines` that tracks the number of lines
        for each axis, initializing it with a single count set to zero.
        """

        # Explicitly initialize the instance variable with a type hint
        self._num_lines: list[int] = [0]

    def update_num_lines(self, axis_index: int) -> None:
        """
        Ensures that the `_num_lines` list can accommodate the specified axis index.

        Parameters
        ----------
        axis_index : int
            The index of the axis for which to update the line count list.
        """

        length = len(self._num_lines)
        if axis_index + 1 > length:
            self._num_lines.extend([0] * (axis_index - length + 1))

    @property
    def num_lines(self) -> list[int]:
        """
        Returns the current list of line counts for all axes.

        Returns
        -------
        list[int]
            A list where each element represents the number of lines plotted on the corresponding axis.
        """

        return self._num_lines

    def num_lines_axis(self, axis_index: int) -> int:
        """
        Returns the number of lines plotted on the specified axis.

        Parameters
        ----------
        axis_index : int
            The index of the axis for which to retrieve the line count.

        Returns
        -------
        int
            The number of lines plotted on the specified axis.
        """

        self.update_num_lines(axis_index)
        return self._num_lines[axis_index]

    def increment(self, axis_index: int) -> None:
        """
        Increments the line count for the specified axis.

        Parameters
        ----------
        axis_index : int
            The index of the axis for which to increment the line count.
        """

        self.update_num_lines(axis_index)
        self._num_lines[axis_index] += 1

    @classmethod
    def count(cls, func) -> Any:
        """
        A decorator to increment the line count for the axis before calling the function.

        This decorator increments the line count for the `axis_index` attribute of the class
        instance (`self`) before executing the wrapped plotting function.

        Parameters
        ----------
        func : Any
            The function to be wrapped by the decorator.

        Returns
        -------
        Any
            The wrapped function.
        """

        def wrapper(self, *args, **kwargs):
            cls().increment(self.axis_target)
            result = func(self, *args, **kwargs)
            return result

        return wrapper

    @classmethod
    def reset(cls) -> None:
        """
        Resets the singleton instance, clearing all line counts.

        This method resets the singleton instance of the `NumLines` class, effectively clearing
        all line counts for all axes.
        """

        cls._instance = None


class AutoColor:
    """
    A class to automatically assign colors to lines based on the number of lines already plotted.

    The `AutoColor` class uses a colormap to assign a color to each new line plotted on a specific axis.
    The color is chosen based on the number of lines already plotted on that axis, cycling through a
    predefined colormap.

    Parameters
    ----------
    axis_index : int
        The index of the axis for which the color is to be determined.

    Attributes
    ----------
    COLORMAP_LENGTH : int
        The number of colors in the colormap.
    CMAP : str
        The name of the colormap to use (default is "viridis").
    colormap : np.ndarray
        An array of colors generated from the specified colormap.
    num_lines_axis : int
        The current number of lines on the specified axis.
    cycle_color_index : int
        The index of the color to be used for the next line, based on the number of lines already plotted.

    Methods
    -------
    get_color() -> np.ndarray
        Returns the color to be used for the next line.
    """

    def __init__(self, axis_index: int) -> None:
        self.COLORMAP_LENGTH: int = 5
        self.CMAP = "viridis"
        self.colormap: np.ndarray = Colormap(
            cmap=self.CMAP, N=self.COLORMAP_LENGTH
        ).get_split_cmap()

        self.num_lines_axis: int = NumLines().num_lines_axis(axis_index)
        self.cycle_color_index: int = self.num_lines_axis % self.COLORMAP_LENGTH

    def get_color(self) -> np.ndarray:
        """
        Returns the color to be used for the next line.

        This method returns a color from the colormap based on the number of lines already plotted on the axis.
        It cycles through the colors in the colormap.

        Returns
        -------
        np.ndarray
            The RGBA color as a NumPy array to be used for the next line.
        """

        return np.array(self.colormap[self.cycle_color_index])
