from typing import cast, List, Optional, Tuple, Any
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.axes import Axes
from matplotlib.transforms import Bbox
from ..base.base import AttributeSetter
from ..figure.axes_base import (
    AxesSingleton,
    AxisRangeController,
    AxesRangeSingleton,
    AxisRangeManager,
)
from .ticks import MinorTicks


class AddIndexToAxes:
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

    def __init__(self) -> None:
        self.__axes: AxesSingleton = AxesSingleton()
        self._axes: list[Axes] = self.__axes.axes

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
            renderer = cast(FigureCanvasAgg, plt.gcf().canvas).get_renderer()
            tight_bbox: Optional[Bbox] = axis.get_tightbbox(renderer)
            coords: Optional[tuple[float, float, float, float]] = None

            if tight_bbox is not None:
                coords = tight_bbox.bounds

            if coords is not None:
                fig_coords = plt.gcf().bbox.bounds
                coords_array = np.array(coords)
                coords_array /= np.array(
                    [fig_coords[2], fig_coords[3], fig_coords[2], fig_coords[3]]
                )
                plt.gcf().text(
                    coords_array[0],
                    coords_array[1] + coords_array[3],
                    "($\\,$%s$\\,$)" % ("abcdefghijklmnopqrstuvwxyz"[i]),
                    ha="center",
                    va="top",
                    fontsize="large",
                )
            else:
                print("No bounding box available.")


def label_add_index() -> None:
    """
    Adds index labels to all axes in the current figure.

    This function uses the `AddIndexToAxes` class to add alphabetical index
    labels to the top center of each axis in the current figure.

    Returns
    -------
    None
    """

    AddIndexToAxes().add_index()


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
        add_index: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:

        self.lab_lims: list[Any] = lab_lims
        self.x_pad: int = x_pad
        self.y_pad: int = y_pad
        self.minor_ticks_all: bool = minor_ticks_all
        self.tight_layout: bool = tight_layout
        self.add_index: bool = add_index
        self.args: Any = args
        self.kwargs: Any = kwargs

        attributer = AttributeSetter()
        self.kwargs = attributer.set_attributes(self, locals(), key="label")

        self.__axes: AxesSingleton = AxesSingleton()
        self._axes: list[Axes] = self.__axes.axes

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
    def _add_index(self) -> None:
        """
        Adds index labels to the axes if specified.

        Uses the `AddIndexToAxes` class to add alphabetical index labels to the axes.

        Returns
        -------
        None
        """

        if self.add_index:
            AddIndexToAxes().add_index()

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
        self._add_index()


def label(
    lab_lims: list[Any],
    x_pad: int = 2,
    y_pad: int = 2,
    minor_ticks_all: bool = True,
    tight_layout: bool = True,
    add_index: bool = False,
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
        add_index,
        *args,
        **kwargs,
    )

    label.label()
