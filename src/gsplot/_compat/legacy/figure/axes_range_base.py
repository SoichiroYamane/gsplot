from __future__ import annotations

import threading
from typing import Any, Callable, TypeVar, cast

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from numpy.typing import NDArray

F = TypeVar("F", bound=Callable[..., Any])


class AxesRangeSingleton:
    """
    AxesRangeSingleton
    ==================

    A thread-safe singleton class for managing and storing axis ranges in a plotting context.
    The class provides utility methods for retrieving, updating, and managing axis ranges
    for matplotlib axes, ensuring consistency across multiple threads and functions.

    Key Features
    --------------------
    - Implements a thread-safe singleton pattern.
    - Stores axis ranges (`xrange` and `yrange`) for matplotlib axes.
    - Updates axis ranges dynamically based on new data using decorators.
    - Provides utility functions for handling infinities and calculating wider ranges.

    Usage
    --------------------
    This class is designed to be used as a singleton, meaning only one instance of it
    exists at any time. Use the `AxesRangeSingleton()` constructor to access the instance.

    Examples
    --------------------
    >>> import numpy as np
    >>> import matplotlib.pyplot as plt
    >>> from AxesRangeSingleton import AxesRangeSingleton

    >>> ax = plt.subplot()
    >>> singleton = AxesRangeSingleton()
    >>> singleton.add_range(ax, np.array([0, 5]), np.array([1, 10]))
    >>> print(singleton.get_axes_range(ax))
    [array([0, 5]), array([1, 10])]

    >>> @AxesRangeSingleton.update
    ... def draw_plot():
    ...     pass

    Attributes
    --------------------
    _axes_ranges_dict : dict[matplotlib.axes.Axes, list]
        A dictionary storing the `xrange` and `yrange` for each axis.

    _lock : threading.Lock
        A threading lock to ensure thread safety when accessing the singleton instance.

    Methods
    --------------------
    __new__(cls) -> AxesRangeSingleton
        Ensures only one instance of the singleton is created.

    axes_ranges_dict -> dict[matplotlib.axes.Axes, list]
        Returns the dictionary containing the axis ranges.

    get_axes_range(ax: Axes) -> list
        Retrieves the range for a specific axis. If the axis does not exist, initializes it
        with `[None, None]`.

    add_range(ax: Axes, xrange: NDArray[Any], yrange: NDArray[Any]) -> None
        Adds or updates the range for a specific axis.

    _get_wider_range(range1: NDArray[Any], range2: NDArray[Any]) -> NDArray[Any]
        Computes a wider range that encompasses two given ranges.

    get_max_wo_inf(array: NDArray[Any]) -> float
        Returns the maximum value in an array, ignoring positive infinities.

    get_min_wo_inf(array: NDArray[Any]) -> float
        Returns the minimum value in an array, ignoring negative infinities.

    update(cls, func: F) -> F
        A decorator that updates axis ranges dynamically based on data.

    reset() -> None
        Resets the axes ranges for all

    Notes
    --------------------
    - This class is thread-safe and ensures that modifications to the axis ranges are consistent.
    - Axis ranges are represented as numpy arrays for compatibility with mathematical operations.

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
        self._axes_ranges_dict: dict[Axes, list] = {}

    @property
    def axes_ranges_dict(self) -> dict[Axes, list]:
        """
        Retrieves the dictionary containing the ranges for each axis.

        Returns
        --------------------
        dict[matplotlib.axes.Axes, list]
            The dictionary containing the ranges for each axis.
        """

        return self._axes_ranges_dict

    def get_axes_range(self, ax: Axes) -> list:
        """
        Retrieves the range for a specific axis.

        Parameters
        --------------------
        ax: matplotlib.axes.Axes
            The axis for which to retrieve the range.

        Returns
        --------------------
        list
            The range for the specified axis.

        Examples
        --------------------
        >>> axes_ranges = AxesRangeSingleton()
        >>> axes_ranges.get_axes_range(axs[0])
        """
        if ax not in self._axes_ranges_dict:
            self._axes_ranges_dict[ax] = [None, None]
            return [None, None]
        return self._axes_ranges_dict[ax]

    def add_range(self, ax: Axes, xrange: NDArray[Any], yrange: NDArray[Any]) -> None:
        """
        Adds or updates the range for a specific axis.

        Parameters
        --------------------
        ax: matplotlib.axes.Axes
            Axes object for which to add or update the range.
        xrange : numpy.ndarray
            The range for the x-axis.
        yrange : numpy.ndarray
            The range for the y-axis.

        Examples
        --------------------
        """
        if ax not in self._axes_ranges_dict:
            self._axes_ranges_dict[ax] = [None, None]

        self._axes_ranges_dict[ax] = [xrange, yrange]

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
            ax = self.ax
            x: NDArray[Any] = self.x
            y: NDArray[Any] = self.y

            xrange, yrange = AxisRangeHandler(ax, x, y).get_new_axis_range()
            xrange = np.array([cls().get_min_wo_inf(x), cls().get_max_wo_inf(x)])
            yrange = np.array([cls().get_min_wo_inf(y), cls().get_max_wo_inf(y)])

            xrange_singleton, yrange_singleton = cls().get_axes_range(ax)

            if xrange_singleton is not None:
                new_xrange = cls()._get_wider_range(xrange, xrange_singleton)
            else:
                new_xrange = xrange

            if yrange_singleton is not None:
                new_yrange = cls()._get_wider_range(yrange, yrange_singleton)
            else:
                new_yrange = yrange

            cls().add_range(ax, new_xrange, new_yrange)

            result = func(self, *args, **kwargs)
            return result

        return cast(F, wrapper)

    def reset(self):
        """
        Resets the axes ranges for all axes.
        """
        self._axes_ranges_dict = {}


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

    def __init__(self, ax: Axes):
        self.ax: Axes = ax

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
        ax_xrange: NDArray[Any] = np.array(self.ax.get_xlim())
        return ax_xrange

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
        ax_yrange: NDArray[Any] = np.array(self.ax.get_ylim())
        return ax_yrange

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
        self.ax.set_xlim(xrange_tuple)

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
        self.ax.set_ylim(yrange_tuple)


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

    def __init__(self, ax: Axes):
        self.ax: Axes = ax

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
        num_lines = len(self.ax.lines)

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

    def __init__(self, ax: Axes, xdata: NDArray[Any], ydata: NDArray[Any]):
        self.ax: Axes = ax
        self.xdata: NDArray[Any] = xdata
        self.ydata: NDArray[Any] = ydata

        self._is_init_axis: bool = AxisRangeManager(self.ax).is_init_axis()

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
            axis_xrange = AxisRangeController(self.ax).get_axis_xrange()
            axis_yrange = AxisRangeController(self.ax).get_axis_yrange()
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
