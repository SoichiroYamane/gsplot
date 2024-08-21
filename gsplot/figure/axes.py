from enum import Enum
from typing import Dict, List, Tuple, Any

import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from .axes_base import AxesSingleton, AxesRangeSingleton
from .store import StoreSingleton
from ..base.base import AttributeSetter
from ..plot.line_base import NumLines


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
    conversion_factors : Dict[Unit, float]
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

        self.conversion_factors: Dict[Unit, float] = {
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


class AxesHandler:
    """
    A class for handling the creation and management of matplotlib Axes objects,
    including configuration of figure size, units, and layout using mosaic.

    Parameters
    ----------
    store : bool, optional
        Whether to store the current figure (default is False).
    size : List[int], optional
        The size of the figure in the specified unit (default is [5, 5]).
    unit : str, optional
        The unit of the figure size (default is "in"). Must be one of 'mm', 'cm', 'in', 'pt'.
    mosaic : str, optional
        The layout of the subplot using a mosaic string (default is "A").
    clear : bool, optional
        Whether to clear the current figure before creating a new one (default is True).
    ion : bool, optional
        Whether to turn on interactive mode in matplotlib (default is False).
    *args : Any
        Additional positional arguments for figure creation.
    **kwargs : Any
        Additional keyword arguments for figure creation.

    Attributes
    ----------
    store : bool
        Whether to store the current figure.
    size : List[int]
        The size of the figure in the specified unit.
    unit : str
        The unit of the figure size.
    mosaic : str
        The layout of the subplot using a mosaic string.
    clear : bool
        Whether to clear the current figure before creating a new one.
    ion : bool
        Whether to turn on interactive mode in matplotlib.
    args : Any
        Additional positional arguments for figure creation.
    kwargs : Any
        Additional keyword arguments for figure creation.
    unit_enum : Unit
        The unit enum corresponding to the specified unit.
    unit_conv : UnitConv
        The UnitConv object used for converting units.
    __axes : AxesSingleton
        The singleton instance of Axes to manage subplot axes.

    Methods
    -------
    get_axes -> List[Axes]
        Returns the list of Axes objects created in the current figure.
    _open_figure() -> None
        Opens a new figure, configures its size, and arranges subplots based on the mosaic string.
    """

    def __init__(
        self,
        store: bool = False,
        size: List[int] = [5, 5],
        unit: str = "in",
        mosaic: str = "A",
        clear: bool = True,
        ion: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.store: bool = store
        self.size: List[int] = size
        self.unit: str = unit
        self.mosaic: str = mosaic
        self.clear: bool = clear
        self.ion: bool = ion
        self.args: Any = args
        self.kwargs: Any = kwargs

        attributer = AttributeSetter()
        self.kwargs = attributer.set_attributes(self, locals(), key="axes")

        self._store_class = StoreSingleton()
        self._store_class.store = self.store

        self.__axes = AxesSingleton()
        self.unit_enum: Unit = Unit[self.unit.upper()]
        self.unit_conv: UnitConv = UnitConv()

        NumLines().reset()

        self._open_figure()

        AxesRangeSingleton().reset(self.__axes.axes)

    @property
    def get_axes(self) -> List[Axes]:
        """
        Returns the list of Axes objects created in the current figure.

        Returns
        -------
        List[Axes]
            A list of Axes objects in the current figure.
        """
        return self.__axes.axes

    def _open_figure(self) -> None:
        """
        Opens a new figure, configures its size, and arranges subplots based on the mosaic string.

        Raises
        ------
        ValueError
            If the figure size list does not contain exactly two elements.
            If the mosaic string is not specified.
        """
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
        plt.gcf().set_size_inches(*conv_size, *self.args, **self.kwargs)

        if self.mosaic != "":
            axes: List[Any] = [
                p[1] for p in (sorted(plt.gcf().subplot_mosaic(self.mosaic).items()))
            ]
            self.__axes.axes = axes

            # To ensure that the axes are tightly packed, otherwise axes sizes will be different after tight_layout is called
            plt.tight_layout()
        else:
            raise ValueError("Mosaic must be specified.")


def axes(
    store: bool = False,
    size: List[int] = [5, 5],
    unit: str = "in",
    mosaic: str = "A",
    clear: bool = True,
    ion: bool = False,
    *args: Any,
    **kwargs: Any,
) -> List[Axes]:
    """
    Creates and returns a list of matplotlib Axes objects based on the provided configuration.

    Parameters
    ----------
    store : bool, optional
        Whether to store the current figure (default is False).
    size : List[int], optional
        The size of the figure in the specified unit (default is [5, 5]).
    unit : str, optional
        The unit of the figure size (default is "in"). Must be one of 'mm', 'cm', 'in', 'pt'.
    mosaic : str, optional
        The layout of the subplot using a mosaic string (default is "A").
    clear : bool, optional
        Whether to clear the current figure before creating a new one (default is True).
    ion : bool, optional
        Whether to turn on interactive mode in matplotlib (default is False).
    *args : Any
        Additional positional arguments for figure creation.
    **kwargs : Any
        Additional keyword arguments for figure creation.

    Returns
    -------
    List[Axes]
        A list of matplotlib Axes objects created based on the specified configuration.

    Examples
    --------
    >>> import gsplot as gs
    >>> axes = gs.axes(size=[6, 4], mosaic="AB;CD")
    """
    __axes_handler = AxesHandler(
        store,
        size,
        unit,
        mosaic,
        clear,
        ion,
        *args,
        **kwargs,
    )

    return __axes_handler.get_axes
