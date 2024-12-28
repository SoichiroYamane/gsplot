from typing import Literal

import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
from matplotlib.axes import Axes
from matplotlib.ticker import NullLocator

__all__: list[str] = ["ticks_off", "ticks_on", "ticks_on_axes"]


class MinorTicks:
    """
    A class for managing minor ticks on a specific axis.

    Parameters
    --------------------
    ax : Axes
        The target axis for minor tick configuration.

    Methods
    --------------------
    set_minor_ticks_off(mode)
        Turns off minor ticks on the specified axis.
    set_minor_ticks_on(mode)
        Turns on minor ticks on the specified axis.

    Examples
    --------------------
    >>> import matplotlib.pyplot as plt
    >>> fig, ax = plt.subplots()
    >>> x = [0, 1, 2, 3, 4]
    >>> y = [0, 1, 4, 9, 16]
    >>> ax.plot(x, y)
    >>> # Turn off minor ticks on the x-axis
    >>> ticks_off(ax=ax, mode="x")
    >>> # Turn on minor ticks on the y-axis
    >>> ticks_on(ax=ax, mode="y")
    >>> plt.show()
    """

    def __init__(self, ax: Axes) -> None:
        self.ax: Axes = ax

    def set_minor_ticks_off(self, mode: Literal["x", "y", "xy"] = "xy") -> None:
        """
        Turn off minor ticks for the specified axis.

        Parameters
        --------------------
        mode : {"x", "y", "xy"}, optional
            Specifies the axis to configure. 'x' for x-axis, 'y' for y-axis,
            and 'xy' for both axes. Default is 'xy'.
        """
        if mode == "x":
            self.ax.xaxis.set_minor_locator(NullLocator())
        elif mode == "y":
            self.ax.yaxis.set_minor_locator(NullLocator())
        elif mode == "xy":
            self.ax.xaxis.set_minor_locator(NullLocator())
            self.ax.yaxis.set_minor_locator(NullLocator())
        else:
            raise ValueError("Invalid mode. Choose from 'x', 'y', or 'xy'.")

    def set_minor_ticks_on(self, mode: Literal["x", "y", "xy"] = "xy") -> None:
        """
        Turn on minor ticks for the specified axis.

        Parameters
        --------------------
        mode : {"x", "y", "xy"}, optional
            Specifies the axis to configure. 'x' for x-axis, 'y' for y-axis,
            and 'xy' for both axes. Default is 'xy'.
        """
        if mode == "x":
            self.ax.xaxis.set_minor_locator(plticker.AutoMinorLocator())
        elif mode == "y":
            self.ax.yaxis.set_minor_locator(plticker.AutoMinorLocator())
        elif mode == "xy":
            self.ax.xaxis.set_minor_locator(plticker.AutoMinorLocator())
            self.ax.yaxis.set_minor_locator(plticker.AutoMinorLocator())
        else:
            raise ValueError("Invalid mode. Choose from 'x', 'y', or 'xy'.")


class MinorTicksAxes:
    """
    A class for managing minor ticks across all axes in the current figure.

    Methods
    --------------------
    set_minor_ticks_axes()
        Turn on minor ticks for all axes in the current figure.

    Examples
    --------------------
    >>> # Turn on minor ticks for all axes
    >>> ticks_on_axes()
    """

    def set_minor_ticks_axes(self) -> None:
        """
        Turn on minor ticks for all axes in the current figure.
        """
        for axis in plt.gcf().axes:
            axis.xaxis.set_minor_locator(plticker.AutoMinorLocator())
            axis.yaxis.set_minor_locator(plticker.AutoMinorLocator())


def ticks_off(ax: Axes, mode: Literal["x", "y", "xy"] = "xy") -> None:
    """
    Turn off minor ticks for the specified axis.

    Parameters
    --------------------
    ax : Axes
        The target axis for minor tick configuration.
    mode : {"x", "y", "xy"}, optional
        Specifies the axis to configure. 'x' for x-axis, 'y' for y-axis,
        and 'xy' for both axes. Default is 'xy'.

    Examples
    --------------------
    >>> import gsplot as gs
    >>> # Turn off minor ticks on the x-axis
    >>> gs.ticks_off(ax=ax, mode="x")
    """
    MinorTicks(ax).set_minor_ticks_off(mode)


def ticks_on(ax: Axes, mode: Literal["x", "y", "xy"] = "xy") -> None:
    """
    Turn on minor ticks for the specified axis.

    Parameters
    --------------------
    ax : Axes
        The target axis for minor tick configuration.
    mode : {"x", "y", "xy"}, optional
        Specifies the axis to configure. 'x' for x-axis, 'y' for y-axis,
        and 'xy' for both axes. Default is 'xy'.

    Examples
    --------------------
    >>> import gsplot as gs
    >>> # Turn on minor ticks on the x-axis
    >>> gs.ticks_on(ax=ax, mode="x")
    """
    MinorTicks(ax).set_minor_ticks_on(mode)


def ticks_on_axes() -> None:
    """
    Turn on minor ticks for all axes in the current figure.

    Examples
    --------------------
    >>> import gsplot as gs
    >>> # Turn on minor ticks for all axes
    >>> gs.ticks_on_axes()
    """
    MinorTicksAxes().set_minor_ticks_axes()
