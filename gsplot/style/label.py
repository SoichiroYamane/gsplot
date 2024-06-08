from ..params.params import Params
from ..base.base import AttributeSetter
from ..plts.axes import _Axes
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
    __axes : _Axes
        an instance of the _Axes class

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
            "x_pad": 1,
            "y_pad": 1,
            "minor_ticks_all": True,
            "tight_layout": True,
            "add_index": False,
        }

        params = Params().getitem("labels")

        attribute_setter = AttributeSetter(defaults, params, **kwargs)

        self._args = args
        self._kwargs = attribute_setter.set_attributes(self)

        self.__axes = _Axes()

        self.main()

    def xticks(base=None, num_minor=None):
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
            plt.gca().xaxis.set_major_locator(plticker.MultipleLocator(base=base))
        if num_minor != None:
            plt.gca().xaxis.set_minor_locator(plticker.AutoMinorLocator(num_minor))

    def yticks(base=None, num_minor=None):
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
            plt.gca().yaxis.set_major_locator(plticker.MultipleLocator(base=base))
        if num_minor != None:
            plt.gca().yaxis.set_minor_locator(plticker.AutoMinorLocator(num_minor))

    def xlabels_off(self, axis):
        """
        Turns off x-labels on the given axis.

        Parameters
        ----------
            axis : Axes
                the axis on which to turn off x-labels
        """
        axis.xlabel("")
        axis.tick_params(labelbottom=False)

    def ylabels_off(self, axis):
        """
        Turns off y-labels on the given axis.

        Parameters
        ----------
            axis : Axes
                the axis on which to turn off y-labels
        """
        axis.ylabel("")
        axis.tick_params(labelleft=False)

    def _ticks_all(self):
        if self.minor_ticks_all:
            MinorTicks().minor_ticks_all()

    def _add_labels(self):
        for i, (x_lab, y_lab, *lims) in enumerate(self.lab_lims):
            # Change axis pointer only if there are multiple axes
            axis = self.__axes.axes[i]
            if len(self.lab_lims) > 1:
                plt.sca(axis)
            if x_lab == "":
                self.xlabels_off()
            else:
                plt.xlabel(x_lab)
            if y_lab == "":
                self.ylabels_off()
            else:
                plt.ylabel(y_lab)
            if len(lims) > 0:  # Limits are specified
                [x_lims, y_lims] = lims
                set_lims = dict()
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
                        self.GioXticks(num_minor=x_lims[2])
                        if len(x_lims) > 3:
                            self.xticks(base=x_lims[3])
                if len(y_lims) > 2:
                    if type(y_lims[2]) == str:
                        plt.yscale(y_lims[2])
                    else:
                        self.GioYticks(num_minor=y_lims[2])
                        if len(y_lims) > 3:
                            self.yticks(base=y_lims[3])

    def _tight_layout(self):
        if self.tight_layout:
            try:
                plt.tight_layout(
                    w_pad=self.x_pad, h_pad=self.y_pad, *self._args, **self._kwargs
                )
            except:
                plt.tight_layout(w_pad=self.x_pad, h_pad=self.y_pad)

    def _add_index(self):
        if self.add_index:
            AddIndexToAxes(self.__axes.axes).add_index()

    def main(self):
        """
        Executes the main functionality of the class. This includes adding minor ticks, labels, adjusting layout, and adding index.
        """
        self._ticks_all()
        self._add_labels()
        self._tight_layout()
        self._add_index()
