import numpy as np
from typing import List, Any, Optional

from ..color.colormap import Colormap


class NumLines:
    _instance: Optional["NumLines"] = None

    def __new__(cls) -> "NumLines":
        if cls._instance is None:
            cls._instance = super(NumLines, cls).__new__(cls)
            cls._instance._initialize_num_lines()
        return cls._instance

    def _initialize_num_lines(self) -> None:
        # Explicitly initialize the instance variable with a type hint
        self._num_lines: List[int] = [0]

    def update_num_lines(self, axis_index: int) -> None:
        length = len(self._num_lines)
        if axis_index + 1 > length:
            self._num_lines.extend([0] * (axis_index - length + 1))

    @property
    def num_lines(self) -> List[int]:
        return self._num_lines

    def num_lines_axis(self, axis_index: int) -> int:
        self.update_num_lines(axis_index)
        return self._num_lines[axis_index]

    def increment(self, axis_index: int) -> None:
        self.update_num_lines(axis_index)
        self._num_lines[axis_index] += 1

    @classmethod
    def count(cls, func) -> Any:
        def wrapper(self, *args, **kwargs):
            cls().increment(self.axis_index)
            result = func(self, *args, **kwargs)
            return result

        return wrapper

    @classmethod
    def reset(cls) -> None:
        cls._instance = None


class AutoColor:
    def __init__(self, axis_index: int) -> None:
        self.COLORMAP_LENGTH: int = 5
        self.CMAP = "viridis"
        self.colormap: np.ndarray = Colormap(
            cmap=self.CMAP, N=self.COLORMAP_LENGTH
        ).get_split_cmap()

        self.num_lines_axis: int = NumLines().num_lines_axis(axis_index)
        self.cycle_color_index: int = self.num_lines_axis % self.COLORMAP_LENGTH

    def get_color(self) -> np.ndarray:
        return np.array(self.colormap[self.cycle_color_index])
