from collections.abc import Hashable
from enum import Enum
from typing import Any, Generic, Literal, TypeVar

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.typing import HashableList

from ..base.base import CreateClassParams, ParamsGetter, bind_passed_params
from ..plot.line_base import NumLines
from .axes_range_base import AxesRangeSingleton
from .store import StoreSingleton

_T = TypeVar("_T")

__all__: list[str] = ["axes"]


class Unit(Enum):
    """
    Enumeration of measurement units for various contexts such as dimensions and typography.

    This class defines common measurement units, including millimeters, centimeters,
    inches, and points. It also includes an "INVALID" option for invalid or unspecified units.

    Attributes
    --------------------
    MM : str
        Represents millimeters ("mm").
    CM : str
        Represents centimeters ("cm").
    IN : str
        Represents inches ("in").
    PT : str
        Represents points ("pt").
    INVALID : str
        Represents an invalid or unspecified unit ("invalid").

    Examples
    --------------------
    >>> unit = Unit.MM
    >>> print(unit)
    Unit.MM
    >>> print(unit.value)
    'mm'

    >>> invalid_unit = Unit.INVALID
    >>> print(invalid_unit)
    Unit.INVALID
    >>> print(invalid_unit.value)
    'invalid'
    """

    MM = "mm"
    CM = "cm"
    IN = "in"
    PT = "pt"
    INVALID = "invalid"


class UnitConv:
    """
    A utility class for converting values between different measurement units.

    This class supports conversion from millimeters (mm), centimeters (cm),
    inches (in), and points (pt) to a base unit of inches. Conversion factors
    are defined for each supported unit.

    Attributes
    --------------------
    conversion_factors : dict of Unit, float
        A dictionary mapping each `Unit` to its corresponding conversion factor to inches.

    Methods
    --------------------
    convert(value, unit)
        Converts a value from the specified unit to inches.

    Examples
    --------------------
    >>> converter = UnitConv()
    >>> inches = converter.convert(10, Unit.CM)
    >>> print(inches)
    3.937007874015748

    >>> points = converter.convert(1, Unit.PT)
    >>> print(points)
    0.013888888888888888

    >>> try:
    ...     converter.convert(10, Unit.INVALID)
    ... except ValueError as e:
    ...     print(e)
    Invalid unit
    """

    def __init__(self) -> None:

        self.conversion_factors: dict[Unit, float] = {
            Unit.MM: 1 / 25.4,
            Unit.CM: 1 / 2.54,
            Unit.IN: 1,
            Unit.PT: 1 / 72,
        }

    def convert(self, value: float, unit: Unit) -> float:
        """
        Converts a value from the specified unit to inches.

        Parameters
        --------------------
        value : float
            The numerical value to convert.
        unit : Unit
            The unit of the value to be converted. Must be a member of the `Unit` enum.

        Returns
        --------------------
        float
            The converted value in inches.

        Raises
        --------------------
        ValueError
            If the specified unit is not supported.

        Examples
        --------------------
        >>> converter = UnitConv()
        >>> inches = converter.convert(10, Unit.CM)
        >>> print(inches)
        3.937007874015748
        """

        if unit not in self.conversion_factors:
            raise ValueError("Invalid unit")
        return value * self.conversion_factors[unit]


