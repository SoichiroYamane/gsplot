from typing import List
from matplotlib import rcParams
from matplotlib.axes import Axes

from ..figure.axes_base import AxesSingleton


class GraphSquare:
    """
    A class for setting the aspect ratio of matplotlib axes to be square.

    The `GraphSquare` class allows setting individual or all axes in a figure
    to have a square aspect ratio, meaning the data scales equally on both axes.

    Methods
    -------
    set_square(axis_index: int) -> None
        Sets the aspect ratio of the specified axis to be square.
    set_square_all() -> None
        Sets the aspect ratio of all axes to be square.
    """

    def __init__(self) -> None:
        self.__axes: AxesSingleton = AxesSingleton()
        self._axes: List[Axes] = self.__axes.axes

    def set_square(self, axis_index: int) -> None:
        """
        Sets the aspect ratio of the specified axis to be square.

        Parameters
        ----------
        axis_index : int
            The index of the axis to set the aspect ratio.

        Returns
        -------
        None
        """

        axis: Axes = self._axes[axis_index]
        axis.set_box_aspect(1)

    def set_square_all(self) -> None:
        """
        Sets the aspect ratio of all axes to be square.

        Returns
        -------
        None
        """

        for axis in self._axes:
            axis.set_box_aspect(1)


def graph_square(axis_index: int) -> None:
    """
    Sets the aspect ratio of the specified axis to be square.

    Parameters
    ----------
    axis_index : int
        The index of the axis to set the aspect ratio.

    Returns
    -------
    None
    """

    GraphSquare().set_square(axis_index)


def graph_square_all() -> None:
    """
    Sets the aspect ratio of all axes to be square.

    Returns
    -------
    None
    """

    GraphSquare().set_square_all()


class GraphWhite:
    """
    A class for setting the color scheme of matplotlib axes to white.

    The `GraphWhite` class allows setting individual or all axes in a figure
    to have white-colored labels, ticks, and titles, suitable for dark backgrounds.

    Methods
    -------
    set_white(axis_index: int) -> None
        Sets the color scheme of the specified axis to white.
    set_white_all() -> None
        Sets the color scheme of all axes to white.
    set_white_axis(axis_index: int) -> None
        Sets the color scheme of the specified axis to white, including spines.
    set_white_axis_all() -> None
        Sets the color scheme of all axes to white, including spines.
    """

    def __init__(self) -> None:
        self.__axes: AxesSingleton = AxesSingleton()
        self._axes: List[Axes] = self.__axes.axes

    def set_white(self, axis_index: int) -> None:
        """
        Sets the color scheme of the specified axis to white.

        This includes the axis labels, ticks, and titles.

        Parameters
        ----------
        axis_index : int
            The index of the axis to set the color scheme.

        Returns
        -------
        None
        """

        axis: Axes = self._axes[axis_index]

        axis.xaxis.label.set_color("w")
        axis.yaxis.label.set_color("w")
        axis.title.set_color("w")
        for child in axis.get_children():
            if hasattr(child, "set_color"):
                child.set_color("w")  # type: ignore
        axis.tick_params(axis="x", which="both", colors="w")
        axis.tick_params(axis="y", which="both", colors="w")

        axis.patch.set_alpha(0)

    def set_white_all(self) -> None:
        """
        Sets the color scheme of all axes to white.

        This includes the axis labels, ticks, and titles.

        Returns
        -------
        None
        """

        rcParams["text.color"] = "w"
        for axis_index in range(len(self._axes)):
            self.set_white(axis_index)

    def set_white_axis(self, axis_index: int) -> None:
        """
        Sets the color scheme of the specified axis to white, including spines.

        This includes the axis labels, ticks, titles, and spines.

        Parameters
        ----------
        axis_index : int
            The index of the axis to set the color scheme.

        Returns
        -------
        None
        """

        axis: Axes = self._axes[axis_index]

        axis.xaxis.label.set_color("w")
        axis.yaxis.label.set_color("w")
        axis.title.set_color("w")

        for spine in axis.spines.values():
            spine.set_edgecolor("w")

        axis.tick_params(axis="x", which="both", colors="w")
        axis.tick_params(axis="y", which="both", colors="w")

        axis.patch.set_alpha(0)

    def set_white_axis_all(self) -> None:
        """
        Sets the color scheme of all axes to white, including spines.

        This includes the axis labels, ticks, titles, and spines.

        Returns
        -------
        None
        """

        rcParams["text.color"] = "w"
        for axis_index in range(len(self._axes)):
            self.set_white_axis(axis_index)


