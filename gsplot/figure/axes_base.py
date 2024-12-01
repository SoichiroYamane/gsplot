from __future__ import annotations

import threading
from typing import Any, Callable, TypeVar, cast

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.transforms import Bbox
from numpy.typing import NDArray

from .figure_tools import FigureLayout

F = TypeVar("F", bound=Callable[..., Any])


class AxesResolver:
    def __init__(self, axis_target: int | Axes) -> None:
        self.axis_target: int | Axes = axis_target

        self._axis_index: int | None = None
        self._axis: Axes | None = None

        self._resolve_type()

    def _resolve_type(self) -> None:
        def ordinal_suffix(n: int) -> str:
            if 11 <= n % 100 <= 13:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            return f"{n}{suffix}"

        if isinstance(self.axis_target, int):
            self._axis_index = self.axis_target
            axes = plt.gcf().axes
            try:
                self._axis = axes[self._axis_index]
            except IndexError:
                error_message = f"Axes out of range: {self._axis_index} => Number of axes: {len(axes)}, but requested {ordinal_suffix(self._axis_index + 1)} axis."
                raise IndexError(error_message)

        elif isinstance(self.axis_target, Axes):
            self._axis = self.axis_target
            self._axis_index = plt.gcf().axes.index(self._axis)
        else:
            raise ValueError(
                "Invalid axis target. Please provide an integer or Axes object."
            )

    @property
    def axis_index(self) -> int:
        if isinstance(self._axis_index, int):
            return self._axis_index
        else:
            raise ValueError("Axis index not resolved. Please check the AxisResolver")

    @property
    def axis(self) -> Axes:
        if isinstance(self._axis, Axes):
            return self._axis
        else:
            raise ValueError("Axis not resolced. Please check the AxisResolver")


class AxesRangeSingleton:

    _instance: AxesRangeSingleton | None = None
    _lock: threading.Lock = threading.Lock()  # Lock to ensure thread safety

    def __new__(cls) -> "AxesRangeSingleton":
        with cls._lock:  # Ensure thread safety
            if cls._instance is None:
                cls._instance = super(AxesRangeSingleton, cls).__new__(cls)
                cls._instance._initialize_axes_ranges()
        return cls._instance

    def _initialize_axes_ranges(self) -> None:

        # Explicitly initialize the instance variable with a type hint
        self._axes_ranges: list[list[Any]] = [[None, None]]

    def ensure_size_of_axes_ranges(self) -> None:

        axes = plt.gcf().axes
        axes_length = len(axes)
        num_elements_to_append = max(0, axes_length - len(self._axes_ranges))
        self._axes_ranges.extend([[None, None]] * num_elements_to_append)

    @property
    def axes_ranges(self) -> list[list[Any]]:

        self.ensure_size_of_axes_ranges()
        return self._axes_ranges

    @axes_ranges.setter
    def axes_ranges(
        self,
        axes_ranges: list[list[Any]],
    ) -> None:

        try:
            iter(axes_ranges)
        except TypeError:
            raise TypeError(f"Expected an iterable, got {type(axes_ranges).__name__}")
        self._axes_ranges = axes_ranges

    def add_range(
        self, axis_index: int, xrange: np.ndarray, yrange: np.ndarray
    ) -> None:

        while len(self._axes_ranges) <= axis_index:
            self._axes_ranges.append([None, None])
        self._axes_ranges[axis_index] = [xrange, yrange]

    def _get_wider_range(self, range1: np.ndarray, range2: np.ndarray) -> np.ndarray:

        new_range = np.array([min(range1[0], range2[0]), max(range1[1], range2[1])])
        return new_range

    def get_max_wo_inf(self, array: np.ndarray) -> float:

        array = np.array(array)
        array = array[array != np.inf]
        return float(np.nanmax(array))

    def get_min_wo_inf(self, array: np.ndarray) -> float:

        array = np.array(array)
        array = array[array != -np.inf]
        return float(np.nanmin(array))

    @classmethod
    def update(cls, func: F) -> F:
        def wrapper(self, *args: Any, **kwargs: Any) -> Any:
            axis_index: int = self.axis_index
            x: np.ndarray = self.x
            y: np.ndarray = self.y

            num_elements_to_append = max(0, axis_index + 1 - len(cls().axes_ranges))
            cls().axes_ranges.extend([[None, None]] * num_elements_to_append)

            xrange, yrange = AxisRangeHandler(axis_index, x, y).get_new_axis_range()
            xrange = np.array([cls().get_min_wo_inf(x), cls().get_max_wo_inf(x)])
            yrange = np.array([cls().get_min_wo_inf(y), cls().get_max_wo_inf(y)])

            xrange_singleton = cls().axes_ranges[axis_index][0]
            yrange_singleton = cls().axes_ranges[axis_index][1]

            if xrange_singleton is not None:
                new_xrange = cls()._get_wider_range(xrange, xrange_singleton)
            else:
                new_xrange = xrange

            if yrange_singleton is not None:
                new_yrange = cls()._get_wider_range(yrange, yrange_singleton)
            else:
                new_yrange = yrange

            cls().add_range(axis_index, new_xrange, new_yrange)

            result = func(self, *args, **kwargs)
            return result

        return cast(F, wrapper)

    def reset(self, axes: list[Axes]):
        axes_length = len(axes)
        self._axes_ranges = [[None, None]] * axes_length


