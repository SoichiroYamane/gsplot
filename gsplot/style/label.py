from typing import cast, List, Optional, Tuple, Callable, Any, Literal

from numpy.typing import ArrayLike
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.transforms import Bbox
from ..base.base import AttributeSetter
from ..figure.axes_base import (
    AxisRangeController,
    AxesRangeSingleton,
    AxisRangeManager,
)
from .ticks import MinorTicks

import warnings
from functools import wraps


class FuncOrderManager:
    def __init__(
        self,
    ) -> None:
        self.last_called: str | None = None
        self.rules: dict = {}

    def add_rule(self, func_a: str, func_b: str, warning_message: str) -> None:
        self.rules[(func_b, func_a)] = warning_message

    def track(self, func_name: str) -> None:
        print(func_name)
        if self.last_called and (self.last_called, func_name) in self.rules:
            warnings.warn(self.rules[(self.last_called, func_name)])
        self.last_called = func_name


order_manager = FuncOrderManager()
# !TODO: modify the warning
order_manager.add_rule(
    "label", "label_add_index", "Label should be called before track_order"
)


def track_order(func: Callable) -> Callable:

    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        order_manager.track(func_name)
        return func(*args, **kwargs)

    return wrapper


class LabelAddIndex:
    """
    A class to add index labels to matplotlib axes.

    The `AddIndexToAxes` class adds alphabetical index labels (e.g., (a), (b), etc.)
    to the top center of each axis in the current figure. The index labels correspond
    to the position of the axes in the figure.

    Methods
    -------
    add_index() -> None
        Adds index labels to all axes in the current figure.
    """

    def __init__(
        self,
        position: Literal["in", "out", "corner"] = "out",
        x_offset: float = 0,
        y_offset: float = 0,
        ha: str = "center",
        va: str = "top",
        fontsize: str | float = "large",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.position = position
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.ha = ha
        self.va = va
        self.fontsize = fontsize

        self.args = args
        self.kwargs = kwargs

        self.fig: Figure = plt.gcf()
        self._axes: list[Axes] = plt.gcf().axes

        self.renderer = cast(FigureCanvasAgg, self.fig.canvas).get_renderer()

        self.fig_width, self.fig_height = (
            self.fig.bbox.bounds[2],
            self.fig.bbox.bounds[3],
        )
        self.canvas_width, self.canvas_height = self.fig.canvas.get_width_height()

        # To convert from device coordinates to figure coordinates
        self.normalization_factors = np.array(
            [self.fig_width, self.fig_height, self.fig_width, self.fig_height]
        )

    def _get_render_position(self, axis: Axes) -> tuple[float, float] | None:
        bbox: Bbox | None = None
        PADDING_X: float = 0
        PADDING_Y: float = 0

        if self.position == "out":
            # Coordinate: device coordinates
            bbox = axis.get_tightbbox(self.renderer)
            PADDING_X, PADDING_Y = 0, -5
        elif self.position == "in":
            # Coordinate: device coordinates
            bbox = axis.get_window_extent(self.renderer)
            PADDING_X, PADDING_Y = 30, -30
        elif self.position == "corner":
            bbox = axis.get_window_extent(self.renderer)
        else:
            raise ValueError(
                f"Invalid position: {self.position}, must be 'in', 'out', or 'corner'"
            )

        # Ensure that padding does not depend on the figure size
        PADDING_X = PADDING_X / self.canvas_width
        PADDING_Y = PADDING_Y / self.canvas_height

        if bbox is None:
            print(f"No bounding box available for the axis. axis: {axis}")
            return None

        # Calculate the axis bounds in figure coordinates
        axis_bounds_on_fig = np.array(bbox.bounds) / self.normalization_factors

        x0 = axis_bounds_on_fig[0]
        y0 = axis_bounds_on_fig[1]
        width = axis_bounds_on_fig[2]
        height = axis_bounds_on_fig[3]

        x = x0 + self.x_offset + PADDING_X
        y = y0 + height + self.y_offset + PADDING_Y
        return x, y

    def add_index(self) -> None:
        """
        Adds index labels to all axes in the current figure.

        The index labels are placed at the top center of each axis, based on the
        alphabetical order corresponding to their position.

        Returns
        -------
        None
        """

        for i, axis in enumerate(self._axes):
            position = self._get_render_position(axis)
            if position is None:
                continue
            x, y = position

            #!TODO: enable numbers and roman numerals
            self.fig.text(
                x,
                y,
                "($\\,$%s$\\,$)" % ("abcdefghijklmnopqrstuvwxyz"[i]),
                ha=self.ha,
                va=self.va,
                fontsize=self.fontsize,
                transform=self.fig.transFigure,
                *self.args,
                **self.kwargs,
            )


@track_order
def label_add_index(
    position: Literal["in", "out", "corner"] = "out",
    x_offset: float = 0,
    y_offset: float = 0,
    ha: str = "center",
    va: str = "center",
    fontsize: float | str = "large",
    *args: Any,
    **kwargs: Any,
) -> None:
    """
    Adds index labels to all axes in the current figure.

    This function uses the `AddIndexToAxes` class to add alphabetical index
    labels to the top center of each axis in the current figure.

    Returns
    -------
    None
    """

    LabelAddIndex(
        position, x_offset, y_offset, ha, va, fontsize, *args, **kwargs
    ).add_index()


class Label:
    """
    A class to label and adjust matplotlib axes in the current figure.

    The `Label` class provides functionality to label axes with specified labels and limits,
    adjust ticks, and apply tight layout adjustments. Optionally, it can add alphabetical
    index labels to the axes.

    Parameters
    ----------
    lab_lims : list[Any]
        A list of labels and limits for the axes.
    x_pad : int, optional
        Padding for the x-axis when applying tight layout (default is 2).
    y_pad : int, optional
        Padding for the y-axis when applying tight layout (default is 2).
    minor_ticks_all : bool, optional
        Whether to add minor ticks to all axes (default is True).
    tight_layout : bool, optional
        Whether to apply tight layout adjustments (default is True).
    add_index : bool, optional
        Whether to add alphabetical index labels to the axes (default is False).
    *args : Any
        Additional positional arguments passed to the matplotlib layout functions.
    **kwargs : Any
        Additional keyword arguments passed to the matplotlib layout functions.

    Methods
    -------
    label() -> None
        Applies labels, adjusts ticks, applies tight layout, and optionally adds index labels.
    """

    def __init__(
        self,
        lab_lims: list[Any],
        x_pad: int = 2,
        y_pad: int = 2,
        minor_ticks_all: bool = True,
        tight_layout: bool = True,
        *args: Any,
        **kwargs: Any,
    ) -> None:

        self.lab_lims: list[Any] = lab_lims
        self.x_pad: int = x_pad
        self.y_pad: int = y_pad
        self.minor_ticks_all: bool = minor_ticks_all
        self.tight_layout: bool = tight_layout
        self.args: Any = args
        self.kwargs: Any = kwargs

        attributer = AttributeSetter()
        self.kwargs = attributer.set_attributes(self, locals(), key="label")

        self._axes: list[Axes] = plt.gcf().axes

    def xticks(
        self, axis: Axes, base: float | None = None, num_minor: int | None = None
    ) -> None:
        """
        Sets the x-axis ticks and minor ticks for a given axis.

        Parameters
        ----------
        axis : Axes
            The axis on which to set the x-axis ticks.
        base : float, optional
            The base value for the major ticks (default is None).
        num_minor : int, optional
            The number of minor ticks to set (default is None).

        Returns
        -------
        None
        """

        if base is not None:
            axis.xaxis.set_major_locator(plticker.MultipleLocator(base=base))
        if num_minor is not None:
            axis.xaxis.set_minor_locator(plticker.AutoMinorLocator(num_minor))

    def yticks(
        self, axis: Axes, base: float | None = None, num_minor: int | None = None
    ) -> None:
        """
        Sets the y-axis ticks and minor ticks for a given axis.

        Parameters
        ----------
        axis : Axes
            The axis on which to set the y-axis ticks.
        base : float, optional
            The base value for the major ticks (default is None).
        num_minor : int, optional
            The number of minor ticks to set (default is None).

        Returns
        -------
        None
        """

        if base is not None:
            axis.yaxis.set_major_locator(plticker.MultipleLocator(base=base))
        if num_minor is not None:
            axis.yaxis.set_minor_locator(plticker.AutoMinorLocator(num_minor))

    def xlabels_off(self, axis: Axes) -> None:
        """
        Disables the x-axis labels for a given axis.

        Parameters
        ----------
        axis : Axes
            The axis on which to disable the x-axis labels.

        Returns
        -------
        None
        """

        axis.set_xlabel("")
        axis.tick_params(labelbottom=False)

    def ylabels_off(self, axis: Axes) -> None:
        """
        Disables the y-axis labels for a given axis.

        Parameters
        ----------
        axis : Axes
            The axis on which to disable the y-axis labels.

        Returns
        -------
        None
        """

        axis.set_ylabel("")
        axis.tick_params(labelleft=False)

    def _ticks_all(self) -> None:
        """
        Adds minor ticks to all axes in the current figure if specified.

        Returns
        -------
        None
        """

        if self.minor_ticks_all:
            MinorTicks().minor_ticks_all()

    def _add_labels(self) -> None:
        """
        Adds labels and sets limits for all axes in the current figure.

        The labels and limits are specified during the initialization of the class.

        Returns
        -------
        None
        """

        final_axes_range = self._get_final_axes_range()
        for i, (x_lab, y_lab, *lims) in enumerate(self.lab_lims):
            # Change axis pointer only if there are multiple axes
            axis = self._axes[i]
            if len(self.lab_lims) > 1:
                plt.sca(axis)
            if x_lab == "":
                self.xlabels_off(axis)
            else:
                axis.set_xlabel(x_lab)
            if y_lab == "":
                self.ylabels_off(axis)
            else:
                axis.set_ylabel(y_lab)

            if len(lims) > 0:  # Limits are specified
                [x_lims, y_lims] = lims
                for lim, val in zip(
                    ["xmin", "xmax", "ymin", "ymax"],
                    [x_lims[0], x_lims[1], y_lims[0], y_lims[1]],
                ):
                    if val != "":
                        axis.axis(**{lim: val})
                if len(x_lims) > 2:
                    if isinstance(x_lims[2], str):
                        axis.set_xscale(x_lims[2])
                    else:
                        self.xticks(axis, num_minor=x_lims[2])
                        if len(x_lims) > 3:
                            self.xticks(axis, base=x_lims[3])
                if len(y_lims) > 2:
                    if isinstance(y_lims[2], str):
                        plt.yscale(y_lims[2])
                    else:
                        self.yticks(axis, num_minor=y_lims[2])
                        if len(y_lims) > 3:
                            self.yticks(axis, base=y_lims[3])
            else:
                final_axis_range = final_axes_range[i]
                plt.axis(
                    xmin=final_axis_range[0][0],
                    xmax=final_axis_range[0][1],
                    ymin=final_axis_range[1][0],
                    ymax=final_axis_range[1][1],
                )

        self._get_final_axes_range()

    def _calculate_padding_range(self, range: np.ndarray) -> np.ndarray:
        """
        Calculates the padded range for axis limits.

        Adds a padding factor to the provided range to ensure some space around the data.

        Parameters
        ----------
        range : np.ndarray
            The original range as a NumPy array.

        Returns
        -------
        np.ndarray
            The padded range as a NumPy array.
        """

        PADDING_FACTOR: float = 0.05
        span: float = range[1] - range[0]
        return np.array(
            range + np.array([-PADDING_FACTOR, PADDING_FACTOR]) * span, dtype=np.float64
        )

    def _get_wider_range(self, range1: np.ndarray, range2: np.ndarray) -> np.ndarray:
        """
        Combines two ranges to get a wider range.

        Finds the minimum and maximum values between two ranges and returns the combined range.

        Parameters
        ----------
        range1 : np.ndarray
            The first range as a NumPy array.
        range2 : np.ndarray
            The second range as a NumPy array.

        Returns
        -------
        np.ndarray
            The combined wider range as a NumPy array.
        """

        new_range = np.array([min(range1[0], range2[0]), max(range1[1], range2[1])])
        return new_range

    def _get_axes_ranges_current(self) -> list[list[np.ndarray]]:
        """
        Retrieves the current axis ranges for all axes in the figure.

        Returns
        -------
        list[list[np.ndarray]]
            A list of lists containing the x and y ranges for each axis.
        """

        axes_ranges_current = []
        for axis_index in range(len(self._axes)):
            xrange = AxisRangeController(axis_index).get_axis_xrange()
            yrange = AxisRangeController(axis_index).get_axis_yrange()
            axes_ranges_current.append([xrange, yrange])
        return axes_ranges_current

    def _get_final_axes_range(self) -> list[list[np.ndarray]]:
        """
        Determines the final axis ranges, considering initial and current axis ranges.

        Returns
        -------
        list[list[np.ndarray]]
            A list of lists containing the final x and y ranges for each axis.
        """

        axes_ranges_singleton = AxesRangeSingleton().axes_ranges
        axes_ranges_current = self._get_axes_ranges_current()

        final_axes_ranges = []
        for axis_index, (xrange, yrange) in enumerate(axes_ranges_current):
            xrange_singleton = axes_ranges_singleton[axis_index][0]
            yrange_singleton = axes_ranges_singleton[axis_index][1]

            is_init_axis = AxisRangeManager(axis_index).is_init_axis()

            if is_init_axis and xrange_singleton is not None:
                new_xrange = xrange_singleton
            elif not is_init_axis and xrange_singleton is not None:
                new_xrange = self._get_wider_range(xrange, xrange_singleton)
            else:
                new_xrange = xrange

            if is_init_axis and yrange_singleton is not None:
                new_yrange = yrange_singleton
            elif not is_init_axis and yrange_singleton is not None:
                new_yrange = self._get_wider_range(yrange, yrange_singleton)
            else:
                new_yrange = yrange

            new_xrange = self._calculate_padding_range(new_xrange)
            new_yrange = self._calculate_padding_range(new_yrange)

            final_axes_ranges.append([new_xrange, new_yrange])
        return final_axes_ranges

    #! Xpad and Ypad will change the size of the axis
    def _tight_layout(self) -> None:
        """
        Applies tight layout adjustments to the figure.

        Adds padding between subplots to prevent overlap of labels and titles.

        Returns
        -------
        None
        """

        if self.tight_layout:
            try:
                plt.tight_layout(
                    w_pad=self.x_pad, h_pad=self.y_pad, *self.args, **self.kwargs
                )
            except Exception:
                plt.tight_layout(w_pad=self.x_pad, h_pad=self.y_pad)

    #! Adding index will change the size of axis

    def label(self) -> None:
        """
        Applies labels, adjusts ticks, applies tight layout, and optionally adds index labels.

        This method combines all the labeling and adjustment functionalities provided by the class.

        Returns
        -------
        None
        """

        self._ticks_all()
        self._add_labels()
        self._tight_layout()


@track_order
def label(
    lab_lims: list[Any],
    x_pad: int = 2,
    y_pad: int = 2,
    minor_ticks_all: bool = True,
    tight_layout: bool = True,
    *args: Any,
    **kwargs: Any,
) -> None:
    """
    Labels and adjusts matplotlib axes in the current figure.

    Parameters
    ----------
    lab_lims : list[Any]
        A list of labels and limits for the axes.
    x_pad : int, optional
        Padding for the x-axis when applying tight layout (default is 2).
    y_pad : int, optional
        Padding for the y-axis when applying tight layout (default is 2).
    minor_ticks_all : bool, optional
        Whether to add minor ticks to all axes (default is True).
    tight_layout : bool, optional
        Whether to apply tight layout adjustments (default is True).
    add_index : bool, optional
        Whether to add alphabetical index labels to the axes (default is False).
    *args : Any
        Additional positional arguments passed to the matplotlib layout functions.
    **kwargs : Any
        Additional keyword arguments passed to the matplotlib layout functions.

    Returns
    -------
    None
    """

    label = Label(
        lab_lims,
        x_pad,
        y_pad,
        minor_ticks_all,
        tight_layout,
        *args,
        **kwargs,
    )

    label.label()
