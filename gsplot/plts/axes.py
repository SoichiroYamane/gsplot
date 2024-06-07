from typing import Union
from enum import Enum

from ..params.params import Params
from ..base.base import AttributeSetter

import matplotlib.pyplot as plt
from .store import Store


class _Axes:
    """
    A singleton class used to manage a list of axes.

    ...

    Attributes
    ----------
    _instance : _Axes
        the single instance of the _Axes class
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
        Creates a new instance of the _Axes class if one does not already exist.
        """

        if cls._instance is None:
            cls._instance = super(_Axes, cls).__new__(cls)
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


class Axes(_Axes):
    """
    A class used to create axes of a plot via mosaic.

    ...

    Attributes
    ----------
    _kwargs : dict
        a dictionary of keyword arguments passed to the class
    _store_class : Store
        an instance of the Store class
    __axes : _Axes
        an instance of the _Axes class
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

        keys = ["store", "size", "unit", "mosaic", "clear", "ion"]
        defaults = [False, [300, 300], "pt", "A", True, False]

        params = Params().getitem("axes")

        attribute_setter = AttributeSetter(keys, defaults, params, **kwargs)
        self._kwargs = attribute_setter.set_attributes(self)

        self._store_class = Store()
        self._store_class.store = self.store

        self.__axes = _Axes()
        self.unit = Unit[self.unit.upper()]
        self.unit_conv = UnitConv()

        self.args = args

        self._open_figure(*self.args, **self._kwargs)

    @property
    def axes(self):
        """
        Gets the _axes attribute.

        Returns
        -------
        list
            The list of axes.
        """

        return self.__axes.axes

    def _open_figure(self, *args, **kwargs):
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
        if self.clear:
            plt.clf()
        if self.ion:
            plt.ion()

        # Set the size of the figure in the unit
        conv_size = tuple(
            map(lambda size: self.unit_conv.convert(size, self.unit), self.size)
        )
        plt.gcf().set_size_inches(*conv_size, **kwargs)

        if self.mosaic != "":
            structures = [
                p[1] for p in (sorted(plt.gcf().subplot_mosaic(self.mosaic).items()))
            ]
            self.__axes.axes = structures
        else:
            raise ValueError("Mosaic must be specified.")
