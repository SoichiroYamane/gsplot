from typing import List, Any, Optional, Union, Tuple

import numpy as np
from matplotlib.transforms import Bbox
from matplotlib.axes import Axes

from .figure_tool import FigureLayout


class AxesSingleton:
    """
    Singleton class to manage a shared list of matplotlib Axes objects.

    Attributes
    ----------
    _instance : Optional[AxesSingleton]
        Singleton instance of the AxesSingleton class.
    _axes : List[Axes]
        List of matplotlib Axes objects managed by the singleton.

    Methods
    -------
    axes() -> List[Axes]
        Getter for the list of Axes.
    axes(axes: List[Axes]) -> None
        Setter for the list of Axes.
    get_axis(axis_index: int) -> Axes
        Retrieves a specific Axes object by its index.
    """

    _instance: Optional["AxesSingleton"] = None

    def __new__(cls) -> "AxesSingleton":
        if cls._instance is None:
            cls._instance = super(AxesSingleton, cls).__new__(cls)
            cls._instance._initialize_axes()
        return cls._instance

    def _initialize_axes(self) -> None:
        """
        Initializes the list of Axes.
        """

        # Explicitly initialize the instance variable with a type hint
        self._axes: List[Axes] = []

    @property
    def axes(self) -> List[Axes]:
        """
        Returns the list of Axes objects.

        Returns
        -------
        List[Axes]
            The list of matplotlib Axes objects managed by the singleton.
        """

        return self._axes

    @axes.setter
    def axes(self, axes: List[Axes]) -> None:
        """
        Sets the list of Axes objects.

        Parameters
        ----------
        axes : List[Axes]
            A list of matplotlib Axes objects to be managed by the singleton.

        Raises
        ------
        TypeError
            If the provided axes is not iterable.
        """

        try:
            iter(axes)
        except TypeError:
            raise TypeError(f"Expected an iterable, got {type(axes).__name__}")
        self._axes = axes

    def get_axis(self, axis_index: int) -> Axes:
        """
        Retrieves a specific Axes object by its index.

        Parameters
        ----------
        axis_index : int
            The index of the Axes object to retrieve.

        Returns
        -------
        Axes
            The matplotlib Axes object at the specified index.

        Raises
        ------
        IndexError
            If the axis_index is out of range.
        """

        def ordinal_suffix(n: int) -> str:
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
    """
    Singleton class to manage a shared list of axis ranges (x and y ranges) for matplotlib Axes.

    Attributes
    ----------
    _instance : Optional[AxesRangeSingleton]
        Singleton instance of the AxesRangeSingleton class.
    _axes_ranges : List[List[Any]]
        List of x and y ranges for each Axes object managed by the singleton.

    Methods
    -------
    axes_ranges() -> List[List[Any]]
        Getter for the list of axes ranges.
    axes_ranges(axes_ranges: List[List[Any]]) -> None
        Setter for the list of axes ranges.
    add_range(axis_index: int, xrange: np.ndarray, yrange: np.ndarray) -> None
        Adds or updates the range for a specific axis.
    _get_wider_range(range1: np.ndarray, range2: np.ndarray) -> np.ndarray
        Combines two ranges into a wider range.
    get_max_wo_inf(array: np.ndarray) -> float
        Gets the maximum value from an array, excluding infinity.
    get_min_wo_inf(array: np.ndarray) -> float
        Gets the minimum value from an array, excluding negative infinity.
    update(func: Any) -> Any
        Decorator to update axis ranges based on data.
    reset(axes: List[Axes]) -> None
        Resets the axis ranges based on the number of axes.
    """

    _instance: Optional["AxesRangeSingleton"] = None

    def __new__(cls) -> "AxesRangeSingleton":
        if cls._instance is None:
            cls._instance = super(AxesRangeSingleton, cls).__new__(cls)
            cls._instance._initialize_axes_ranges()
        return cls._instance

    def _initialize_axes_ranges(self) -> None:
        """
        Initializes the list of axes ranges.
        """

        # Explicitly initialize the instance variable with a type hint
        self._axes_ranges: List[List[Any]] = [[None, None]]

    @property
    def axes_ranges(self) -> List[List[Any]]:
        """
        Returns the list of axes ranges.

        Returns
        -------
        List[List[Any]]
            The list of x and y ranges for each Axes object.
        """

        return self._axes_ranges

    @axes_ranges.setter
    def axes_ranges(
        self,
        axes_ranges: List[List[Any]],
    ) -> None:
        """
        Sets the list of axes ranges.

        Parameters
        ----------
        axes_ranges : List[List[Any]]
            A list of x and y ranges for each Axes object.

        Raises
        ------
        TypeError
            If the provided axes_ranges is not iterable.
        """

        try:
            iter(axes_ranges)
        except TypeError:
            raise TypeError(f"Expected an iterable, got {type(axes_ranges).__name__}")
        self._axes_ranges = axes_ranges

    def add_range(
        self, axis_index: int, xrange: np.ndarray, yrange: np.ndarray
    ) -> None:
        """
        Adds or updates the range for a specific axis.

        Parameters
        ----------
        axis_index : int
            The index of the Axes object to update.
        xrange : np.ndarray
            The x-axis range to set.
        yrange : np.ndarray
            The y-axis range to set.
        """

        while len(self._axes_ranges) <= axis_index:
            self._axes_ranges.append([None, None])
        self._axes_ranges[axis_index] = [xrange, yrange]

    def _get_wider_range(self, range1: np.ndarray, range2: np.ndarray) -> np.ndarray:
        """
        Combines two ranges into a wider range.

        Parameters
        ----------
        range1 : np.ndarray
            The first range.
        range2 : np.ndarray
            The second range.

        Returns
        -------
        np.ndarray
            The combined wider range.
        """

        new_range = np.array([min(range1[0], range2[0]), max(range1[1], range2[1])])
        return new_range

    def get_max_wo_inf(self, array: np.ndarray) -> float:
        """
        Gets the maximum value from an array, excluding infinity.

        Parameters
        ----------
        array : np.ndarray
            The array from which to find the maximum value.

        Returns
        -------
        float
            The maximum value in the array, excluding infinity.
        """

        array = np.array(array)
        array = array[array != np.inf]
        return float(np.nanmax(array))

    def get_min_wo_inf(self, array: np.ndarray) -> float:
        """
        Gets the minimum value from an array, excluding negative infinity.

        Parameters
        ----------
        array : np.ndarray
            The array from which to find the minimum value.

        Returns
        -------
        float
            The minimum value in the array, excluding negative infinity.
        """

        array = np.array(array)
        array = array[array != -np.inf]
        return float(np.nanmin(array))

    @classmethod
    def update(cls, func: Any) -> Any:
        """
        Decorator to update axis ranges based on the provided data.

        This decorator updates the x and y ranges of the axes managed by
        `AxesRangeSingleton` based on the data passed to the decorated function.

        Parameters
        ----------
        func : Any
            The function to be wrapped by the decorator. This function is expected
            to be a method that has `axis_index`, `xdata`, and `ydata` as attributes.

        Returns
        -------
        Any
            The wrapped function. After execution, the axes ranges are updated
            based on the x and y data.

        Example
        -------
        @AxesRangeSingleton.update
        def some_function(self):
            # Function logic that uses self.axis_index, self.xdata, and self.ydata
        """

        def wrapper(self, *args: Any, **kwargs: Any) -> Any:
            axis_index: int = self.axis_index
            xdata: np.ndarray = self.xdata
            ydata: np.ndarray = self.ydata

            num_elements_to_append = max(0, axis_index + 1 - len(cls().axes_ranges))
            cls().axes_ranges.extend([[None, None]] * num_elements_to_append)

            xrange, yrange = AxisRangeHandler(
                axis_index, xdata, ydata
            ).get_new_axis_range()
            xrange = np.array(
                [cls().get_min_wo_inf(xdata), cls().get_max_wo_inf(xdata)]
            )
            yrange = np.array(
                [cls().get_min_wo_inf(ydata), cls().get_max_wo_inf(ydata)]
            )

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
        """
        Resets the axis ranges managed by the singleton to their initial state.

        This method clears the stored axis ranges and sets them to a list of
        `[None, None]` for each axis in the provided list.

        Parameters
        ----------
        axes : List[Axes]
            A list of matplotlib Axes objects. The length of this list determines
            how many axis ranges are reset.

        Example
        -------
        axes = [ax1, ax2, ax3]
        AxesRangeSingleton().reset(axes)
        """
        axes_length = len(axes)
        self._axes_ranges = [[None, None]] * axes_length


