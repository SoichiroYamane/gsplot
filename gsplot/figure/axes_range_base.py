from __future__ import annotations

import threading
from typing import Any, Callable, TypeVar, cast

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from numpy.typing import NDArray

from .axes_base import AxesResolver

F = TypeVar("F", bound=Callable[..., Any])


class AxesRangeSingleton:
    """
    A thread-safe singleton class for managing axis ranges in Matplotlib figures.

    This class provides functionality to store and update axis ranges for all axes
    in a figure, ensuring consistency across different parts of the application.
    It maintains axis ranges for each axis and can dynamically extend or reset the stored ranges.

    Attributes
    --------------------
    _instance : AxesRangeSingleton or None
        The singleton instance of the `AxesRangeSingleton` class.
    _lock : threading.Lock
        A lock to ensure thread-safe access to the singleton instance.
    _axes_ranges : list of list[Any]
        A list storing ranges for each axis, where each range is represented as `[xrange, yrange]`.

    Methods
    --------------------
    axes_ranges
        Retrieves the list of axis ranges, ensuring its size matches the number of axes in the current figure.
    add_range(axis_index, xrange, yrange)
        Adds or updates the range for a specific axis.
    get_max_wo_inf(array)
        Returns the maximum value in an array, ignoring infinities.
    get_min_wo_inf(array)
        Returns the minimum value in an array, ignoring infinities.
    reset(axes)
        Resets the stored ranges to match the provided list of axes.
    update(func)
        A decorator to update axis ranges based on data and ensure consistency.

    Examples
    --------------------
    >>> axes_ranges = AxesRangeSingleton()
    >>> print(axes_ranges.axes_ranges)
    [[None, None]]

    >>> axes_ranges.add_range(0, np.array([0, 10]), np.array([0, 20]))
    >>> print(axes_ranges.axes_ranges)
    [array([0, 10]), array([0, 20])]

    >>> axes_ranges.reset(plt.gcf().axes)
    >>> print(axes_ranges.axes_ranges)
    [[None, None], [None, None]]  # Resets to the number of current figure axes
    """

    _instance: AxesRangeSingleton | None = None
    _lock: threading.Lock = threading.Lock()  # Lock to ensure thread safety

    def __new__(cls) -> "AxesRangeSingleton":
        with cls._lock:  # Ensure thread safety
            if cls._instance is None:
                cls._instance = super(AxesRangeSingleton, cls).__new__(cls)
                cls._instance._initialize_axes_ranges()
        return cls._instance

    def _initialize_axes_ranges(self) -> None:
        """
        Initializes the axis ranges storage with a default value.
        """

        # Explicitly initialize the instance variable with a type hint
        self._axes_ranges: list[list[Any]] = [[None, None]]

    def ensure_size_of_axes_ranges(self) -> None:
        """
        Ensures the `_axes_ranges` list matches the number of axes in the current figure.
        """

        axes = plt.gcf().axes
        axes_length = len(axes)
        num_elements_to_append = max(0, axes_length - len(self._axes_ranges))
        self._axes_ranges.extend([[None, None]] * num_elements_to_append)

    @property
    def axes_ranges(self) -> list[list[Any]]:
        """
        Retrieves the list of axis ranges, ensuring its size matches the number of axes.

        Returns
        --------------------
        list of list[Any]
            The list of axis ranges.
        """

        self.ensure_size_of_axes_ranges()
        return self._axes_ranges

    @axes_ranges.setter
    def axes_ranges(
        self,
        axes_ranges: list[list[Any]],
    ) -> None:
        """
        Sets the axis ranges to a new list.

        Parameters
        --------------------
        axes_ranges : list of list[Any]
            The new axis ranges to set.

        Raises
        --------------------
        TypeError
            If the provided value is not iterable.
        """

        try:
            iter(axes_ranges)
        except TypeError:
            raise TypeError(f"Expected an iterable, got {type(axes_ranges).__name__}")
        self._axes_ranges = axes_ranges

    def add_range(
        self, axis_index: int, xrange: NDArray[Any], yrange: NDArray[Any]
    ) -> None:
        """
        Adds or updates the range for a specific axis.

        Parameters
        --------------------
        axis_index : int
            The index of the axis to update.
        xrange : numpy.ndarray
            The range for the x-axis.
        yrange : numpy.ndarray
            The range for the y-axis.

        Examples
        --------------------
        >>> axes_ranges = AxesRangeSingleton()
        >>> axes_ranges.add_range(0, np.array([0, 10]), np.array([0, 20]))
        >>> print(axes_ranges.axes_ranges)
        [[array([ 0, 10]), array([ 0, 20])]]
        """
        while len(self._axes_ranges) <= axis_index:
            self._axes_ranges.append([None, None])
        self._axes_ranges[axis_index] = [xrange, yrange]

    def _get_wider_range(
        self, range1: NDArray[Any], range2: NDArray[Any]
    ) -> NDArray[Any]:
        """
        Computes the wider range encompassing two given ranges.

        Parameters
        --------------------
        range1 : numpy.ndarray
            The first range.
        range2 : numpy.ndarray
            The second range.

        Returns
        --------------------
        numpy.ndarray
            The wider range encompassing both inputs.

        Examples
        --------------------
        >>> wider_range = AxesRangeSingleton()._get_wider_range(
        ...     np.array([0, 5]),
        ...     np.array([3, 10])
        ... )
        >>> print(wider_range)
        array([0, 10])
        """
        new_range = np.array([min(range1[0], range2[0]), max(range1[1], range2[1])])
        return new_range

    def get_max_wo_inf(self, array: NDArray[Any]) -> float:
        """
        Returns the maximum value in an array, ignoring infinities.

        Parameters
        --------------------
        array : numpy.ndarray
            The input array.

        Returns
        --------------------
        float
            The maximum value excluding infinities.

        Examples
        --------------------
        >>> max_value = AxesRangeSingleton().get_max_wo_inf(
        ...     np.array([1, 2, np.inf, 3])
        ... )
        >>> print(max_value)
        3.0
        """
        array = np.array(array)
        array = array[array != np.inf]
        return float(np.nanmax(array))

    def get_min_wo_inf(self, array: NDArray[Any]) -> float:
        """
        Returns the minimum value in an array, ignoring negative infinities.

        Parameters
        --------------------
        array : numpy.ndarray
            The input array.

        Returns
        --------------------
        float
            The minimum value excluding negative infinities.

        Examples
        --------------------
        >>> min_value = AxesRangeSingleton().get_min_wo_inf(
        ...     np.array([1, 2, -np.inf, 3])
        ... )
        >>> print(min_value)
        1.0
        """
        array = np.array(array)
        array = array[array != -np.inf]
        return float(np.nanmin(array))

    @classmethod
    def update(cls, func: F) -> F:
        """
        A decorator to update axis ranges based on data and ensure consistency.

        The decorator dynamically adjusts axis ranges by considering the current axis
        data and adding it to the stored ranges.

        Parameters
        --------------------
        func : callable
            The function to wrap.

        Returns
        --------------------
        callable
            The wrapped function.

        Examples
        --------------------
        >>> @AxesRangeSingleton.update
        ... def draw_plot(self, *args, **kwargs):
        ...     pass
        """

        def wrapper(self, *args: Any, **kwargs: Any) -> Any:
            axis_index: int = self.axis_index
            x: NDArray[Any] = self.x
            y: NDArray[Any] = self.y

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


