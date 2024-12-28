from typing import Any

import matplotlib.pyplot as plt
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.legend import Legend as Lg
from matplotlib.legend_handler import HandlerBase

from ..base.base import CreateClassParams, ParamsGetter, bind_passed_params

__all__: list[str] = [
    "legend",
    "legend_axes",
    "legend_handlers",
    "legend_reverse",
    "legend_get_handlers",
]


class Legend:
    """
    A class to manage legends for a specific Matplotlib axis.

    This class provides functionality for customizing, reversing, and managing
    legends on a specific axis in a Matplotlib figure.

    Parameters
    --------------------
    ax : Axes
        The target axis for the legend.
    handles : list[Any], optional
        A list of handles for the legend.
    labels : list[str], optional
        A list of labels for the legend.
    handlers : dict, optional
        A dictionary of custom legend handlers.
    *args : Any
        Additional positional arguments for the legend.
    **kwargs : Any
        Additional keyword arguments for the legend.

    Attributes
    --------------------
    handles : list[Any] | None
        The legend handles.
    labels : list[str] | None
        The legend labels.
    handlers : dict | None
        The custom legend handlers.

    Methods
    --------------------
    get_legend_handlers() -> tuple[list[Artist], list[str], dict[Artist, HandlerBase]]
        Retrieves the legend handles, labels, and associated handlers.
    legend() -> matplotlib.legend.Legend
        Adds a legend to the axis.
    legend_handlers() -> matplotlib.legend.Legend
        Adds a legend with custom handles, labels, and handlers.
    reverse_legend() -> matplotlib.legend.Legend
        Adds a legend to the axis with reversed order of handles and labels.
    """

    def __init__(
        self,
        ax: Axes,
        handles: list[Any] | None = None,
        labels: list[str] | None = None,
        handlers: dict | None = None,
        *args: Any,
        **kwargs: Any
    ):
        self.ax: Axes = ax
        self.handles: list[Any] | None = handles
        self.labels: list[str] | None = labels
        self.handlers: dict | None = handlers
        self.args: Any = args
        self.kwargs: Any = kwargs

    def get_legend_handlers(
        self,
    ) -> tuple[list[Artist], list[str], dict[Artist, HandlerBase]]:
        """
        Retrieves the legend handles, labels, and associated handlers for the target axis.

        Returns
        --------------------
        tuple[list[Artist], list[str], dict[Artist, HandlerBase]]
            - handles: The list of legend handles.
            - labels: The list of legend labels.
            - handlers: A dictionary mapping handles to their legend handlers.
        """

        handles, labels = self.ax.get_legend_handles_labels()

        handler_map = Lg(parent=self.ax, handles=[], labels=[]).get_legend_handler_map()

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
        """
        Adds a legend to the target axis.

        Returns
        --------------------
        matplotlib.legend.Legend
            The created legend object.
        """
        _lg = self.ax.legend(*self.args, **self.kwargs)

        return _lg

    def legend_handlers(self) -> Lg:
        """
        Adds a legend with custom handles, labels, and handlers to the target axis.

        Returns
        --------------------
        matplotlib.legend.Legend
            The created legend object with the provided custom handlers.
        """
        _lg = self.ax.legend(
            handles=self.handles,
            labels=self.labels,
            handler_map=self.handlers,
            *self.args,
            **self.kwargs,
        )

        return _lg

    def reverse_legend(self) -> Lg:
        """
        Adds a legend to the target axis with reversed order of handles and labels.

        Returns
        --------------------
        matplotlib.legend.Legend
            The created legend object with reversed order.
        """

        handles, labels, handlers = self.get_legend_handlers()
        _lg = self.ax.legend(
            handles=handles[::-1],
            labels=labels[::-1],
            handler_map=handlers,
            *self.args,
            **self.kwargs,
        )
        return _lg


