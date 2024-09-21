from typing import Any, Dict, List, Tuple
from matplotlib.axes import Axes
from matplotlib.artist import Artist
from matplotlib.legend import Legend as Lg
from matplotlib.legend_handler import HandlerBase

from ..base.base import AttributeSetter
from ..figure.axes import AxesSingleton


class Legend:
    """
    A class to manage legends on matplotlib axes.

    This class provides methods to create, customize, and manage legends
    on specific matplotlib axes, including the ability to reverse legend
    entries and use custom handlers.

    Parameters
    ----------
    axis_index : int
        Index of the axis to apply the legend to.
    handles : list[Any], optional
        Custom legend handles to use, by default None.
    labels : list[str], optional
        Custom legend labels to use, by default None.
    handlers : dict, optional
        Custom legend handlers to use, by default None.
    *args : Any
        Additional positional arguments for matplotlib legend.
    **kwargs : Any
        Additional keyword arguments for matplotlib legend.
    """

    def __init__(
        self,
        axis_index: int,
        handles: list[Any] | None = None,
        labels: list[str] | None = None,
        handlers: dict | None = None,
        *args: Any,
        **kwargs: Any
    ):
        self.axis_index: int = axis_index
        self.handles: list[Any] | None = handles
        self.labels: list[str] | None = labels
        self.handlers: dict | None = handlers
        self.args: Any = args
        self.kwargs: Any = kwargs

        attributer = AttributeSetter()
        self.kwargs = attributer.set_attributes(self, locals(), key="legend")

        self.__axes: AxesSingleton = AxesSingleton()
        self._axes: list[Axes] = self.__axes.axes
        self._axis: Axes = self._axes[self.axis_index]

    def get_legend_handlers(
        self,
    ) -> tuple[list[Artist], list[str], dict[Artist, HandlerBase]]:
        """
        Retrieve the handles, labels, and handler map for the legend.

        Returns
        -------
        tuple[list[Artist], list[str], dict[Artist, HandlerBase]]
            The handles, labels, and handler map for the legend.
        """

        handles, labels = self._axis.get_legend_handles_labels()

        handler_map = Lg(
            parent=self._axis, handles=[], labels=[]
        ).get_legend_handler_map()
        handlers = dict(zip(handles, [handler_map[type(handle)] for handle in handles]))

        return handles, labels, handlers

    def legend(self) -> None:
        """
        Apply the legend to the specified axis.

        Returns
        -------
        None
        """

        self._axis.legend(*self.args, **self.kwargs)

    def legend_handlers(self) -> None:
        """
        Apply the legend with custom handlers to the specified axis.

        Returns
        -------
        None
        """

        self._axis.legend(
            handles=self.handles,
            labels=self.labels,
            handler_map=self.handlers,
            *self.args,
            **self.kwargs,
        )

    def reverse_legend(self) -> None:
        """
        Reverse the order of legend entries and apply to the specified axis.

        Returns
        -------
        None
        """

        handles, labels, handlers = self.get_legend_handlers()
        self._axis.legend(
            handles=handles[::-1],
            labels=labels[::-1],
            handler_map=handlers,
            *self.args,
            **self.kwargs,
        )


def legend(axis_index: int, *args: Any, **kwargs: Any) -> None:
    """
    Apply a legend to the specified axis.

    Parameters
    ----------
    axis_index : int
        Index of the axis to apply the legend to.
    *args : Any
        Additional positional arguments for matplotlib legend.
    **kwargs : Any
        Additional keyword arguments for matplotlib legend.

    Returns
    -------
    None
    """

    Legend(axis_index, *args, **kwargs).legend()


def legend_handlers(
    axis_index: int,
    handles: list[Any] | None = None,
    labels: list[str] | None = None,
    handlers: dict | None = None,
    *args: Any,
    **kwargs: Any
) -> None:
    """
    Apply a legend with custom handlers to the specified axis.

    Parameters
    ----------
    axis_index : int
        Index of the axis to apply the legend to.
    handles : list[Any], optional
        Custom legend handles to use, by default None.
    labels : list[str], optional
        Custom legend labels to use, by default None.
    handlers : dict, optional
        Custom legend handlers to use, by default None.
    *args : Any
        Additional positional arguments for matplotlib legend.
    **kwargs : Any
        Additional keyword arguments for matplotlib legend.

    Returns
    -------
    None
    """

    Legend(axis_index, handles, labels, handlers, *args, **kwargs).legend_handlers()


def legend_reverse(
    axis_index: int,
    handles: list[Any] | None = None,
    labels: list[str] | None = None,
    handlers: dict | None = None,
    *args: Any,
    **kwargs: Any
) -> None:
    """
    Apply a legend with reversed order of entries to the specified axis.

    Parameters
    ----------
    axis_index : int
        Index of the axis to apply the legend to.
    handles : list[Any], optional
        Custom legend handles to use, by default None.
    labels : list[str], optional
        Custom legend labels to use, by default None.
    handlers : dict, optional
        Custom legend handlers to use, by default None.
    *args : Any
        Additional positional arguments for matplotlib legend.
    **kwargs : Any
        Additional keyword arguments for matplotlib legend.

    Returns
    -------
    None
    """

    Legend(axis_index, handles, labels, handlers, *args, **kwargs).reverse_legend()


def legend_get_handlers(
    axis_index: int,
) -> tuple:
    """
    Retrieve the handles, labels, and handler map for the legend.

    Parameters
    ----------
    axis_index : int
        Index of the axis to retrieve the legend handlers for.

    Returns
    -------
    tuple[list[Artist], list[str], dict[Artist, HandlerBase]]
        The handles, labels, and handler map for the legend.
    """

    return Legend(axis_index).get_legend_handlers()
