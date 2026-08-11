import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.axes import Axes
from matplotlib.figure import Figure

__all__: list[str] = [
    "graph_square",
    "graph_square_axes",
    "graph_white",
    "graph_white_axes",
    "graph_transparent",
    "graph_transparent_axes",
    "graph_facecolor",
]


class GraphSquare:
    """
    A class to set Matplotlib axes to have a square aspect ratio.

    This class provides methods to adjust the aspect ratio of a single axis
    or all axes in the current figure to make them square.

    Attributes
    --------------------
    _axes : list[matplotlib.axes.Axes]
        List of all axes in the current figure.

    Methods
    --------------------
    set_square(ax: matplotlib.axes.Axes) -> None
        Sets the aspect ratio of the specified axis to square.
    set_square_axes() -> None
        Sets the aspect ratio of all axes in the current figure to square.

    Examples
    --------------------
    >>> gs = GraphSquare()
    >>> gs.set_square(ax)  # Set the first axis to square aspect ratio
    >>> gs.set_square_axes()  # Set all axes to square aspect ratio
    """

    def __init__(self) -> None:
        self._axes: list[Axes] = plt.gcf().axes

    def set_square(self, ax: Axes) -> None:
        """
        Sets the aspect ratio of the specified axis to square.

        Parameters
        --------------------
        ax : matplotlib.axes.Axes
            The target axis to adjust.

        Returns
        --------------------
        None

        Notes
        --------------------
        - Uses the `AxesResolver` to resolve the target axis.
        - Sets the aspect ratio of the specified axis using `set_box_aspect`.

        Examples
        --------------------
        >>> gs = GraphSquare()
        >>> gs.set_square(axs[0])  # Set the first axis to square aspect ratio
        """

        ax.set_box_aspect(1)

    def set_square_axes(self) -> None:
        """
        Sets the aspect ratio of all axes in the current figure to square.

        This method iterates through all axes in the current figure and sets their
        aspect ratio to square.

        Returns
        --------------------
        None

        Examples
        --------------------
        >>> gs = GraphSquare()
        >>> gs.set_square_axes()  # Set all axes to square aspect ratio
        """
        for axis in self._axes:
            axis.set_box_aspect(1)


def graph_square(ax: Axes) -> None:
    """
    Sets the aspect ratio of a specified axis to square.

    This function is a wrapper for the `set_square` method of the `GraphSquare` class.

    Parameters
    --------------------
    ax : matplotlib.axes.Axes
        The target axis to adjust.

    Returns
    --------------------
    None

    Examples
    --------------------
    >>> import gsplot as gs
    >>> gs.graph_square(axs[0])  # Set the first axis to square aspect ratio
    """
    GraphSquare().set_square(ax)


def graph_square_axes() -> None:
    """
    Sets the aspect ratio of all axes in the current figure to square.

    This function is a wrapper for the `set_square_axes` method of the `GraphSquare` class.

    Returns
    --------------------
    None

    Examples
    --------------------
    >>> import gsplot as gs
    >>> gs.graph_square_axes()  # Set all axes to square aspect ratio
    """
    GraphSquare().set_square_axes()


class GraphWhite:
    """
    A class to apply a white color scheme to Matplotlib axes.

    This class provides methods to set the text, spines, and ticks of a single
    axis or all axes in the current figure to white, making them suitable for
    dark-themed backgrounds.

    Attributes
    --------------------
    _axes : list[matplotlib.axes.Axes]
        List of all axes in the current figure.

    Methods
    --------------------
    set_white(axt: matplotlib.axes.Axes) -> None
        Sets the text, spines, and ticks of the specified axis to white.
    set_white_axes() -> None
        Applies the white color scheme to all axes in the current figure.

    Examples
    --------------------
    >>> gw = GraphWhite()
    >>> gw.set_white(axs[0])  # Apply white color scheme to the first axis
    >>> gw.set_white_axes()  # Apply white color scheme to all axes
    """

    def __init__(self) -> None:
        self._axes: list[Axes] = plt.gcf().axes

    def set_white(self, ax: Axes) -> None:
        """
        Sets the text, spines, and ticks of the specified axis to white.

        This method modifies the color of axis labels, title, spines, and ticks to white
        and makes the axis background transparent.

        Parameters
        --------------------
        ax : matplotlib.axes.Axes
            The target axis to modify.

        Returns
        --------------------
        None

        Notes
        --------------------
        - Uses the `AxesResolver` to resolve the target axis.
        - Sets transparency for the axis background by adjusting the patch alpha value.

        Examples
        --------------------
        >>> gw = GraphWhite()
        >>> gw.set_white(axs[0])  # Apply white color scheme to the first axis
        """

        ax.xaxis.label.set_color("w")
        ax.yaxis.label.set_color("w")
        ax.title.set_color("w")

        for spine in ax.spines.values():
            spine.set_edgecolor("w")

        ax.tick_params(axis="x", which="both", colors="w")
        ax.tick_params(axis="y", which="both", colors="w")

        ax.patch.set_alpha(0)

    def set_white_axes(self) -> None:
        """
        Applies the white color scheme to all axes in the current figure.

        This method iterates through all axes in the current figure and modifies
        their text, spines, and ticks to white, while also updating global text
        color settings.

        Returns
        --------------------
        None

        Notes
        --------------------
        - Updates the `rcParams` to set the default text color to white.

        Examples
        --------------------
        >>> gw = GraphWhite()
        >>> gw.set_white_axes()  # Apply white color scheme to all axes
        """

        rcParams["text.color"] = "w"
        for ax in self._axes:
            self.set_white(ax)