class LegendAxes:
    """
    A class to manage legends for all axes in the current Matplotlib figure.

    Parameters
    --------------------
    *args : Any
        Additional positional arguments for legends.
    **kwargs : Any
        Additional keyword arguments for legends.

    Attributes
    --------------------
    args : Any
        Positional arguments for legends.
    kwargs : Any
        Keyword arguments for legends.

    Methods
    --------------------
    legend_axes() -> list[matplotlib.legend.Legend]
        Adds legends to all axes in the current figure.
    """

    def __init__(self, *args: Any, **kwargs: Any):
        self.args: Any = args
        self.kwargs: Any = kwargs

    def legend_axes(self) -> list[Lg]:
        """
        Adds legends to all axes in the current Matplotlib figure.

        Returns
        --------------------
        list[matplotlib.legend.Legend]
            A list of legend objects created for each axis.
        """
        _lg_list = []
        for ax in plt.gcf().axes:
            _lg = ax.legend(*self.args, **self.kwargs)
            _lg_list.append(_lg)
        return _lg_list


@bind_passed_params()
def legend(ax: Axes, *args: Any, **kwargs: Any) -> Lg:
    """
    Adds a legend to the specified axis.

    Parameters
    --------------------
    ax : matplotlib.axes.Axes
        The target axis for the legend.
    *args : Any
        Additional positional arguments for the legend.
    **kwargs : Any
        Additional keyword arguments for the legend.

    Notes
    --------------------
    This function utilizes the `ParamsGetter` to retrieve bound parameters and
    the `CreateClassParams` class to handle the merging of default, configuration,
    and passed parameters.

    Returns
    --------------------
    matplotlib.legend.Legend
        The created legend object.

    Examples
    --------------------
    >>> import matplotlib.pyplot as plt
    >>> import numpy as np
    >>> import gsplot as gs
    >>> x = np.linspace(0, 10, 100)
    >>> plt.plot(x, np.sin(x), label="Sine")
    >>> plt.plot(x, np.cos(x), label="Cosine")
    >>> gs.legend(plt.gcf()[0])  # Adds legend to the first axis
    >>> plt.show()
    """
    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    class_params = CreateClassParams(passed_params).get_class_params()

    _legend = Legend(
        class_params["ax"],
        *class_params["args"],
        **class_params["kwargs"],
    )
    return _legend.legend()


@bind_passed_params()
def legend_axes(*args: Any, **kwargs: Any) -> list[Lg]:
    """
    Adds legends to all axes in the current Matplotlib figure.

    Parameters
    --------------------
    *args : Any
        Additional positional arguments for legends.
    **kwargs : Any
        Additional keyword arguments for legends.

    Notes
    --------------------
    This function utilizes the `ParamsGetter` to retrieve bound parameters and
    the `CreateClassParams` class to handle the merging of default, configuration,
    and passed parameters.

    Returns
    --------------------
    list[matplotlib.legend.Legend]
        A list of legend objects created for each axis.

    Examples
    --------------------
    >>> import matplotlib.pyplot as plt
    >>> fig, axes = plt.subplots(2, 1)
    >>> import gsplot as gs
    >>> axes[0].plot([1, 2, 3], [4, 5, 6], label="Line 1")
    >>> axes[1].plot([1, 2, 3], [6, 5, 4], label="Line 2")
    >>> gs.legend_axes()  # Adds legends to all axes
    >>> plt.show()
    """
    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    class_params = CreateClassParams(passed_params).get_class_params()

    _legend_axes = LegendAxes(
        *class_params["args"],
        **class_params["kwargs"],
    )
    return _legend_axes.legend_axes()


