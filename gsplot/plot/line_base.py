from __future__ import annotations

import threading
from typing import Any, Callable, TypeVar, cast

import numpy as np
from numpy.typing import NDArray

from ..color.colormap import Colormap

F = TypeVar("F", bound=Callable[..., Any])

__all__: list[str] = []


class NumLines:

    _instance: NumLines | None = None
    _lock: threading.Lock = threading.Lock()  # Lock to ensure thread safety

    def __new__(cls) -> "NumLines":
        with cls._lock:  # Ensure thread safety
            if cls._instance is None:
                cls._instance = super(NumLines, cls).__new__(cls)
                cls._instance._initialize_num_lines()
        return cls._instance

    def _initialize_num_lines(self) -> None:

        # Explicitly initialize the instance variable with a type hint
        self._num_lines: list[int] = [0]

    def update_num_lines(self, axis_index: int) -> None:

        length = len(self._num_lines)
        if axis_index + 1 > length:
            self._num_lines.extend([0] * (axis_index - length + 1))

    @property
    def num_lines(self) -> list[int]:

        return self._num_lines

    def num_lines_axis(self, axis_index: int) -> int:

        self.update_num_lines(axis_index)
        return self._num_lines[axis_index]

    def increment(self, axis_index: int) -> None:

        self.update_num_lines(axis_index)
        self._num_lines[axis_index] += 1

    @classmethod
    def count(cls, func: F) -> F:

        def wrapper(self, *args: Any, **kwargs: Any) -> Any:
            cls().increment(self.axis_index)
            result = func(self, *args, **kwargs)
            return result

        return cast(F, wrapper)

    @classmethod
    def reset(cls) -> None:

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
        self.colormap: NDArray[Any] = Colormap(
            cmap=self.CMAP, N=self.COLORMAP_LENGTH
        ).get_split_cmap()

        self.num_lines_axis: int = NumLines().num_lines_axis(axis_index)
        self.cycle_color_index: int = self.num_lines_axis % self.COLORMAP_LENGTH

    def get_color(self) -> NDArray[Any]:
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
