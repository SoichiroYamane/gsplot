from typing import Union
from enum import Enum

from .axes_base import AxesSingleton

from ..params.params import Params
from ..params.params import LoadParams
from ..base.base import AttributeSetter
from ..plot.line_base import NumLines

import matplotlib.pyplot as plt
from .store import StoreSingleton

# from .axes_range_singleton import AxesRangeSingleton
from .axes_base import AxesRangeSingleton


class Unit(Enum):
    """
    An enumeration representing different units of measurement.

    ...

    Attributes
    ----------
    MM : str
        Represents millimeters.
    CM : str
        Represents centimeters.
    IN : str
        Represents inches.
    PT : str
        Represents points.
    """

    MM = "mm"
    CM = "cm"
    IN = "in"
    PT = "pt"


class UnitConv:
    """
    A class used to convert between different units of measurement.

    ...

    Attributes
    ----------
    conversion_factors : dict
        A dictionary mapping units of measurement to their conversion factors to inches.

    Methods
    -------
    convert(value: float, unit: Unit):
        Converts a value from the given unit to inches.
    """

    # TODO Calculate the conversion factors from inchecs
    def __init__(self):
        """
        Constructs all the necessary attributes for the UnitConv object.

        Parameters
        ----------
            None
        """

        self.conversion_factors = {
            Unit.MM: 1 / 25.4,
            Unit.CM: 1 / 2.54,
            Unit.IN: 1,
            Unit.PT: 1 / 72,
        }

    def convert(self, value: float, unit: Unit):
        """
        Converts a value from the given unit to inches.

        Parameters
        ----------
            value : float
                The value to convert.
            unit : Unit
                The unit of the value.

        Returns
        -------
            float
                The converted value in inches.

        Raises
        ------
            ValueError
                If the unit is not a valid Unit enum.
        """

        if unit not in self.conversion_factors:
            raise ValueError("Invalid unit")
        return value * self.conversion_factors[unit]


class Axes:
    """
    A class used to create axes of a plot via mosaic.

    ...

    Attributes
    ----------
    _kwargs : dict
        a dictionary of keyword arguments passed to the class
    _store_class : StoreSingleton
        an instance of the StoreSingleton class
    __axes : AxesSingleton
        an instance of the AxesSingleton class
    unit : Unit
        the unit of measurement for the size of the figure
    unit_conv : UnitConv
        an instance of the UnitConv class for converting units
    args : tuple
        a tuple of positional arguments passed to the class

    Methods
    -------
    axes:
        Property that gets the _axes attribute.
    _open_figure(*args, **kwargs):
        Opens a new figure and sets its size and axes.
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """
        Constructs all the necessary attributes for the Axes object.

        Parameters
        ----------
            args : tuple
                a tuple of positional arguments
            kwargs : dict
                a dictionary of keyword arguments
        """

        # Initialize attributes
        self.store = False
        self.size = [300, 300]
        self.unit = "pt"
        self.mosaic = "A"
        self.clear = True
        self.ion = False

        # Define default values
        defaults = {
            "store": self.store,
            "size": self.size,
            "unit": self.unit,
            "mosaic": self.mosaic,
            "clear": self.clear,
            "ion": self.ion,
        }

        # Load the parameters from the configuration file (~/.gsplot.json)
        LoadParams().load_params()
        params = Params().getitem("axes")

        attribute_setter = AttributeSetter(defaults, params, **kwargs)

        self._args = args
        self._kwargs: dict = attribute_setter.set_attributes(self)

        self._store_class = StoreSingleton()
        self._store_class.store = self.store

        self.__axes = AxesSingleton()
        self.unit_enum = Unit[self.unit.upper()]
        self.unit_conv = UnitConv()

        NumLines().reset()

        self._open_figure(*self._args, **self._kwargs)

        AxesRangeSingleton().reset(self.__axes.axes)

    @property
    def get_axes(self):
        """
        Gets the _axes attribute.

        Returns
        -------
        list
            The list of axes.
        """

        return self.__axes.axes

    def _open_figure(self):
        """
        Opens a new figure and sets its size and axes.

        Parameters
        ----------
            args : tuple
                a tuple of positional arguments
            kwargs : dict
                a dictionary of keyword arguments

        Raises
        ------
            ValueError
                If the mosaic attribute is not specified.
        """

        if self.ion:
            plt.ion()

        # # get all axes
        # axes = plt.gcf().get_axes()
        # for ax in axes:
        #     ax.remove()
        # # print(axes)

        if self.clear:
            plt.gcf().clear()

        conv_size = tuple(
            map(lambda size: self.unit_conv.convert(size, self.unit_enum), self.size)
        )
        plt.gcf().set_size_inches(*conv_size, **self._kwargs)

        if self.mosaic != "":
            structures = [
                p[1] for p in (sorted(plt.gcf().subplot_mosaic(self.mosaic).items()))
            ]
            self.__axes.axes = structures

            # To ensure that the axes are tightly packed, otherwise axes sizes will be different after tight_layout is called
            plt.tight_layout()
        else:
            raise ValueError("Mosaic must be specified.")