@bind_passed_params()
def legend_handlers(
    ax: Axes,
    handles: list[Any] | None = None,
    labels: list[str] | None = None,
    handlers: dict | None = None,
    *args: Any,
    **kwargs: Any
) -> Lg:
    """
    Adds a legend with custom handles, labels, and handlers to the specified axis.

    Parameters
    --------------------
    ax : Axes
        The target axis for the legend. Can be an axis index or an `Axes` object.
    handles : list[Any], optional
        A list of custom handles for the legend.
    labels : list[str], optional
        A list of custom labels for the legend.
    handlers : dict, optional
        A dictionary of custom legend handlers.
    *args : Any
        Additional positional arguments for the legend.
    **kwargs : Any
        Additional keyword arguments for the legend.

    Notes
    --------------------
    This function utilizes the `ParamsGetter` to retrieve bound parameters and
    the `CreateClassParams` class to handle the merging of default, configuration,
    and passed parameters.

    Returns
    --------------------
    matplotlib.legend.Legend
        The created legend object with the provided custom handlers.

    Examples
    --------------------
    >>> import matplotlib.pyplot as plt
    >>> from matplotlib.lines import Line2D
    >>> import gsplot as gs
    >>> fig, ax = plt.subplots()
    >>> ax.plot([0, 1], [0, 1], label="Line A")
    >>> custom_handle = [Line2D([0], [0], color="r", lw=2)]
    >>> gs.legend_handlers(ax, handles=custom_handle, labels=["Custom Line"])
    >>> plt.show()
    """
    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    class_params = CreateClassParams(passed_params).get_class_params()

    _legend = Legend(
        class_params["ax"],
        class_params["handles"],
        class_params["labels"],
        class_params["handlers"],
        *class_params["args"],
        **class_params["kwargs"],
    )
    return _legend.legend_handlers()


@bind_passed_params()
def legend_reverse(
    ax: Axes,
    handles: list[Any] | None = None,
    labels: list[str] | None = None,
    handlers: dict | None = None,
    *args: Any,
    **kwargs: Any
) -> Lg:
    """
    Adds a legend to the specified axis with reversed order of handles and labels.

    Parameters
    --------------------
    ax : Axes
        The target axis for the legend. Can be an axis index or an `Axes` object.
    handles : list[Any], optional
        A list of custom handles for the legend.
    labels : list[str], optional
        A list of custom labels for the legend.
    handlers : dict, optional
        A dictionary of custom legend handlers.
    *args : Any
        Additional positional arguments for the legend.
    **kwargs : Any
        Additional keyword arguments for the legend.

    Notes
    --------------------
    This function utilizes the `ParamsGetter` to retrieve bound parameters and
    the `CreateClassParams` class to handle the merging of default, configuration,
    and passed parameters.

    Returns
    --------------------
    matplotlib.legend.Legend
        The created legend object with reversed order.

    Examples
    --------------------
    >>> import matplotlib.pyplot as plt
    >>> x = [1, 2, 3]
    >>> y1 = [4, 5, 6]
    >>> y2 = [6, 5, 4]
    >>> plt.plot(x, y1, label="Line 1")
    >>> plt.plot(x, y2, label="Line 2")
    >>> legend_reverse(plt.gca()[0])  # Reverses the legend order
    >>> plt.show()
    """
    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    class_params = CreateClassParams(passed_params).get_class_params()

    _legend = Legend(
        class_params["ax"],
        class_params["handles"],
        class_params["labels"],
        class_params["handlers"],
        *class_params["args"],
        **class_params["kwargs"],
    )
    return _legend.reverse_legend()


def legend_get_handlers(
    ax: Axes,
) -> tuple:
    """
    Retrieves the legend handles, labels, and associated handlers for the specified axis.

    Parameters
    --------------------
    ax : Axes
        The target axis for retrieving the legend handlers. Can be an axis index or an `Axes` object.

    Returns
    --------------------
    tuple
        - handles: The list of legend handles.
        - labels: The list of legend labels.
        - handlers: A dictionary mapping handles to their legend handlers.

    Examples
    --------------------
    >>> import matplotlib.pyplot as plt
    >>> import gsplot as gs
    >>> fig, ax = plt.subplots()
    >>> ax.plot([0, 1], [0, 1], label="Line A")
    >>> ax.plot([1, 0], [0, 1], label="Line B")
    >>> handles, labels, handlers = gs.legend_get_handlers(ax)
    >>> print("Handles:", handles)
    >>> print("Labels:", labels)
    >>> print("Handlers:", handlers)
    """
    return Legend(ax).get_legend_handlers()
