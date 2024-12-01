from collections.abc import Hashable
from enum import Enum
from typing import Any, Generic, TypeVar

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.typing import HashableList

from ..base.base import CreateClassParams, ParamsGetter, bind_passed_params
from ..plot.line_base import NumLines
from .axes_base import AxesRangeSingleton
from .store import StoreSingleton

_T = TypeVar("_T")


class Unit(Enum):
    """
    Enumeration of supported units for measurement conversions.

    Attributes
    ----------
    MM : str
        Millimeters (mm).
    CM : str
        Centimeters (cm).
    IN : str
        Inches (in).
    PT : str
        Points (pt).
    INVALID : str
        An invalid or unrecognized unit.
    """

    MM = "mm"
    CM = "cm"
    IN = "in"
    PT = "pt"
    INVALID = "invalid"


class UnitConv:
    """
    A class for converting values between different units of measurement.

    Attributes
    ----------
    conversion_factors : dict[Unit, float]
        A dictionary mapping units to their corresponding conversion factors relative to inches.

    Methods
    -------
    convert(value: float, unit: Unit) -> float
        Converts the given value to inches based on the specified unit.
    """

    def __init__(self) -> None:
        """
        Initializes the UnitConv class with predefined conversion factors.
        """

        self.conversion_factors: dict[Unit, float] = {
            Unit.MM: 1 / 25.4,
            Unit.CM: 1 / 2.54,
            Unit.IN: 1,
            Unit.PT: 1 / 72,
        }

    def convert(self, value: float, unit: Unit) -> float:
        """
        Converts the given value to inches based on the specified unit.

        Parameters
        ----------
        value : float
            The value to be converted.
        unit : Unit
            The unit of the value to be converted.

        Returns
        -------
        float
            The converted value in inches.

        Raises
        ------
        ValueError
            If the provided unit is not recognized or is invalid.
        """

        if unit not in self.conversion_factors:
            raise ValueError("Invalid unit")
        return value * self.conversion_factors[unit]


class AxesHandler(Generic[_T]):

    def __init__(
        self,
        store: bool = False,
        size: list[int | float] = [5, 5],
        unit: str = "in",
        mosaic: str | list[HashableList[_T]] | list[HashableList[Hashable]] = "A",
        clear: bool = True,
        ion: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.store = store
        self.size: list[int | float] = size
        self.unit: str = unit
        self.mosaic: str | list[HashableList[_T]] | list[HashableList[Hashable]] = (
            mosaic
        )
        self.clear: bool = clear
        self.ion: bool = ion
        self.args: Any = args
        self.kwargs: Any = kwargs

        self._store_singleton = StoreSingleton()
        self._store_singleton.store = self.store

        self.unit_enum: Unit = Unit[self.unit.upper()]
        self.unit_conv: UnitConv = UnitConv()

    @property
    def get_axes(self) -> list[Axes]:
        return plt.gcf().axes

    def create_figure(self) -> None:
        NumLines().reset()

        if self.ion:
            plt.ion()

        if self.clear:
            plt.gcf().clear()

        if len(self.size) != 2:
            raise ValueError("Size must contain exactly two elements.")

        conv_size: tuple[float, float] = (
            self.unit_conv.convert(self.size[0], self.unit_enum),
            self.unit_conv.convert(self.size[1], self.unit_enum),
        )
        plt.gcf().set_size_inches(*conv_size, *self.args, **self.kwargs)

        if self.mosaic != "":
            plt.gcf().subplot_mosaic(self.mosaic)

            # To ensure that the axes are tightly packed, otherwise axes sizes will be different after tight_layout is called
            plt.tight_layout()
        else:
            raise ValueError("Mosaic must be specified.")

        # Initialize the axes range list by the number of axes in the current figure
        AxesRangeSingleton().reset(plt.gcf().axes)


@bind_passed_params()
def axes(
    store: bool = False,
    size: list[int | float] = [5, 5],
    unit: str = "in",
    mosaic: str | list[HashableList[_T]] | list[HashableList[Hashable]] = "A",
    clear: bool = True,
    ion: bool = False,
    *args: Any,
    **kwargs: Any,
):
    """
    Create and manage Matplotlib axes with customizable options.

    This function creates a Matplotlib figure and axes with user-specified settings,
    such as size, units, layout, and interactivity. It provides flexibility for
    handling mosaic layouts and additional customization through arguments.

    Parameters
    ----------
    store : bool, optional
        If True, store the created axes in a persistent handler for future access.
        Default is False.
    size : list[int or float], optional
        The size of the figure in the specified unit. Default is [5, 5].
    unit : str, optional
        The unit for the figure size. Common values include "in" (inches) and "cm"
        (centimeters). Default is "in".
    mosaic : str or list[HashableList], optional
        The layout of the axes as a mosaic grid. It can be a single-character string
        for a simple layout or a list defining the layout. Default is "A".
    clear : bool, optional
        If True, clear any existing figure or axes before creating new ones. Default
        is True.
    ion : bool, optional
        If True, enable interactive mode for Matplotlib. Default is False.
    *args : Any
        Additional positional arguments passed to the axes creation process.
    **kwargs : Any
        Additional keyword arguments for figure or axes customization.

    Returns
    -------
    Callable
        A callable function to retrieve the created axes.

    Notes
    -----
    - This function leverages the `AxesHandler` class for managing axes creation
      and customization.
    - The mosaic parameter allows complex layouts by specifying a grid pattern
      with strings or nested lists.

    Examples
    --------
    Create a default figure with a single axes:

    >>> axes()

    Create a figure with specific size and units:

    >>> axes(size=[10, 7], unit="cm")

    Use a mosaic layout to create multiple subplots:

    >>> axes(mosaic="AB;CC")

    Enable interactive mode:

    >>> axes(ion=True)

    Pass additional arguments for customization:

    >>> axes(clear=False, dpi=300)
    """
    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    class_params = CreateClassParams(passed_params).get_class_params()

    _axes_handler: AxesHandler = AxesHandler(
        class_params["store"],
        class_params["size"],
        class_params["unit"],
        class_params["mosaic"],
        class_params["clear"],
        class_params["ion"],
        *class_params["args"],
        **class_params["kwargs"],
    )
    _axes_handler.create_figure()
    return _axes_handler.get_axes