class AxisLayout:
    """
    A class for handling the layout and size properties of a specific matplotlib Axes object.

    Parameters
    ----------
    axis_index : int
        The index of the axis in the list of Axes managed by `AxesSingleton`.

    Attributes
    ----------
    axis_index : int
        The index of the axis in the list of Axes.
    __axes : AxesSingleton
        The singleton instance managing all Axes objects.
    _axes : List[Axes]
        The list of Axes objects managed by the singleton.
    axis : Axes
        The specific Axes object corresponding to `axis_index`.
    fig_size : np.ndarray
        The size of the figure containing the axis, in inches.

    Methods
    -------
    get_axis_position() -> Bbox
        Returns the position of the axis as a bounding box (Bbox).
    get_axis_size() -> np.ndarray
        Returns the size of the axis in figure-relative coordinates.
    get_axis_position_inches() -> Bbox
        Returns the position of the axis in inches as a bounding box (Bbox).
    get_axis_size_inches() -> np.ndarray
        Returns the size of the axis in inches.
    """

    def __init__(self, axis_index: int) -> None:
        self.axis_index = axis_index
        self.__axes: AxesSingleton = AxesSingleton()
        self._axes: List[Axes] = self.__axes.axes
        self.axis: Axes = self.__axes.get_axis(self.axis_index)

        self.fig_size: np.ndarray = FigureLayout().get_figure_size()

    def get_axis_position(self) -> Bbox:
        """
        Returns the position of the axis as a bounding box (Bbox).

        Returns
        -------
        Bbox
            The bounding box representing the position of the axis.
        """

        axis_position = self.axis.get_position()
        return axis_position

    def get_axis_size(self) -> np.ndarray:
        """
        Returns the size of the axis in figure-relative coordinates.

        Returns
        -------
        np.ndarray
            An array representing the width and height of the axis in figure-relative coordinates.
        """

        axis_position_size = np.array(self.get_axis_position().size)
        return axis_position_size

    def get_axis_position_inches(self) -> Bbox:
        """
        Returns the position of the axis in inches as a bounding box (Bbox).

        Returns
        -------
        Bbox
            The bounding box representing the position of the axis in inches.
        """

        axis_position = self.get_axis_position()

        axis_position_inches = Bbox.from_bounds(
            axis_position.x0 * self.fig_size[0],
            axis_position.y0 * self.fig_size[1],
            axis_position.width * self.fig_size[0],
            axis_position.height * self.fig_size[1],
        )
        return axis_position_inches

    def get_axis_size_inches(self) -> np.ndarray:
        """
        Returns the size of the axis in inches.

        Returns
        -------
        np.ndarray
            An array representing the width and height of the axis in inches.
        """

        axis_position_size_inches = np.array(self.get_axis_position_inches().size)
        return axis_position_size_inches