class AxesHandler(Generic[_T]):
    """
    A handler for managing Matplotlib figures and axes with custom configurations.

    This class provides a high-level interface for creating and managing Matplotlib
    figures with support for size adjustments, unit conversions, subplot mosaics,
    and interactive plotting. It also integrates singleton patterns for managing
    state across multiple instances.

    Parameters
    --------------------
    store : bool, optional
        Whether to use a shared storage for axes or figure states (default is False).
    size : list of int or float, optional
        The size of the figure in the specified unit (default is [5, 5]).
    unit : str, optional
        The unit for the figure size. Supported units are "mm", "cm", "in", and "pt" (default is "in").
    mosaic : str or list of HashableList[_T] or list of HashableList[Hashable], optional
        The mosaic layout for subplots. Can be a string or a list of hashable items (default is "A").
    clear : bool, optional
        Whether to clear the current figure before creating a new one (default is True).
    ion : bool, optional
        Whether to enable interactive mode for the figure (default is False).
    *args : Any
        Additional positional arguments to pass to Matplotlib's figure creation methods.
    **kwargs : Any
        Additional keyword arguments to pass to Matplotlib's figure creation methods.

    Attributes
    --------------------
    store : bool
        Indicates whether shared storage is used.
    size : list of int or float
        The size of the figure in the specified unit.
    unit : {"mm", "cm", "in", "pt"}
        The unit for the figure size.
    mosaic : str or list of HashableList[_T] or list of HashableList[Hashable]
        The mosaic layout for subplots.
    clear : bool
        Indicates whether the current figure is cleared.
    ion : bool
        Indicates whether interactive mode is enabled.
    unit_enum : Unit
        The unit as an enumerated value for validation and conversion.
    unit_conv : UnitConv
        An instance of `UnitConv` for size conversion.
    get_axes : list of matplotlib.axes.Axes
        A property that retrieves the current figure's axes.

    Methods
    --------------------
    create_figure()
        Creates and configures a Matplotlib figure based on the specified parameters.

    Examples
    --------------------
    >>> handler = AxesHandler(
    ...     size=[10, 8],
    ...     unit="cm",
    ...     mosaic="AB;CD",
    ...     ion=True
    ... )
    >>> handler.create_figure()
    >>> axes = handler.get_axes
    >>> print(axes)
    [<Axes: label='A'>, <Axes: label='B'>, <Axes: label='C'>, <Axes: label='D'>]
    """

    def __init__(
        self,
        store: bool = False,
        size: list[int | float] = [5, 5],
        unit: Literal["mm", "cm", "in", "pt"] = "in",
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
        """
        Retrieves the current figure's axes.

        Returns
        --------------------
        list of matplotlib.axes.Axes
            A list of axes in the current figure.
        """
        return plt.gcf().axes

    def create_figure(self) -> None:
        """
        Creates and configures a Matplotlib figure based on the specified parameters.

        Raises
        --------------------
        ValueError
            If `size` does not contain exactly two elements or if `mosaic` is empty.

        Examples
        --------------------
        >>> handler = AxesHandler(size=[10, 8], unit="cm", mosaic="AB;CD", ion=True)
        >>> handler.create_figure()
        """
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
        AxesRangeSingleton().reset()


@bind_passed_params()
def axes(
    store: bool = False,
    size: list[int | float] = [5, 5],
    unit: Literal["mm", "cm", "in", "pt"] = "in",
    mosaic: str | list[HashableList[_T]] | list[HashableList[Hashable]] = "A",
    clear: bool = True,
    ion: bool = False,
    *args: Any,
    **kwargs: Any,
):
    """
    Creates and configures a Matplotlib figure with specified parameters.

    This function wraps the `AxesHandler` class to provide an easy interface
    for managing Matplotlib figures and their axes. Parameters such as figure size,
    units, mosaic layouts, and additional configuration options can be specified.

    Parameters
    --------------------
    store : bool, optional
        Whether to use a shared storage for axes or figure states (default is False).
    size : list of int or float, optional
        The size of the figure in the specified unit (default is [5, 5]).
    unit : {"mm", "cm", "in", "pt"}, optional
        The unit for the figure size. Supported units are "mm", "cm", "in", and "pt" (default is "in").
    mosaic : str or list of HashableList[_T] or list of HashableList[Hashable], optional
        The mosaic layout for subplots. Can be a string or a list of hashable items (default is "A").
    clear : bool, optional
        Whether to clear the current figure before creating a new one (default is True).
    ion : bool, optional
        Whether to enable interactive mode for the figure (default is False).
    *args : Any
        Additional positional arguments to pass to Matplotlib's figure creation methods.
    **kwargs : Any
        Additional keyword arguments to pass to Matplotlib's figure creation methods.

    Notes
    --------------------
    This function utilizes the `ParamsGetter` to retrieve bound parameters and
    the `CreateClassParams` class to handle the merging of default, configuration,
    and passed parameters.

    Returns
    --------------------
    list of matplotlib.axes.Axes
        A list of axes in the created figure.

    Examples
    --------------------
    >>> import gsplot as
    >>> axs = gs.axes(size=[10, 8], unit="cm", mosaic="AB;CD", ion=True)
    >>> print(axs)
    [<Axes: label='A'>, <Axes: label='B'>, <Axes: label='C'>, <Axes: label='D'>]
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
