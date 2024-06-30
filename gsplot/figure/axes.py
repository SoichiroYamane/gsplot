from enum import Enum
from typing import Dict, List, Tuple, Any, Union

import matplotlib.pyplot as plt

from .axes_base import AxesSingleton, AxesRangeSingleton
from .store import StoreSingleton
from ..base.base import AttributeSetter
from ..params.params import Params, LoadParams
from ..plot.line_base import NumLines


class Unit(Enum):

    MM = "mm"
    CM = "cm"
    IN = "in"
    PT = "pt"
    INVALID = "invalid"


class UnitConv:
    # TODO Calculate the conversion factors from inches
    def __init__(self):
        self.conversion_factors: Dict[Unit, float] = {
            Unit.MM: 1 / 25.4,
            Unit.CM: 1 / 2.54,
            Unit.IN: 1,
            Unit.PT: 1 / 72,
        }

    def convert(self, value: float, unit: Unit) -> float:
        if unit not in self.conversion_factors:
            raise ValueError("Invalid unit")
        return value * self.conversion_factors[unit]


class AxesHandler:
    def __init__(
        self,
        *args: Tuple[Any],
        **kwargs: Dict[str, Any],
    ):
        # Initialize attributes
        self.store: bool = False
        self.size: List[int] = [5, 5]
        self.unit: str = "in"
        self.mosaic: str = "A"
        self.clear: bool = True
        self.ion: bool = False

        # Define default values
        defaults: Dict[str, Union[bool, List[int], str]] = {
            "store": self.store,
            "size": self.size,
            "unit": self.unit,
            "mosaic": self.mosaic,
            "clear": self.clear,
            "ion": self.ion,
        }

        # Load the parameters from the configuration file (~/.gsplot.json)
        LoadParams().load_params()
        params: Dict[str, Any] = Params().getitem("axes")

        attribute_setter = AttributeSetter(defaults, params, **kwargs)

        self._args: Tuple[Any, ...] = args
        self._kwargs: Dict[str, Any] = attribute_setter.set_attributes(self)

        self._store_class = StoreSingleton()
        self._store_class.store = self.store

        self.__axes = AxesSingleton()
        self.unit_enum: Unit = Unit[self.unit.upper()]
        self.unit_conv: UnitConv = UnitConv()

        NumLines().reset()

        self._open_figure(*self._args, **self._kwargs)

        AxesRangeSingleton().reset(self.__axes.axes)

    @property
    def get_axes(self) -> Any:
        return self.__axes.axes

    def _open_figure(self) -> None:
        if self.ion:
            plt.ion()

        if self.clear:
            plt.gcf().clear()

        if len(self.size) != 2:
            raise ValueError("Size must contain exactly two elements.")

        conv_size: Tuple[float, float] = (
            self.unit_conv.convert(self.size[0], self.unit_enum),
            self.unit_conv.convert(self.size[1], self.unit_enum),
        )
        plt.gcf().set_size_inches(*conv_size, **self._kwargs)

        if self.mosaic != "":
            axes: List[Any] = [
                p[1] for p in (sorted(plt.gcf().subplot_mosaic(self.mosaic).items()))
            ]
            self.__axes.axes = axes

            # To ensure that the axes are tightly packed, otherwise axes sizes will be different after tight_layout is called
            plt.tight_layout()
        else:
            raise ValueError("Mosaic must be specified.")
