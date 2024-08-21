from typing import List
from matplotlib.axes import Axes
from matplotlib.ticker import NullLocator
import matplotlib.ticker as plticker

from ..figure.axes import AxesSingleton


class MinorTicks:
    """
    A utility class for managing minor ticks on matplotlib Axes.

    This class provides methods to enable or disable minor ticks on specific axes
    within a matplotlib figure. It supports enabling or disabling minor ticks
    for both the x and y axes individually or collectively.

    Methods
    -------
    minor_ticks_off(axis_index: int) -> None
        Disables minor ticks on both x and y axes for the specified axis.
    minor_ticks_on(axis_index: int) -> None
        Enables minor ticks on both x and y axes for the specified axis.
    minor_ticks_on_by_axis(axis: Axes) -> None
        Enables minor ticks on both x and y axes for the provided Axes object.
    minor_ticks_x(axis_index: int) -> None
        Enables minor ticks on the x-axis for the specified axis.
    minor_ticks_y(axis_index: int) -> None
        Enables minor ticks on the y-axis for the specified axis.
    minor_ticks_all() -> None
        Enables minor ticks on all axes within the figure.
    """

    def __init__(self) -> None:
        self.__axes: AxesSingleton = AxesSingleton()
        self._axes: List[Axes] = self.__axes.axes

    def minor_ticks_off(
        self,
        axis_index: int,
    ) -> None:
        """
        Disables minor ticks on both x and y axes for the specified axis.

        Parameters
        ----------
        axis_index : int
            The index of the axis on which to disable minor ticks.
        """

        axis: Axes = self._axes[axis_index]
        axis.xaxis.set_minor_locator(NullLocator())
        axis.yaxis.set_minor_locator(NullLocator())

    def minor_ticks_on(self, axis_index: int) -> None:
        """
        Enables minor ticks on both x and y axes for the specified axis.

        Parameters
        ----------
        axis_index : int
            The index of the axis on which to enable minor ticks.
        """

        axis: Axes = self._axes[axis_index]
        axis.xaxis.set_minor_locator(plticker.AutoMinorLocator())
        axis.yaxis.set_minor_locator(plticker.AutoMinorLocator())

    def minor_ticks_on_by_axis(self, axis: Axes) -> None:
        """
        Enables minor ticks on both x and y axes for the provided Axes object.

        Parameters
        ----------
        axis : Axes
            The Axes object on which to enable minor ticks.
        """

        axis.xaxis.set_minor_locator(plticker.AutoMinorLocator())
        axis.yaxis.set_minor_locator(plticker.AutoMinorLocator())

    def minor_ticks_x(self, axis_index: int) -> None:
        """
        Enables minor ticks on the x-axis for the specified axis.

        Parameters
        ----------
        axis_index : int
            The index of the axis on which to enable minor ticks for the x-axis.
        """

        axis: Axes = self._axes[axis_index]
        axis.xaxis.set_minor_locator(plticker.AutoMinorLocator())

    def minor_ticks_y(self, axis_index: int) -> None:
        """
        Enables minor ticks on the y-axis for the specified axis.

        Parameters
        ----------
        axis_index : int
            The index of the axis on which to enable minor ticks for the y-axis.
        """

        axis: Axes = self._axes[axis_index]
        axis.yaxis.set_minor_locator(plticker.AutoMinorLocator())

    def minor_ticks_all(self) -> None:
        """
        Enables minor ticks on all axes within the figure.

        This method applies minor ticks to both x and y axes for every axis in the figure.
        """

        for axis in self._axes:
            self.minor_ticks_on_by_axis(axis)


def ticks_off(axis_index: int) -> None:
    """
    Disables minor ticks on both x and y axes for the specified axis.

    Parameters
    ----------
    axis_index : int
        The index of the axis on which to disable minor ticks.
    """

    MinorTicks().minor_ticks_off(axis_index)


def ticks_on(axis_index: int) -> None:
    """
    Enables minor ticks on both x and y axes for the specified axis.

    Parameters
    ----------
    axis_index : int
        The index of the axis on which to enable minor ticks.
    """

    MinorTicks().minor_ticks_on(axis_index)


def ticks_on_by_axis(axis: Axes) -> None:
    """
    Enables minor ticks on both x and y axes for the provided Axes object.

    Parameters
    ----------
    axis : Axes
        The Axes object on which to enable minor ticks.
    """

    MinorTicks().minor_ticks_on_by_axis(axis)


def ticks_x(axis_index: int) -> None:
    """
    Enables minor ticks on the x-axis for the specified axis.

    Parameters
    ----------
    axis_index : int
        The index of the axis on which to enable minor ticks for the x-axis.
    """

    MinorTicks().minor_ticks_x(axis_index)


def ticks_y(axis_index: int) -> None:
    """
    Enables minor ticks on the y-axis for the specified axis.

    Parameters
    ----------
    axis_index : int
        The index of the axis on which to enable minor ticks for the y-axis.
    """

    MinorTicks().minor_ticks_y(axis_index)


def ticks_all() -> None:
    """
    Enables minor ticks on all axes within the figure.

    This function applies minor ticks to both x and y axes for every axis in the figure.
    """

    MinorTicks().minor_ticks_all()
