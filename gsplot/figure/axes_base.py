from typing import List, Any, Optional, Union, Tuple

import numpy as np
from matplotlib.transforms import Bbox
from matplotlib.axes import Axes

from .figure_tool import FigureLayout


class AxesSingleton:
    _instance: Optional["AxesSingleton"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AxesSingleton, cls).__new__(cls)
            cls._instance._initialize_axes()
        return cls._instance

    def _initialize_axes(self) -> None:
        # Explicitly initialize the instance variable with a type hint
        self._axes: List[Axes] = []

    @property
    def axes(self) -> List[Axes]:
        return self._axes

    @axes.setter
    def axes(self, axes: List[Axes]) -> None:
        try:
            iter(axes)
        except TypeError:
            raise TypeError(f"Expected an iterable, got {type(axes).__name__}")
        self._axes = axes

    def get_axis(self, axis_index: int) -> Axes:
        def ordinal_suffix(n):
            if 11 <= n % 100 <= 13:
                suffix = "th"
            else:
                suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            return f"{n}{suffix}"

        try:
            axis = self._axes[axis_index]
            return axis

        except IndexError:
            error_message = f"Axes out of range: {axis_index} => Number of axes: {len(self._axes)}, but requested {ordinal_suffix(axis_index + 1)} axis."
            raise IndexError(error_message)


class AxesRangeSingleton:
    _instance: Optional["AxesRangeSingleton"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AxesRangeSingleton, cls).__new__(cls)
            cls._instance._initialize_axes_ranges()
        return cls._instance

    def _initialize_axes_ranges(self) -> None:
        # Explicitly initialize the instance variable with a type hint
        self._axes_ranges: List[List[Any]] = [[None, None]]

    @property
    def axes_ranges(self) -> List[List[Any]]:
        return self._axes_ranges

    @axes_ranges.setter
    def axes_ranges(
        self,
        axes_ranges: List[List[Any]],
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

    @classmethod
    def update(cls, func: Any) -> Any:
        def wrapper(self, *args, **kwargs) -> Any:
            axis_index: int = self.axis_index
            xdata: np.ndarray = self.xdata
            ydata: np.ndarray = self.ydata

            num_elements_to_append = max(0, axis_index + 1 - len(cls().axes_ranges))
            cls().axes_ranges.extend([[None, None]] * num_elements_to_append)

            xrange, yrange = AxisRangeHandler(
                axis_index, xdata, ydata
            ).get_new_axis_range()
            xrange = np.array([np.nanmin(xdata), np.nanmax(xdata)])
            yrange = np.array([np.nanmin(ydata), np.nanmax(ydata)])

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

        return wrapper

    def reset(self, axes: List[Axes]):
        axes_length = len(axes)
        self._axes_ranges = [[None, None]] * axes_length


class AxisLayout:
    def __init__(self, axis_index: int):
        self.axis_index = axis_index
        self.__axes: AxesSingleton = AxesSingleton()
        self._axes: List[Axes] = self.__axes.axes
        self.axis: Axes = self.__axes.get_axis(self.axis_index)

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
        self.__axes: AxesSingleton = AxesSingleton()
        self._axes: List[Axes] = self.__axes.axes
        self.axis: Axes = self.__axes.get_axis(self.axis_index)

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

        self.__axes: AxesSingleton = AxesSingleton()
        self._axes: List[Axes] = self.__axes.axes

        self.axis: Axes = self.__axes.get_axis(self.axis_index)

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

        self.__axes: AxesSingleton = AxesSingleton()
        self._axes: List[Axes] = self.__axes.axes
        self.axis: Axes = self.__axes.get_axis(self.axis_index)

        self._is_init_axis: bool = AxisRangeManager(self.axis_index).is_init_axis()

    def _get_axis_range(
        self,
    ) -> Optional[Tuple[Union[np.ndarray, None], Union[np.ndarray, None]]]:
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
    ) -> Tuple[Union[np.ndarray, None], Union[np.ndarray, None]]:
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