class AxisRangeController:
    """
    A class for controlling and setting the x and y ranges of a specific matplotlib Axes object.

    Parameters
    ----------
    axis_index : int
        The index of the axis in the list of Axes managed by `AxesSingleton`.

    Attributes
    ----------
    axis_index : int
        The index of the axis in the list of Axes.
    __axes : AxesSingleton
        The singleton instance managing all Axes objects.
    _axes : List[Axes]
        The list of Axes objects managed by the singleton.
    axis : Axes
        The specific Axes object corresponding to `axis_index`.

    Methods
    -------
    get_axis_xrange() -> np.ndarray
        Returns the x-axis range of the axis.
    get_axis_yrange() -> np.ndarray
        Returns the y-axis range of the axis.
    set_axis_xrange(xrange: np.ndarray) -> None
        Sets the x-axis range of the axis.
    set_axis_yrange(yrange: np.ndarray) -> None
        Sets the y-axis range of the axis.
    """

    def __init__(self, axis_index: int):
        self.axis_index = axis_index
        self.__axes: AxesSingleton = AxesSingleton()
        self._axes: List[Axes] = self.__axes.axes
        self.axis: Axes = self.__axes.get_axis(self.axis_index)

    def get_axis_xrange(self) -> np.ndarray:
        """
        Returns the x-axis range of the axis.

        Returns
        -------
        np.ndarray
            An array representing the minimum and maximum values of the x-axis range.
        """

        axis_xrange: np.ndarray = np.array(self.axis.get_xlim())
        return axis_xrange

    def get_axis_yrange(self) -> np.ndarray:
        """
        Returns the y-axis range of the axis.

        Returns
        -------
        np.ndarray
            An array representing the minimum and maximum values of the y-axis range.
        """

        axis_yrange: np.ndarray = np.array(self.axis.get_ylim())
        return axis_yrange

    def set_axis_xrange(self, xrange: np.ndarray) -> None:
        """
        Sets the x-axis range of the axis.

        Parameters
        ----------
        xrange : np.ndarray
            An array representing the minimum and maximum values to set for the x-axis range.
        """

        xrange_tuple = tuple(xrange)
        self.axis.set_xlim(xrange_tuple)

    def set_axis_yrange(self, yrange: np.ndarray) -> None:
        """
        Sets the y-axis range of the axis.

        Parameters
        ----------
        yrange : np.ndarray
            An array representing the minimum and maximum values to set for the y-axis range.
        """

        yrange_tuple = tuple(yrange)
        self.axis.set_ylim(yrange_tuple)