class AxisRangeController:
    """
    A controller for managing the x and y ranges of a specific Matplotlib axis.

    This class provides methods to get and set the x-axis and y-axis ranges for
    a given axis in a Matplotlib figure.

    Parameters
    --------------------
    axis_index : int
        The index of the target axis in the current figure.

    Attributes
    --------------------
    axis_index : int
        The index of the target axis.
    axis : matplotlib.axes.Axes
        The resolved `Axes` object corresponding to the target index.

    Methods
    --------------------
    get_axis_xrange()
        Retrieves the x-axis range of the target axis.
    get_axis_yrange()
        Retrieves the y-axis range of the target axis.
    set_axis_xrange(xrange)
        Sets the x-axis range of the target axis.
    set_axis_yrange(yrange)
        Sets the y-axis range of the target axis.

    Examples
    --------------------
    >>> controller = AxisRangeController(axis_index=0)
    >>> x_range = controller.get_axis_xrange()
    >>> print(x_range)
    array([0.0, 1.0])

    >>> controller.set_axis_xrange(np.array([0.5, 1.5]))
    >>> print(controller.get_axis_xrange())
    array([0.5, 1.5])

    >>> y_range = controller.get_axis_yrange()
    >>> print(y_range)
    array([0.0, 1.0])

    >>> controller.set_axis_yrange(np.array([0.2, 0.8]))
    >>> print(controller.get_axis_yrange())
    array([0.2, 0.8])
    """

    def __init__(self, axis_index: int):
        self.axis_index = axis_index
        self.axis: Axes = AxesResolver(self.axis_index).axis

    def get_axis_xrange(self) -> NDArray[Any]:
        """
        Retrieves the x-axis range of the target axis.

        Returns
        --------------------
        numpy.ndarray
            The x-axis range as a NumPy array.

        Examples
        --------------------
        >>> controller = AxisRangeController(axis_index=0)
        >>> x_range = controller.get_axis_xrange()
        >>> print(x_range)
        array([0.0, 1.0])
        """
        axis_xrange: NDArray[Any] = np.array(self.axis.get_xlim())
        return axis_xrange

    def get_axis_yrange(self) -> NDArray[Any]:
        """
        Retrieves the y-axis range of the target axis.

        Returns
        --------------------
        numpy.ndarray
            The y-axis range as a NumPy array.

        Examples
        --------------------
        >>> controller = AxisRangeController(axis_index=0)
        >>> y_range = controller.get_axis_yrange()
        >>> print(y_range)
        array([0.0, 1.0])
        """
        axis_yrange: NDArray[Any] = np.array(self.axis.get_ylim())
        return axis_yrange

    def set_axis_xrange(self, xrange: NDArray[Any]) -> None:
        """
        Sets the x-axis range of the target axis.

        Parameters
        --------------------
        xrange : numpy.ndarray
            The new x-axis range as a NumPy array.

        Examples
        --------------------
        >>> controller = AxisRangeController(axis_index=0)
        >>> controller.set_axis_xrange(np.array([0.5, 1.5]))
        >>> print(controller.get_axis_xrange())
        array([0.5, 1.5])
        """
        xrange_tuple = tuple(xrange)
        self.axis.set_xlim(xrange_tuple)

    def set_axis_yrange(self, yrange: NDArray[Any]) -> None:
        """
        Sets the y-axis range of the target axis.

        Parameters
        --------------------
        yrange : numpy.ndarray
            The new y-axis range as a NumPy array.

        Examples
        --------------------
        >>> controller = AxisRangeController(axis_index=0)
        >>> controller.set_axis_yrange(np.array([0.2, 0.8]))
        >>> print(controller.get_axis_yrange())
        array([0.2, 0.8])
        """
        yrange_tuple = tuple(yrange)
        self.axis.set_ylim(yrange_tuple)


