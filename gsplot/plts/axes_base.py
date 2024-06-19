from .figure_tool import FigureLayout

from matplotlib import pyplot as plt
from matplotlib.transforms import Bbox
import numpy as np


class AxesSingleton:
    """
    A singleton class used to manage a list of axes.

    ...

    Attributes
    ----------
    _instance : AxesSingleton
        the single instance of the AxesSingleton class
    _axes : list
        a list of axes

    Methods
    -------
    axes:
        Property that gets or sets the _axes attribute.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Creates a new instance of the AxesSingleton class if one does not already exist.
        """

        if cls._instance is None:
            cls._instance = super(AxesSingleton, cls).__new__(cls)
            cls._instance._axes = []
        return cls._instance

    @property
    def axes(self):
        """
        Gets the _axes attribute.

        Returns
        -------
        list
            The list of axes.
        """

        return self._instance._axes

    @axes.setter
    def axes(self, axes: list):
        """
        Sets the _axes attribute.

        Parameters
        ----------
        axes : list
            The new list of axes.

        Raises
        ------
        TypeError
            If axes is not a list.
        """

        if not isinstance(axes, list):
            raise TypeError(f"Expected type list, got {type(axes).__name__}")
        self._instance._axes = axes


class AxesRangeSingleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AxesRangeSingleton, cls).__new__(cls)

            cls._instance._axes_range = [[None, None]]
        return cls._instance

    @property
    def axes_range(self):
        return self._axes_range

    @axes_range.setter
    def axes_range(self, axes_range: list):
        self._axes_range = axes_range

    def add_range(self, axis_index: int, xrange: np.ndarray, yrange: np.ndarray):
        self._axes_range[axis_index] = [xrange, yrange]

    def _get_wider_range(self, range1: np.ndarray, range2: np.ndarray) -> np.ndarray:
        new_range = np.array([min(range1[0], range2[0]), max(range1[1], range2[1])])
        return new_range

    @classmethod
    def update(cls, func):
        def wrapper(self, *args, **kwargs):
            axis_index = self.axis_index
            xdata = self.xdata
            ydata = self.ydata

            if axis_index + 1 >= len(cls().axes_range):
                for i in range(axis_index - len(cls().axes_range) + 1):
                    cls().axes_range.append([None, None])

            xrange, yrange = AxisRangeHandler(
                axis_index, xdata, ydata
            ).get_new_axis_range()
            xrange = np.array([xdata.min(), xdata.max()])
            yrange = np.array([ydata.min(), ydata.max()])

            xrange_singleton = cls().axes_range[axis_index][0]
            yrange_singleton = cls().axes_range[axis_index][1]

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

    def reset(self):
        self._axes_range = [[None, None]]


class AxisLayout:
    def __init__(self, axis_index):
        self.axis_index = axis_index
        self.__axes = AxesSingleton()
        self._axes = self.__axes.axes
        self.axis = self._axes[self.axis_index]

        self.fig_size = FigureLayout().get_figure_size()

    def get_axis_position(self) -> Bbox:
        axis_position = self.axis.get_position()
        return axis_position

    def get_axis_size(self) -> np.ndarray:
        axis_position = self.get_axis_position()
        return axis_position.size

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
        axis_position_inches = self.get_axis_position_inches()
        return axis_position_inches.size


class AxisRangeController:
    def __init__(self, axis_index):
        self.axis_index = axis_index
        self.__axes = AxesSingleton()
        self._axes = self.__axes.axes
        self.axis = self._axes[self.axis_index]

    def get_axis_xrange(self) -> np.ndarray:
        axis_xrange = self.axis.get_xlim()
        return axis_xrange

    def get_axis_yrange(self) -> np.ndarray:
        axis_yrange = self.axis.get_ylim()
        return axis_yrange

    def set_axis_xrange(self, xrange: np.ndarray):
        self.axis.set_xlim(xrange)

    def set_axis_yrange(self, yrange: np.ndarray):
        self.axis.set_ylim(yrange)


class AxisRangeManager:
    def __init__(self, axis_index):
        self.axis_index = axis_index

        self.__axes = AxesSingleton()
        self._axes = self.__axes.axes

        self.axis = self._axes[self.axis_index]

    def is_init_axis(self):
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

        self.__axes = AxesSingleton()
        self._axes = self.__axes.axes
        self.axis = self._axes[self.axis_index]

        self._is_init_axis = AxisRangeManager(self.axis_index).is_init_axis()

    def _get_axis_range(self):
        if self._is_init_axis:
            axis_xrange = None
            axis_yrange = None
        else:
            axis_xrange = AxisRangeController(self.axis_index).get_axis_xrange()
            axis_yrange = AxisRangeController(self.axis_index).get_axis_yrange()
        return axis_xrange, axis_yrange

    def _calculate_data_range(self, data) -> np.ndarray:
        min_data = np.min(data)
        max_data = np.max(data)
        return np.array([min_data, max_data])

    def get_new_axis_range(self):
        xrange, yrange = self._get_axis_range()
        xrange_data, yrange_data = (
            self._calculate_data_range(self.xdata),
            self._calculate_data_range(self.ydata),
        )

        if xrange is None or yrange is None:
            new_xrange = xrange_data if xrange is None else xrange
            new_yrange = yrange_data if yrange is None else yrange

        else:
            new_xrange = np.array(
                [min(xrange[0], xrange_data[0]), max(xrange[1], xrange_data[1])]
            )
            new_yrange = np.array(
                [min(yrange[0], yrange_data[0]), max(yrange[1], yrange_data[1])]
            )

        return new_xrange, new_yrange
