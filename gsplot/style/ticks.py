from ..plts.axes import _Axes

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

        self.__axes = _Axes().axes

    def minor_ticks_off(self, axis):
        """
        Turns off minor ticks on the given axis.

        Parameters
        ----------
        axis : matplotlib.axes.Axes
            The axis on which to turn off minor ticks.
        """

        axis.xaxis.set_minor_locator(plt.NullLocator())
        axis.yaxis.set_minor_locator(plt.NullLocator())

    def minor_ticks_on(self, axis):
        """
        Turns on minor ticks on the given axis.

        Parameters
        ----------
        axis : matplotlib.axes.Axes
            The axis on which to turn on minor ticks.
        """

        axis.xaxis.set_minor_locator(plticker.AutoMinorLocator())
        axis.yaxis.set_minor_locator(plticker.AutoMinorLocator())

    def minor_ticks_all(self):
        """
        Turns on minor ticks on all axes.

        Parameters
        ----------
            None
        """

        for axis in self.__axes:
            self.minor_ticks_on(axis)