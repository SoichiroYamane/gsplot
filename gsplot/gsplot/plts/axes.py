from typing import Union
from enum import Enum

import matplotlib.pyplot as plt
import numpy as np
from .store import Store


class _Axes:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(_Axes, cls).__new__(cls)
            cls._instance._axes = []
        return cls._instance

    @property
    def axes(self):
        return self._instance._axes

    @axes.setter
    def axes(self, axes: list):
        if not isinstance(axes, list):
            raise TypeError(f"Expected type list, got {type(axes).__name__}")
        self._instance._axes = axes


class Unit(Enum):
    MM = "mm"
    CM = "cm"
    IN = "in"
    PT = "pt"


class UnitConv:
    def __init__(self):
        self.conversion_factors = {
            Unit.MM: 1 / 25.4,
            Unit.CM: 1 / 2.54,
            Unit.IN: 1,
            Unit.PT: 1 / 72,
        }

    def convert(self, value: float, unit: Unit):
        if unit not in self.conversion_factors:
            raise ValueError("Invalid unit")
        return value * self.conversion_factors[unit]


class Axes(_Axes):
    def __init__(
        self,
        store: Union[bool, int] = False,
        size: tuple = (300, 300),
        unit: Unit = Unit.PT,
        mosaic: str = "",
        clear: bool = True,
        *args,
        **kwargs,
    ):
        """
        Figure class to manage the saving of plots and additional functionality.

        Parameters
        ----------
        store : bool or int (0 or 1)
            If True or 1, save the plot to a file. If False or 0, do not save the plot. Default is False.
        """
        self.store = Store(store)

        self.size = size
        self.unit = Unit[unit.upper()]
        self.mosaic = mosaic
        self.clear = clear

        self._axes = _Axes()
        self.unit_conv = UnitConv()

        self._open_figure(*args, **kwargs)

    def modify_axes(self, _axes: _Axes):
        """
        Modify the axes of the plot.

        Parameters
        ----------
        axes : Axes
            The axes to modify.
        """
        self._axes.axes = _axes

    def _open_figure(self, *args, **kwargs):
        """
        Create axes for the plot.
        """
        if self.clear:
            plt.clf()

        # Set the size of the figure in the unit
        conv_size = tuple(
            map(lambda size: self.unit_conv.convert(size, self.unit), self.size)
        )
        plt.gcf().set_size_inches(*conv_size)

        if self.mosaic != "":
            structures = [
                p[1]
                for p in (
                    sorted(plt.gcf().subplot_mosaic(self.mosaic, **kwargs).items())
                )
            ]
            self._axes._axes = structures
            print("Structures", structures)
        else:
            raise ValueError("Mosaic must be specified.")
