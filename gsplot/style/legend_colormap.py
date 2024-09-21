from ..figure.axes import AxesSingleton
from ..color.colormap import Colormap
from .legend import Legend
from typing import Any, Dict, List, Tuple


from matplotlib.patches import Rectangle
from matplotlib.artist import Artist
from matplotlib.legend_handler import HandlerBase
import numpy as np


class HandlerColormap(HandlerBase):
    """
    A custom legend handler to display a colormap with stripes in the legend.

    This handler creates a series of rectangles (stripes) representing different
    segments of a colormap, which can be added to a legend in a plot.

    Parameters
    ----------
    cmap : str
        The colormap to use.
    num_stripes : int, optional
        The number of stripes to display in the legend, by default 8.
    vmin : float or int, optional
        The minimum value for the colormap range, by default 0.
    vmax : float or int, optional
        The maximum value for the colormap range, by default 1.
    reverse : bool, optional
        Whether to reverse the order of the colormap stripes, by default False.
    **kwargs
        Additional keyword arguments passed to the HandlerBase initializer.
    """

    def __init__(
        self,
        cmap: str,
        num_stripes: int = 8,
        vmin: float | int = 0,
        vmax: float | int = 1,
        reverse: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.cmap: str = cmap
        self.num_stripes: int = num_stripes
        self.vmin: float | int = vmin
        self.vmax: float | int = vmax
        self.reverse: bool = reverse

    def create_artists(
        self,
        legend,
        orig_handle,
        xdescent,
        ydescent,
        width,
        height,
        fontsize,
        trans,
    ):
        """
        Create a list of artists (rectangles) to represent the colormap in the legend.

        This method generates a series of rectangles (stripes) with colors from the specified
        colormap. The rectangles are arranged horizontally within the legend.

        Parameters
        ----------
        legend : Legend
            The legend object that will display the colormap.
        orig_handle : Any
            The original handle being represented by this handler.
        xdescent : float
            The amount of space reserved on the left side of the legend.
        ydescent : float
            The amount of space reserved on the bottom side of the legend.
        width : float
            The width of the legend entry.
        height : float
            The height of the legend entry.
        fontsize : float
            The font size used in the legend.
        trans : Transform
            The transformation applied to the artists.

        Returns
        -------
        list[Rectangle]
            A list of Rectangle artists representing the colormap stripes.
        """

        stripes = []
        cmap_ndarray = np.linspace(self.vmin, self.vmax, self.num_stripes)
        cmap_list = Colormap(
            cmap=self.cmap, ndarray=cmap_ndarray, normalize=False
        ).get_split_cmap()

        for i in range(self.num_stripes):
            fc = cmap_list[self.num_stripes - i - 1] if self.reverse else cmap_list[i]
            s = Rectangle(
                (xdescent + i * width / self.num_stripes, ydescent),
                width / self.num_stripes,
                height,
                fc=fc,
                transform=trans,
            )
            stripes.append(s)
        return stripes


class LegendColormap:
    """
    A class to add a colormap legend to a specified axis in a matplotlib figure.

    This class generates a custom colormap legend entry with a specified number of
    stripes representing the colormap. The entry can be added to a legend in the plot.

    Parameters
    ----------
    axis_index : int
        Index of the axis to apply the colormap legend to.
    cmap : str, optional
        The colormap to use, by default "viridis".
    label : str, optional
        The label for the colormap in the legend, by default None.
    num_stripes : int, optional
        The number of stripes to display in the colormap legend, by default 8.
    vmin : int or float, optional
        The minimum value for the colormap range, by default 0.
    vmax : int or float, optional
        The maximum value for the colormap range, by default 1.
    reverse : bool, optional
        Whether to reverse the order of the colormap stripes, by default False.
    *args : Any
        Additional positional arguments for matplotlib legend.
    **kwargs : Any
        Additional keyword arguments for matplotlib legend.
    """

    def __init__(
        self,
        axis_index: int,
        cmap: str = "viridis",
        label: str | None = None,
        num_stripes: int = 8,
        vmin: int | float = 0,
        vmax: int | float = 1,
        reverse: bool = False,
        *args: Any,
        **kwargs: Any,
    ):
        self.axis_index: int = axis_index
        self.cmap: str = cmap
        self.label: str | None = label
        self.num_stripes: int = num_stripes
        self.vmin = vmin
        self.vmax = vmax
        self.reverse = reverse

        self.__axes = AxesSingleton()
        self._axis = self.__axes.axes[self.axis_index]

        self._args = args
        self._kwargs = kwargs

    def get_legend_handlers_colormap(
        self,
    ) -> tuple[list[Rectangle], list[str | None], dict[Rectangle, HandlerColormap]]:
        """
        Retrieve the handles, labels, and handler map for the colormap legend.

        Returns
        -------
        tuple[list[Rectangle], list[str | None], dict[Rectangle, HandlerColormap]]
            Handles, labels, and handler map for the colormap legend.
        """

        handle = [Rectangle((0, 0), 1, 1)]
        label: list[str | None] = [self.label]
        _handler = HandlerColormap(
            cmap=self.cmap,
            num_stripes=self.num_stripes,
            reverse=self.reverse,
            vmin=self.vmin,
            vmax=self.vmax,
        )
        handler: dict[Rectangle, HandlerColormap] = {handle[0]: _handler}
        return handle, label, handler

    def add_legend_colormap(self):
        """
        Add the colormap legend to the specified axis.

        This method retrieves the existing legend handles and labels, appends the
        colormap entry, and updates the legend with the new entry.

        Returns
        -------
        None
        """

        handles, labels, handlers = Legend(self.axis_index).get_legend_handlers()
        handle_cmap, label_cmap, handler_cmap = self.get_legend_handlers_colormap()

        # handles += handle_cmap
        # labels += label_cmap
        # handlers |= handler_cmap

        # Filter None values from label_cmap to match the expected types
        label_cmap_filtered = [lbl for lbl in label_cmap if lbl is not None]

        # Append handle_cmap and label_cmap_filtered to the existing lists
        handles += handle_cmap
        labels += label_cmap_filtered

        # Ensure handlers and handler_cmap have compatible types
        handler_cmap_casted: dict[Artist, HandlerBase] = {
            k: v for k, v in handler_cmap.items()
        }
        handlers.update(handler_cmap_casted)

        Legend(
            self.axis_index,
            handles,
            labels,
            handlers,
            *self._args,
            **self._kwargs,
        ).legend_handlers()


def legend_colormap(
    axis_index: int,
    cmap: str = "viridis",
    label: str | None = None,
    num_stripes: int = 8,
    vmin: int | float = 0,
    vmax: int | float = 1,
    reverse: bool = False,
    *args: Any,
    **kwargs: Any,
) -> None:
    """
    Add a colormap entry to the legend on the specified axis.

    Parameters
    ----------
    axis_index : int
        Index of the axis to apply the colormap legend to.
    cmap : str, optional
        The colormap to use, by default "viridis".
    label : str, optional
        The label for the colormap in the legend, by default None.
    num_stripes : int, optional
        The number of stripes to display in the colormap legend, by default 8.
    vmin : int or float, optional
        The minimum value for the colormap range, by default 0.
    vmax : int or float, optional
        The maximum value for the colormap range, by default 1.
    reverse : bool, optional
        Whether to reverse the order of the colormap stripes, by default False.
    *args : Any
        Additional positional arguments for matplotlib legend.
    **kwargs : Any
        Additional keyword arguments for matplotlib legend.

    Returns
    -------
    None
    """

    LegendColormap(
        axis_index,
        cmap,
        label,
        num_stripes,
        vmin,
        vmax,
        reverse,
        *args,
        **kwargs,
    ).add_legend_colormap()
