from ..params.params import Params
from ..base.base import AttributeSetter
from ..plts.axes_base import (
    AxesSingleton,
    AxisRangeController,
    AxesRangeSingleton,
    AxisRangeManager,
)
from .ticks import MinorTicks


import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import numpy as np


class AddIndexToAxes:
    """
    A class used to add index to the axes of a plot.

    ...

    Attributes
    ----------
    _axes : list
        a list of axes to which the index will be added

    Methods
    -------
    add_index():
        Adds an index to each axis in the _axes attribute.
    """

    def __init__(self, axes):
        """
        Constructs all the necessary attributes for the AddIndexToAxes object.

        Parameters
        ----------
            axes : list
                a list of axes to which the index will be added
        """
        self._axes = axes

    def add_index(self):
        """
        Adds an index to each axis in the _axes attribute. The index is a letter from 'a' to 'z'.
        The position of the index is determined by the bounding box of the axis.
        """
        for i, axis in enumerate(self._axes):
            # search Get text bounding box, independent of backend, transforms.Bbox.bounds python
            coords = axis.get_tightbbox(plt.gcf().canvas.get_renderer()).bounds
            fig_coords = plt.gcf().bbox.bounds
            coords /= np.array(
                [fig_coords[2], fig_coords[3], fig_coords[2], fig_coords[3]]
            )
            plt.gcf().text(
                coords[0],
                coords[1] + coords[3],
                "($\\,$%s$\\,$)" % ("abcdefghijklmnopqrstuvwxyz"[i]),
                ha="center",
                va="top",
                fontsize="large",
            )