def graph_white(axis_index: int) -> None:
    """
    Sets the color scheme of the specified axis to white.

    This includes the axis labels, ticks, and titles.

    Parameters
    ----------
    axis_index : int
        The index of the axis to set the color scheme.

    Returns
    -------
    None
    """

    GraphWhite().set_white(axis_index)


def graph_white_all() -> None:
    """
    Sets the color scheme of all axes to white.

    This includes the axis labels, ticks, and titles.

    Returns
    -------
    None
    """

    GraphWhite().set_white_all()


def graph_white_axis(axis_index: int) -> None:
    """
    Sets the color scheme of the specified axis to white, including spines.

    This includes the axis labels, ticks, titles, and spines.

    Parameters
    ----------
    axis_index : int
        The index of the axis to set the color scheme.

    Returns
    -------
    None
    """

    GraphWhite().set_white_axis(axis_index)


def graph_white_axis_all() -> None:
    """
    Sets the color scheme of all axes to white, including spines.

    This includes the axis labels, ticks, titles, and spines.

    Returns
    -------
    None
    """

    GraphWhite().set_white_axis_all()


class GraphTransparent:
    """
    A class for setting matplotlib figures and axes to be transparent.

    The `GraphTransparent` class allows for setting the background of figures and axes to be transparent,
    either for a single axis or all axes. It also updates the global `rcParams` to ensure the figure,
    axes, and saved figure backgrounds are transparent.

    Methods
    -------
    set_transparent(axis_index: int) -> None
        Sets the background of the specified axis to be transparent.
    set_transparent_all() -> None
        Sets the background of all axes to be transparent.
    """

    def __init__(self) -> None:
        self.__axes: AxesSingleton = AxesSingleton()
        self._axes: List[Axes] = self.__axes.axes

        rcParams.update(
            {
                "figure.facecolor": (1.0, 0.0, 0.0, 0),
                "axes.facecolor": (0.0, 1.0, 0.0, 0),
                "savefig.facecolor": (0.0, 0.0, 1.0, 0),
            }
        )

    def set_transparent(self, axis_index: int) -> None:
        """
        Sets the background of the specified axis to be transparent.

        Parameters
        ----------
        axis_index : int
            The index of the axis to make transparent.

        Returns
        -------
        None
        """

        axis: Axes = self._axes[axis_index]
        axis.patch.set_alpha(0)

    def set_transparent_all(self) -> None:
        """
        Sets the background of all axes to be transparent.

        Returns
        -------
        None
        """

        for axis_index in range(len(self._axes)):
            self.set_transparent(axis_index)


def graph_transparent(axis_index: int) -> None:
    """
    Sets the background of the specified axis to be transparent.

    This function uses the `GraphTransparent` class to set the background
    of a single axis to be transparent.

    Parameters
    ----------
    axis_index : int
        The index of the axis to make transparent.

    Returns
    -------
    None
    """

    GraphTransparent().set_transparent(axis_index)


def graph_transparent_all() -> None:
    """
    Sets the background of all axes to be transparent.

    This function uses the `GraphTransparent` class to set the background
    of all axes in the current figure to be transparent.

    Returns
    -------
    None
    """

    GraphTransparent().set_transparent_all()
