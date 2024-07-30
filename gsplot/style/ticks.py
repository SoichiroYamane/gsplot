from ..figure.axes import AxesSingleton

from matplotlib.axes import Axes

import matplotlib.ticker as plticker
from matplotlib.ticker import NullLocator

from typing import List


class MinorTicks:
    def __init__(self) -> None:
        self.__axes: AxesSingleton = AxesSingleton()
        self._axes: List[Axes] = self.__axes.axes

    def minor_ticks_off(
        self,
        axis_index: int,
    ) -> None:

        axis: Axes = self._axes[axis_index]
        axis.xaxis.set_minor_locator(NullLocator())
        axis.yaxis.set_minor_locator(NullLocator())

    def minor_ticks_on(self, axis_index: int) -> None:
        axis: Axes = self._axes[axis_index]
        axis.xaxis.set_minor_locator(plticker.AutoMinorLocator())
        axis.yaxis.set_minor_locator(plticker.AutoMinorLocator())

    def minor_ticks_on_by_axis(self, axis: Axes) -> None:
        axis.xaxis.set_minor_locator(plticker.AutoMinorLocator())
        axis.yaxis.set_minor_locator(plticker.AutoMinorLocator())

    def minor_ticks_x(self, axis_index: int) -> None:
        axis: Axes = self._axes[axis_index]
        axis.xaxis.set_minor_locator(plticker.AutoMinorLocator())

    def minor_ticks_y(self, axis_index: int) -> None:
        axis: Axes = self._axes[axis_index]
        axis.yaxis.set_minor_locator(plticker.AutoMinorLocator())

    def minor_ticks_all(self) -> None:
        for axis in self._axes:
            self.minor_ticks_on_by_axis(axis)


def ticks_off(axis_index: int) -> None:
    MinorTicks().minor_ticks_off(axis_index)


def ticks_on(axis_index: int) -> None:
    MinorTicks().minor_ticks_on(axis_index)


def ticks_on_by_axis(axis: Axes) -> None:
    MinorTicks().minor_ticks_on_by_axis(axis)


def ticks_x(axis_index: int) -> None:
    MinorTicks().minor_ticks_x(axis_index)


def ticks_y(axis_index: int) -> None:
    MinorTicks().minor_ticks_y(axis_index)


def ticks_all() -> None:
    MinorTicks().minor_ticks_all()
