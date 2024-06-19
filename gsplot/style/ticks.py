from ..plts.axes import AxesSingleton

import matplotlib.pyplot as plt
import matplotlib.ticker as plticker


class MinorTicks:
    """
    A class used to manage the minor ticks on a plot's axes.

    ...

    Attributes
    ----------
    __axes : list
        a list of axes

    Methods
    -------
    minor_ticks_off(axis):
        Turns off minor ticks on the given axis.
    minor_ticks_on(axis):
        Turns on minor ticks on the given axis.
    minor_ticks_all():
        Turns on minor ticks on all axes.
    """

    def __init__(self):
        """
        Constructs all the necessary attributes for the MinorTicks object.

        Parameters
        ----------
            None
        """

        self.__axes = AxesSingleton()
        self._axes = self.__axes.axes

    def minor_ticks_off(
        self,
        axis_index: int,
    ):
        """
        Turns off minor ticks on the given axis.

        Parameters
        ----------
        axis_index : int
            The axis_index on which to turn off minor ticks.
        """

        axis = self._axes[axis_index]
        axis.xaxis.set_minor_locator(plt.NullLocator())
        axis.yaxis.set_minor_locator(plt.NullLocator())

    def minor_ticks_on(self, axis_index: int):
        """
        Turns on minor ticks on the given axis.

        Parameters
        ----------
        axis_index : int
            The axis_index on which to turn on minor ticks.
        """

        axis = self._axes[axis_index]
        axis.xaxis.set_minor_locator(plticker.AutoMinorLocator())
        axis.yaxis.set_minor_locator(plticker.AutoMinorLocator())

    def minor_ticks_on_by_axis(self, axis):
        """
        Turns on minor ticks on the given axis.

        Parameters
        ----------
        axis : Axes
            The axis on which to turn on minor ticks.
        """

        axis.xaxis.set_minor_locator(plticker.AutoMinorLocator())
        axis.yaxis.set_minor_locator(plticker.AutoMinorLocator())

    def minor_ticks_x(self, axis_index: int):
        """
        Turns on minor ticks on the x-axis of the given axis.

        Parameters
        ----------
        axis_index : int
            The axis_index on which to turn on minor ticks.
        """

        axis = self._axes[axis_index]
        axis.xaxis.set_minor_locator(plticker.AutoMinorLocator())

    def minor_ticks_y(self, axis_index: int):
        """
        Turns on minor ticks on the y-axis of the given axis.

        Parameters
        ----------
        axis_index : int
            The axis_index on which to turn on minor ticks.
        """

        axis = self._axes[axis_index]
        axis.yaxis.set_minor_locator(plticker.AutoMinorLocator())

    def minor_ticks_all(self):
        """
        Turns on minor ticks on all axes.

        Parameters
        ----------
            None
        """

        for axis in self._axes:
            self.minor_ticks_on_by_axis(axis)