class AxisLayout:
    def __init__(self, axis_index: int) -> None:
        self.axis_index = axis_index
        self.axis: Axes = AxesResolver(self.axis_index).axis

        self.fig_size: np.ndarray = FigureLayout().get_figure_size()

    def get_axis_position(self) -> Bbox:
        axis_position = self.axis.get_position()
        return axis_position

    def get_axis_size(self) -> np.ndarray:
        axis_position_size = np.array(self.get_axis_position().size)
        return axis_position_size

    def get_axis_position_inches(self) -> Bbox:
        axis_position = self.get_axis_position()

        axis_position_inches = Bbox.from_bounds(
            axis_position.x0 * self.fig_size[0],
            axis_position.y0 * self.fig_size[1],
            axis_position.width * self.fig_size[0],
            axis_position.height * self.fig_size[1],
        )
        return axis_position_inches

    def get_axis_size_inches(self) -> np.ndarray:
        axis_position_size_inches = np.array(self.get_axis_position_inches().size)
        return axis_position_size_inches


class AxisRangeController:

    def __init__(self, axis_index: int):
        self.axis_index = axis_index
        self.axis: Axes = AxesResolver(self.axis_index).axis

    def get_axis_xrange(self) -> np.ndarray:

        axis_xrange: np.ndarray = np.array(self.axis.get_xlim())
        return axis_xrange

    def get_axis_yrange(self) -> np.ndarray:

        axis_yrange: np.ndarray = np.array(self.axis.get_ylim())
        return axis_yrange

    def set_axis_xrange(self, xrange: np.ndarray) -> None:

        xrange_tuple = tuple(xrange)
        self.axis.set_xlim(xrange_tuple)

    def set_axis_yrange(self, yrange: np.ndarray) -> None:

        yrange_tuple = tuple(yrange)
        self.axis.set_ylim(yrange_tuple)


class AxisRangeManager:

    def __init__(self, axis_index: int):
        self.axis_index = axis_index

        self.axis: Axes = AxesResolver(self.axis_index).axis

    def is_init_axis(self) -> bool:
        num_lines = len(self.axis.lines)

        if num_lines:
            return False
        else:
            return True


class AxisRangeHandler:

    def __init__(self, axis_index: int, xdata: np.ndarray, ydata: np.ndarray):
        self.axis_index = axis_index
        self.xdata = xdata
        self.ydata = ydata

        self.axis: Axes = AxesResolver(self.axis_index).axis

        self._is_init_axis: bool = AxisRangeManager(self.axis_index).is_init_axis()

    def _get_axis_range(
        self,
    ) -> tuple[NDArray | None, NDArray | None] | None:

        if self._is_init_axis:
            return None, None
        else:
            axis_xrange = AxisRangeController(self.axis_index).get_axis_xrange()
            axis_yrange = AxisRangeController(self.axis_index).get_axis_yrange()
            return axis_xrange, axis_yrange

    def _calculate_data_range(self, data: np.ndarray) -> np.ndarray:

        min_data = np.min(data)
        max_data = np.max(data)
        return np.array([min_data, max_data])

    def get_new_axis_range(
        self,
    ) -> tuple[NDArray | None, NDArray | None]:

        axis_range = self._get_axis_range()
        if axis_range is None:
            return None, None

        xrange, yrange = axis_range
        xrange_data, yrange_data = (
            self._calculate_data_range(self.xdata),
            self._calculate_data_range(self.ydata),
        )

        if xrange is None:
            new_xrange = xrange_data
        else:
            new_xrange = np.array([xrange[0], xrange[1]])

        if yrange is None:
            new_yrange = yrange_data
        else:
            new_yrange = np.array([yrange[0], yrange[1]])

        if xrange is not None and yrange is not None:
            new_xrange = np.array(
                [min(xrange[0], xrange_data[0]), max(xrange[1], xrange_data[1])]
            )
            new_yrange = np.array(
                [min(yrange[0], yrange_data[0]), max(yrange[1], yrange_data[1])]
            )

        return new_xrange, new_yrange