# strictly speaking, this is axis
class Labels:
    """
    A class used to manage labels and ticks on a plot.

    ...

    Attributes
    ----------
    _kwargs : dict
        a dictionary of keyword arguments passed to the class
    _args : tuple
        a tuple of positional arguments passed to the class
    __axes : AxesSingleton
        an instance of the AxesSingleton class

    Example
    -------
    >>> labels = Labels(
    ...     lab_lims=[
    ...         ["x_label1", "y_label1", ["x_min1", "x_max1"], ["y_min1", "y_max1"]],
    ...         ["x_label2", "y_label2", ["x_min2", "x_max2"], ["y_min2", "y_max2"]],
    ...         # Add more lists for more axes
    ...     ]
    ... )
    >>> labels.main()  # Call the main method to apply the labels and limits to the axes

    Methods
    -------
    xticks(base=None, num_minor=None):
        Sets the x-ticks on the current axis.
    yticks(base=None, num_minor=None):
        Sets the y-ticks on the current axis.
    xlabels_off(axis):
        Turns off x-labels on the given axis.
    ylabels_off(axis):
        Turns off y-labels on the given axis.
    _ticks_all():
        Adds minor ticks to all axes if minor_ticks_all is True.
    _add_labels():
        Adds labels to the axes based on the lab_lims attribute.
    _tight_layout():
        Adjusts the padding between and around the subplots.
    _add_index():
        Adds an index to each axis if add_index is True.
    main():
        Executes the main functionality of the class.
    """

    def __init__(
        self,
        lab_lims=None,
        *args,
        **kwargs,
    ):
        """
        Constructs all the necessary attributes for the Labels object.

        Parameters
        ----------
            lab_lims : list
                a list of labels and limits for the axes. Each element of the list should be another list in the format [x_label, y_label, *x_lims, *y_lims], where:
                - x_label (str): The label for the x-axis.
                - y_label (str): The label for the y-axis.
                - x_lims (list): The limits for the x-axis. This should be a list of two elements [x_min, x_max].
                - y_lims (list): The limits for the y-axis. This should be a list of two elements [y_min, y_max].
            args : tuple
                a tuple of positional arguments
            kwargs : dict
                a dictionary of keyword arguments
        """
        defaults = {
            "lab_lims": lab_lims if lab_lims is not None else [],
            "x_pad": 0,
            "y_pad": 0,
            "minor_ticks_all": True,
            "tight_layout": True,
            "add_index": False,
        }

        params = Params().getitem("labels")

        attribute_setter = AttributeSetter(defaults, params, **kwargs)

        self._args = args
        self._kwargs = attribute_setter.set_attributes(self)

        self.__axes = AxesSingleton()
        self._axes = self.__axes.axes

        self.main()

    def xticks(axis, base=None, num_minor=None):
        """
        Sets the x-ticks on the current axis.

        Parameters
        ----------
            base : float, optional
                The base step between each major tick.
            num_minor : int, optional
                The number of minor ticks between each pair of major ticks.
        """
        if base != None:
            axis.xaxis.set_major_locator(plticker.MultipleLocator(base=base))
        if num_minor != None:
            axis.xaxis.set_minor_locator(plticker.AutoMinorLocator(num_minor))

    def yticks(axis, base=None, num_minor=None):
        """
        Sets the y-ticks on the current axis.

        Parameters
        ----------
            base : float, optional
                The base step between each major tick.
            num_minor : int, optional
                The number of minor ticks between each pair of major ticks.
        """
        if base != None:
            axis.yaxis.set_major_locator(plticker.MultipleLocator(base=base))
        if num_minor != None:
            axis.yaxis.set_minor_locator(plticker.AutoMinorLocator(num_minor))

    def xlabels_off(self, axis):
        """
        Turns off x-labels on the given axis.

        Parameters
        ----------
            axis : Axes
                the axis on which to turn off x-labels
        """
        axis.set_xlabel("")
        axis.tick_params(labelbottom=False)

    def ylabels_off(self, axis):
        """
        Turns off y-labels on the given axis.

        Parameters
        ----------
            axis : Axes
                the axis on which to turn off y-labels
        """
        axis.set_ylabel("")
        axis.tick_params(labelleft=False)

    def _ticks_all(self):
        if self.minor_ticks_all:
            MinorTicks().minor_ticks_all()

    def _add_labels(self):
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
                pass
            if y_lab == "":
                self.ylabels_off(axis)
            else:
                axis.set_ylabel(y_lab)
                pass
            if len(lims) > 0:  # Limits are specified
                [x_lims, y_lims] = lims
                for lim, val in zip(
                    ["xmin", "xmax", "ymin", "ymax"],
                    [x_lims[0], x_lims[1], y_lims[0], y_lims[1]],
                ):
                    if val != "":
                        plt.axis(**{lim: val})
                if len(x_lims) > 2:
                    if type(x_lims[2]) == str:
                        plt.xscale(x_lims[2])
                    else:
                        self.xticks(axis, num_minor=x_lims[2])
                        if len(x_lims) > 3:
                            self.xticks(axis, base=x_lims[3])
                if len(y_lims) > 2:
                    if type(y_lims[2]) == str:
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
        PADDING_FACTOR = 0.05
        span = range[1] - range[0]
        return range + np.array([-PADDING_FACTOR, PADDING_FACTOR]) * span

    def _get_wider_range(self, range1: np.ndarray, range2: np.ndarray) -> np.ndarray:
        new_range = np.array([min(range1[0], range2[0]), max(range1[1], range2[1])])
        return new_range

    def _get_axes_range_current(self) -> list:
        axes_range_current = []
        for axis_index in range(len(self._axes)):
            xrange = AxisRangeController(axis_index).get_axis_xrange()
            yrange = AxisRangeController(axis_index).get_axis_yrange()
            axes_range_current.append([xrange, yrange])
        return axes_range_current

    def _get_final_axes_range(self) -> list:
        axes_range_singleton = AxesRangeSingleton().axes_range
        axes_range_current = self._get_axes_range_current()

        final_axes_range = []
        for axis_index, (xrange, yrange) in enumerate(axes_range_current):
            xrange_singleton = axes_range_singleton[axis_index][0]
            yrange_singleton = axes_range_singleton[axis_index][1]

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

            final_axes_range.append([new_xrange, new_yrange])
        return final_axes_range

    def _get_wider_range(self, range1: np.ndarray, range2: np.ndarray) -> np.ndarray:
        new_range = np.array([min(range1[0], range2[0]), max(range1[1], range2[1])])
        return new_range

    #! Xpad and Ypad will change the size of the axis
    def _tight_layout(self):
        if self.tight_layout:
            try:
                plt.tight_layout(
                    w_pad=self.x_pad, h_pad=self.y_pad, *self._args, **self._kwargs
                )
            except:
                plt.tight_layout(w_pad=self.x_pad, h_pad=self.y_pad)

    #! Adding index will change the size of axis
    def _add_index(self):
        if self.add_index:
            AddIndexToAxes(self._axes).add_index()

    def main(self):
        """
        Executes the main functionality of the class. This includes adding minor ticks, labels, adjusting layout, and adding index.
        """
        self._ticks_all()
        self._add_labels()
        self._tight_layout()
        self._add_index()
        pass
