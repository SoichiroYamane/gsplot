from typing import Any

import matplotlib.pyplot as plt
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.legend import Legend as Lg
from matplotlib.legend_handler import HandlerBase

from ..base.base import CreateClassParams, ParamsGetter, bind_passed_params
from ..figure.axes_base import AxesResolver


class Legend:

    def __init__(
        self,
        axis_target: int | Axes,
        handles: list[Any] | None = None,
        labels: list[str] | None = None,
        handlers: dict | None = None,
        *args: Any,
        **kwargs: Any
    ):
        self.axis_target: int | Axes = axis_target
        self.handles: list[Any] | None = handles
        self.labels: list[str] | None = labels
        self.handlers: dict | None = handlers
        self.args: Any = args
        self.kwargs: Any = kwargs

        _axes_resolver = AxesResolver(axis_target)
        self.axis_index: int = _axes_resolver.axis_index
        self.axis: Axes = _axes_resolver.axis

    def get_legend_handlers(
        self,
    ) -> tuple[list[Artist], list[str], dict[Artist, HandlerBase]]:

        handles, labels = self.axis.get_legend_handles_labels()

        # handler_map = Lg(
        #     parent=self.axis, handles=[], labels=[]
        # ).get_legend_handler_map()
        # handlers = dict(zip(handles, [handler_map[type(handle)] for handle in handles]))

        handler_map = Lg(
            parent=self.axis, handles=[], labels=[]
        ).get_legend_handler_map()

        handlers = {}
        for handle in handles:
            if type(handle) in handler_map:
                print(handle)
                handlers[handle] = handler_map[type(handle)]
            else:
                # if handle is not in handler_map, pass
                pass

        return handles, labels, handlers

    def legend(self) -> Lg:
        _lg = self.axis.legend(*self.args, **self.kwargs)

        return _lg

    def legend_handlers(self) -> Lg:

        _lg = self.axis.legend(
            handles=self.handles,
            labels=self.labels,
            handler_map=self.handlers,
            *self.args,
            **self.kwargs,
        )

        return _lg

    def reverse_legend(self) -> Lg:

        handles, labels, handlers = self.get_legend_handlers()
        _lg = self.axis.legend(
            handles=handles[::-1],
            labels=labels[::-1],
            handler_map=handlers,
            *self.args,
            **self.kwargs,
        )
        return _lg


@bind_passed_params()
def legend(axis_target: int | Axes, *args: Any, **kwargs: Any) -> Lg:

    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    class_params = CreateClassParams(passed_params).get_class_params()

    _legend = Legend(
        class_params["axis_target"],
        *class_params["args"],
        **class_params["kwargs"],
    )
    return _legend.legend()


@bind_passed_params()
def legend_handlers(
    axis_target: int | Axes,
    handles: list[Any] | None = None,
    labels: list[str] | None = None,
    handlers: dict | None = None,
    *args: Any,
    **kwargs: Any
) -> Lg:

    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    class_params = CreateClassParams(passed_params).get_class_params()

    _legend = Legend(
        class_params["axis_target"],
        class_params["handles"],
        class_params["labels"],
        class_params["handlers"],
        *class_params["args"],
        **class_params["kwargs"],
    )
    return _legend.legend_handlers()


@bind_passed_params()
def legend_reverse(
    axis_target: int | Axes,
    handles: list[Any] | None = None,
    labels: list[str] | None = None,
    handlers: dict | None = None,
    *args: Any,
    **kwargs: Any
) -> Lg:

    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    class_params = CreateClassParams(passed_params).get_class_params()

    _legend = Legend(
        class_params["axis_target"],
        class_params["handles"],
        class_params["labels"],
        class_params["handlers"],
        *class_params["args"],
        **class_params["kwargs"],
    )
    return _legend.reverse_legend()


def legend_get_handlers(
    axis_target: int | Axes,
) -> tuple:

    return Legend(axis_target).get_legend_handlers()
