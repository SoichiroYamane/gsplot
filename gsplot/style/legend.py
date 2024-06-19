from ..params.params import Params
from ..base.base import AttributeSetter
from ..plts.axes import AxesSingleton

import matplotlib.pyplot as plt
from matplotlib.legend import Legend as Lg


class Legend:
    def __init__(self, axis_index, *args, **kwargs):
        self.axis_index = axis_index

        self.__axes = AxesSingleton()
        self._axis = self.__axes.axes[self.axis_index]

        defaults = {
            "handles": None,
            "labels": None,
            "handlers": None,
        }

        params = Params().getitem("legend")

        attribute_setter = AttributeSetter(defaults, params, **kwargs)

        self._args = args
        self._kwargs = attribute_setter.set_attributes(self)

    def get_legend_handlers(self) -> tuple:
        handles, labels = self._axis.get_legend_handles_labels()

        handler_map = Lg(
            parent=self._axis, handles=[], labels=[]
        ).get_legend_handler_map()
        handlers = dict(zip(handles, [handler_map[type(handle)] for handle in handles]))

        return handles, labels, handlers

    def legend(self) -> Lg:
        return self._axis.legend(
            handles=self.handles,
            labels=self.labels,
            handler_map=self.handlers,
            *self._args,
            **self._kwargs,
        )

    def reverse_legend(self):
        handles, labels, handlers = self.get_legend_handlers()
        self.legend(handles[::-1], labels[::-1], handlers, *self._args, **self._kwargs)