class AxisRangeManager:
    """
    A manager for handling axis range-related operations in Matplotlib.

    This class provides functionality to determine whether a given axis is initialized
    or has any existing plots (lines) drawn on it.

    Parameters
    --------------------
    axis_index : int
        The index of the target axis in the current figure.

    Attributes
    --------------------
    axis_index : int
        The index of the target axis.
    axis : matplotlib.axes.Axes
        The resolved `Axes` object corresponding to the target index.

    Methods
    --------------------
    is_init_axis()
        Checks whether the target axis is initialized (has no plots).

    Examples
    --------------------
    >>> manager = AxisRangeManager(axis_index=0)
    >>> is_initialized = manager.is_init_axis()
    >>> print(is_initialized)
    True  # No lines plotted yet

    >>> plt.plot([1, 2, 3], [4, 5, 6])
    >>> is_initialized = manager.is_init_axis()
    >>> print(is_initialized)
    False  # A line plot exists on the axis
    """

    def __init__(self, axis_index: int):
        self.axis_index = axis_index

        self.axis: Axes = AxesResolver(self.axis_index).axis

    def is_init_axis(self) -> bool:
        """
        Checks whether the target axis is initialized (has no plots).

        This method determines if the axis has no lines plotted, indicating that it is in
        its initial state.

        Returns
        --------------------
        bool
            `True` if the axis has no plots (lines), `False` otherwise.

        Examples
        --------------------
        >>> manager = AxisRangeManager(axis_index=0)
        >>> is_initialized = manager.is_init_axis()
        >>> print(is_initialized)
        True  # No lines plotted yet

        >>> plt.plot([1, 2, 3], [4, 5, 6])
        >>> is_initialized = manager.is_init_axis()
        >>> print(is_initialized)
        False  # A line plot exists on the axis
        """
        num_lines = len(self.axis.lines)

        if num_lines:
            return False
        else:
            return True


