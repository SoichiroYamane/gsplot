from typing import Any, Dict, List, Tuple
from matplotlib.axes import Axes
from matplotlib.artist import Artist
from matplotlib.legend import Legend as Lg
from matplotlib.legend_handler import HandlerBase

from ..base.base import AttributeSetter
from ..figure.axes import AxesSingleton


class Legend:
    def __init__(
        self,
        axis_index: int,
        handles: List[Any] | None = None,
        labels: List[str] | None = None,
        handlers: dict | None = None,
        *args: Any,
        **kwargs: Any
    ):
        self.axis_index: int = axis_index
        self.handles: List[Any] | None = handles
        self.labels: List[str] | None = labels
        self.handlers: dict | None = handlers
        self.args: Any = args
        self.kwargs: Any = kwargs

        attributer = AttributeSetter()
        self.kwargs = attributer.set_attributes(self, locals(), key="legend")

        self.__axes: AxesSingleton = AxesSingleton()
        self._axes: List[Axes] = self.__axes.axes
        self._axis: Axes = self._axes[self.axis_index]

    def get_legend_handlers(
        self,
    ) -> Tuple[List[Artist], List[str], Dict[Artist, HandlerBase]]:
        handles, labels = self._axis.get_legend_handles_labels()

        handler_map = Lg(
            parent=self._axis, handles=[], labels=[]
        ).get_legend_handler_map()
        handlers = dict(zip(handles, [handler_map[type(handle)] for handle in handles]))

        return handles, labels, handlers

    def legend(self) -> None:
        self._axis.legend(*self.args, **self.kwargs)

    def legend_handlers(self) -> None:
        self._axis.legend(
            handles=self.handles,
            labels=self.labels,
            handler_map=self.handlers,
            *self.args,
            **self.kwargs,
        )

    def reverse_legend(self) -> None:
        handles, labels, handlers = self.get_legend_handlers()
        self._axis.legend(
            handles=handles[::-1],
            labels=labels[::-1],
            handler_map=handlers,
            *self.args,
            **self.kwargs,
        )


def legend(axis_index: int, *args: Any, **kwargs: Any) -> None:
    Legend(axis_index, *args, **kwargs).legend()


def legend_handlers(
    axis_index: int,
    handles: List[Any] | None = None,
    labels: List[str] | None = None,
    handlers: dict | None = None,
    *args: Any,
    **kwargs: Any
) -> None:
    Legend(axis_index, handles, labels, handlers, *args, **kwargs).legend_handlers()


def legend_reverse(
    axis_index: int,
    handles: List[Any] | None = None,
    labels: List[str] | None = None,
    handlers: dict | None = None,
    *args: Any,
    **kwargs: Any
) -> None:
    Legend(axis_index, handles, labels, handlers, *args, **kwargs).reverse_legend()


def legend_get_handlers(
    axis_index: int,
) -> tuple:
    return Legend(axis_index).get_legend_handlers()
