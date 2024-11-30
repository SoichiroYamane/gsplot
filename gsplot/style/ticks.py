from typing import Literal
from matplotlib.axes import Axes
from matplotlib.ticker import NullLocator
import matplotlib.ticker as plticker
import matplotlib.pyplot as plt

from ..figure.axes_base import AxesResolver


class MinorTicks:

    def __init__(self, axis_target: int | Axes) -> None:
        self.axis_target: int | Axes = axis_target

        _axes_resolver = AxesResolver(axis_target)
        self.axis_index: int = _axes_resolver.axis_index
        self.axis: Axes = _axes_resolver.axis

    def set_minor_ticks_off(self, mode=Literal["x", "y", "xy"]) -> None:

        if mode == "x":
            self.axis.xaxis.set_minor_locator(NullLocator())
        elif mode == "y":
            self.axis.yaxis.set_minor_locator(NullLocator())
        elif mode == "xy":
            self.axis.xaxis.set_minor_locator(NullLocator())
            self.axis.yaxis.set_minor_locator(NullLocator())
        else:
            raise ValueError("Invalid mode. Choose from 'x', 'y', or 'xy'.")

    def set_minor_ticks_on(self, mode=Literal["x", "y", "xy"]) -> None:

        if mode == "x":
            self.axis.xaxis.set_minor_locator(plticker.AutoMinorLocator())
        elif mode == "y":
            self.axis.yaxis.set_minor_locator(plticker.AutoMinorLocator())
        elif mode == "xy":
            self.axis.xaxis.set_minor_locator(plticker.AutoMinorLocator())
            self.axis.yaxis.set_minor_locator(plticker.AutoMinorLocator())
        else:
            raise ValueError("Invalid mode. Choose from 'x', 'y', or 'xy'.")


class MinorTicksAxes:
    def set_minor_ticks_axes(self) -> None:
        for axis in plt.gcf().axes:
            axis.xaxis.set_minor_locator(plticker.AutoMinorLocator())
            axis.yaxis.set_minor_locator(plticker.AutoMinorLocator())


# TODO: add docstrings
def ticks_off(axis_target: int | Axes, mode=Literal["x", "y", "xy"]) -> None:
    MinorTicks(axis_target).set_minor_ticks_off(mode)


def ticks_on(axis_target: int | Axes, mode=Literal["x", "y", "xy"]) -> None:
    MinorTicks(axis_target).set_minor_ticks_on(mode)


def ticks_on_axes() -> None:
    MinorTicksAxes().set_minor_ticks_axes()