class AxisRangeHandler:
    """
    Handles the computation and updating of axis ranges for a specific Matplotlib axis.

    This class calculates new axis ranges by considering existing ranges and new data,
    ensuring that the axis ranges encompass all relevant data. It also determines whether
    an axis is in its initial state or has been previously modified.

    Parameters
    --------------------
    axis_index : int
        The index of the target axis in the current figure.
    xdata : numpy.ndarray
        The x-axis data to consider for range calculation.
    ydata : numpy.ndarray
        The y-axis data to consider for range calculation.

    Attributes
    --------------------
    axis_index : int
        The index of the target axis.
    xdata : numpy.ndarray
        The x-axis data to consider for range calculation.
    ydata : numpy.ndarray
        The y-axis data to consider for range calculation.
    axis : matplotlib.axes.Axes
        The resolved `Axes` object corresponding to the target index.
    _is_init_axis : bool
        Indicates whether the axis is in its initial state (no plots or data).

    Methods
    --------------------
    get_new_axis_range()
        Calculates the new axis range, combining existing ranges and new data ranges.

    Examples
    --------------------
    >>> xdata = np.array([0, 1, 2, 3])
    >>> ydata = np.array([4, 5, 6, 7])
    >>> handler = AxisRangeHandler(axis_index=0, xdata=xdata, ydata=ydata)
    >>> new_xrange, new_yrange = handler.get_new_axis_range()
    >>> print(new_xrange)
    array([0, 3])
    >>> print(new_yrange)
    array([4, 7])
    """

    def __init__(self, axis_index: int, xdata: NDArray[Any], ydata: NDArray[Any]):
        self.axis_index = axis_index
        self.xdata = xdata
        self.ydata = ydata

        self.axis: Axes = AxesResolver(self.axis_index).axis

        self._is_init_axis: bool = AxisRangeManager(self.axis_index).is_init_axis()

    def _get_axis_range(
        self,
    ) -> tuple[NDArray | None, NDArray | None] | None:
        """
        Retrieves the current axis ranges (x and y) if the axis is not in its initial state.

        Returns
        --------------------
        tuple of (numpy.ndarray or None, numpy.ndarray or None)
            The x-axis and y-axis ranges. Returns `(None, None)` if the axis is in its initial state.

        Examples
        --------------------
        >>> handler = AxisRangeHandler(axis_index=0, xdata=np.array([]), ydata=np.array([]))
        >>> axis_range = handler._get_axis_range()
        >>> print(axis_range)
        (array([0.0, 1.0]), array([0.0, 1.0]))
        """
        if self._is_init_axis:
            return None, None
        else:
            axis_xrange = AxisRangeController(self.axis_index).get_axis_xrange()
            axis_yrange = AxisRangeController(self.axis_index).get_axis_yrange()
            return axis_xrange, axis_yrange

    def _calculate_data_range(self, data: NDArray[Any]) -> NDArray[Any]:
        """
        Calculates the minimum and maximum range for the given data.

        Parameters
        --------------------
        data : numpy.ndarray
            The data for which to calculate the range.

        Returns
        --------------------
        numpy.ndarray
            The range of the data as a NumPy array `[min, max]`.

        Examples
        --------------------
        >>> handler = AxisRangeHandler(axis_index=0, xdata=np.array([0, 1, 2]), ydata=np.array([]))
        >>> data_range = handler._calculate_data_range(np.array([1, 2, 3]))
        >>> print(data_range)
        array([1, 3])
        """
        min_data = np.min(data)
        max_data = np.max(data)
        return np.array([min_data, max_data])

    def get_new_axis_range(
        self,
    ) -> tuple[NDArray | None, NDArray | None]:
        """
        Calculates the new axis ranges based on existing ranges and new data.

        If the axis is in its initial state, it returns the range of the new data.
        Otherwise, it computes the wider range encompassing both the existing range
        and the new data range.

        Returns
        --------------------
        tuple of (numpy.ndarray or None, numpy.ndarray or None)
            The new x-axis and y-axis ranges.

        Examples
        --------------------
        >>> xdata = np.array([0, 1, 2, 3])
        >>> ydata = np.array([4, 5, 6, 7])
        >>> handler = AxisRangeHandler(axis_index=0, xdata=xdata, ydata=ydata)
        >>> new_xrange, new_yrange = handler.get_new_axis_range()
        >>> print(new_xrange)
        array([0, 3])
        >>> print(new_yrange)
        array([4, 7])
        """
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