class AxisRangeManager:
    """
    A class for managing the state of an axis, particularly whether it has been initialized with data.

    Parameters
    ----------
    axis_index : int
        The index of the axis in the list of Axes managed by `AxesSingleton`.

    Attributes
    ----------
    axis_index : int
        The index of the axis in the list of Axes.
    __axes : AxesSingleton
        The singleton instance managing all Axes objects.
    _axes : List[Axes]
        The list of Axes objects managed by the singleton.
    axis : Axes
        The specific Axes object corresponding to `axis_index`.

    Methods
    -------
    is_init_axis() -> bool
        Determines whether the axis has been initialized with data.
    """

    def __init__(self, axis_index: int):
        self.axis_index = axis_index

        self.__axes: AxesSingleton = AxesSingleton()
        self._axes: List[Axes] = self.__axes.axes

        self.axis: Axes = self.__axes.get_axis(self.axis_index)

    def is_init_axis(self) -> bool:
        """
        Determines whether the axis has been initialized with data.

        Returns
        -------
        bool
            True if the axis has not been initialized (i.e., has no lines), False otherwise.
        """
        num_lines = len(self.axis.lines)

        if num_lines:
            return False
        else:
            return True


class AxisRangeHandler:
    """
    A class for handling the calculation and updating of axis ranges based on provided data.

    Parameters
    ----------
    axis_index : int
        The index of the axis in the list of Axes managed by `AxesSingleton`.
    xdata : np.ndarray
        The data to be plotted on the x-axis.
    ydata : np.ndarray
        The data to be plotted on the y-axis.

    Attributes
    ----------
    axis_index : int
        The index of the axis in the list of Axes.
    xdata : np.ndarray
        The data to be plotted on the x-axis.
    ydata : np.ndarray
        The data to be plotted on the y-axis.
    __axes : AxesSingleton
        The singleton instance managing all Axes objects.
    _axes : List[Axes]
        The list of Axes objects managed by the singleton.
    axis : Axes
        The specific Axes object corresponding to `axis_index`.
    _is_init_axis : bool
        A flag indicating whether the axis has been initialized with data.

    Methods
    -------
    _get_axis_range() -> Optional[Tuple[Union[np.ndarray, None], Union[np.ndarray, None]]]
        Retrieves the current x and y ranges of the axis if it is initialized.
    _calculate_data_range(data: np.ndarray) -> np.ndarray
        Calculates the minimum and maximum values of the provided data.
    get_new_axis_range() -> Tuple[Union[np.ndarray, None], Union[np.ndarray, None]]
        Determines the new x and y ranges for the axis based on the existing range and the provided data.
    """

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
        """
        Retrieves the current x and y ranges of the axis if it is initialized.

        Returns
        -------
        Optional[Tuple[Union[np.ndarray, None], Union[np.ndarray, None]]]
            A tuple containing the current x and y ranges, or (None, None) if the axis is not initialized.
        """

        if self._is_init_axis:
            return None, None
        else:
            axis_xrange = AxisRangeController(self.axis_index).get_axis_xrange()
            axis_yrange = AxisRangeController(self.axis_index).get_axis_yrange()
            return axis_xrange, axis_yrange

    def _calculate_data_range(self, data: np.ndarray) -> np.ndarray:
        """
        Calculates the minimum and maximum values of the provided data.

        Parameters
        ----------
        data : np.ndarray
            The data for which to calculate the range.

        Returns
        -------
        np.ndarray
            An array containing the minimum and maximum values of the data.
        """

        min_data = np.min(data)
        max_data = np.max(data)
        return np.array([min_data, max_data])

    def get_new_axis_range(
        self,
    ) -> Tuple[Union[np.ndarray, None], Union[np.ndarray, None]]:
        """
        Determines the new x and y ranges for the axis based on the existing range and the provided data.

        Returns
        -------
        Tuple[Union[np.ndarray, None], Union[np.ndarray, None]]
            A tuple containing the new x and y ranges. If the axis was not initialized,
            the ranges are based solely on the provided data.
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