def graph_white(ax: Axes) -> None:
    """
    Applies the white color scheme to a specified axis.

    This function is a wrapper for the `set_white` method of the `GraphWhite` class.

    Parameters
    --------------------
    axis_target : int or matplotlib.axes.Axes
        The target axis to modify. Can be an axis index or a Matplotlib `Axes` object.

    Returns
    --------------------
    None

    Examples
    --------------------
    >>> import gsplot as gs
    >>> gs.graph_white(axs[0])  # Apply white color scheme to the first axis
    """
    GraphWhite().set_white(ax)


def graph_white_axes() -> None:
    """
    Applies the white color scheme to all axes in the current figure.

    This function is a wrapper for the `set_white_axes` method of the `GraphWhite` class.

    Returns
    --------------------
    None

    Examples
    --------------------
    >>> import gsplot as gs
    >>> gs.graph_white_axes()  # Apply white color scheme to all axes
    """
    GraphWhite().set_white_axes()


class GraphTransparent:
    """
    A class to apply transparency to Matplotlib figures and axes.

    This class provides methods to set individual axes or all axes in the current
    figure to be transparent. It also updates Matplotlib's `rcParams` for figure,
    axes, and saved figure face colors to be transparent.

    Attributes
    --------------------
    _axes : list[matplotlib.axes.Axes]
        List of all axes in the current figure.

    Methods
    --------------------
    set_transparent(ax: matplotlib.axes.Axes) -> None
        Sets a specified axis to be transparent.
    set_transparent_axes() -> None
        Sets all axes in the current figure to be transparent.

    Examples
    --------------------
    >>> gt = GraphTransparent()
    >>> gt.set_transparent(axs[0])  # Set the first axis to be transparent
    >>> gt.set_transparent_axes()  # Set all axes to be transparent
    """

    def __init__(self) -> None:
        self._axes: list[Axes] = plt.gcf().axes

        rcParams.update(
            {
                "figure.facecolor": (1.0, 0.0, 0.0, 0),
                "axes.facecolor": (0.0, 1.0, 0.0, 0),
                "savefig.facecolor": (0.0, 0.0, 1.0, 0),
            }
        )

    def set_transparent(self, ax: Axes) -> None:
        """
        Sets a specified axis to be transparent.

        Parameters
        --------------------
        ax : matplotlib.axes.Axes
            The target axis to modify.

        Returns
        --------------------
        None

        Notes
        --------------------
        - Uses `AxesResolver` to resolve the target axis.
        - Modifies the `patch` attribute of the axis to make it transparent.

        Examples
        --------------------
        >>> gt = GraphTransparent()
        >>> gt.set_transparent(axs[0])  # Make the first axis transparent
        """

        ax.patch.set_alpha(0)

    def set_transparent_axes(self) -> None:
        """
        Sets all axes in the current figure to be transparent.

        This method iterates through all axes in the current figure and makes them
        transparent.

        Returns
        --------------------
        None

        Examples
        --------------------
        >>> gt = GraphTransparent()
        >>> gt.set_transparent_axes()  # Make all axes transparent
        """
        for ax in self._axes:
            self.set_transparent(ax)


def graph_transparent(ax: Axes) -> None:
    """
    Sets a specified axis to be transparent.

    This function is a wrapper for the `set_transparent` method of the `GraphTransparent` class.

    Parameters
    --------------------
    ax : matplotlib.axes.Axes
        The target axis to modify.

    Returns
    --------------------
    None

    Examples
    --------------------
    >>> import gsplot as gs
    >>> gs.graph_transparent(axs[0])  # Make the first axis transparent
    """
    GraphTransparent().set_transparent(ax)


def graph_transparent_axes() -> None:
    """
    Sets all axes in the current figure to be transparent.

    This function is a wrapper for the `set_transparent_axes` method of the `GraphTransparent` class.

    Returns
    --------------------
    None

    Examples
    --------------------
    >>> import gsplot as gs
    >>> gs.graph_transparent_axes()  # Make all axes transparent
    """
    GraphTransparent().set_transparent_axes()


class GraphFaceColor:
    """
    A class to modify the face color of a Matplotlib figure.

    This class provides a method to set the face color of the current figure.

    Attributes
    --------------------
    fig : matplotlib.figure.Figure
        The current figure object.

    Methods
    --------------------
    set_facecolor(color: str = "black") -> None
        Sets the face color of the current figure.

    Examples
    --------------------
    >>> gfc = GraphFaceColor()
    >>> gfc.set_facecolor("blue")  # Set the face color of the figure to blue
    """

    def __init__(self) -> None:
        self.fig: Figure = plt.gcf()

    def set_facecolor(self, color: str = "black") -> None:
        """
        Sets the face color of the current figure.

        Parameters
        --------------------
        color : str, optional
            The desired face color, specified as a color string (default is "black").

        Returns
        --------------------
        None

        Examples
        --------------------
        >>> gfc = GraphFaceColor()
        >>> gfc.set_facecolor("white")  # Set the face color of the figure to white
        """
        self.fig.patch.set_facecolor(color)


def graph_facecolor(color: str = "black") -> None:
    """
    Sets the face color of the current figure.

    This function is a wrapper for the `set_facecolor` method of the `GraphFaceColor` class.

    Parameters
    --------------------
    color : str, optional
        The desired face color, specified as a color string (default is "black").

    Returns
    --------------------
    None

    Examples
    --------------------
    >>> import gsplot as gs
    >>> gs.graph_facecolor("black")  # Set the face color of the figure to black
    """
    GraphFaceColor().set_facecolor(color)
