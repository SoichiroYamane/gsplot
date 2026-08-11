from typing import Any

import numpy as np
from matplotlib.axes import Axes
from matplotlib.legend import Legend as Lg
from matplotlib.legend_handler import HandlerBase
from matplotlib.patches import Rectangle

from ..base.base import CreateClassParams, ParamsGetter, bind_passed_params
from ..color.colormap import Colormap

__all__: list[str] = ["legend_colormap"]


class HandlerColormap(HandlerBase):
    """
    Custom legend handler for displaying a colormap.

    Parameters
    --------------------
    cmap : str
        The colormap to use.
    num_stripes : int, default=8
        Number of stripes in the colormap legend.
    vmin : int | float, default=0
        Minimum value for the colormap.
    vmax : int | float, default=1
        Maximum value for the colormap.
    reverse : bool, default=False
        Whether to reverse the colormap.
    **kwargs : Any
        Additional parameters for the `Rectangle` artists.

    Examples
    --------------------
    >>> from matplotlib.legend_handler import HandlerColormap
    >>> handler = HandlerColormap(cmap="viridis", num_stripes=10, reverse=True)
    """

    def __init__(
        self,
        cmap: str,
        num_stripes: int = 8,
        vmin: int | float = 0,
        vmax: int | float = 1,
        reverse: bool = False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.cmap: str = cmap
        self.num_stripes: int = num_stripes
        self.vmin: int | float = vmin
        self.vmax: int | float = vmax
        self.reverse: bool = reverse
        self.kwargs = kwargs

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
        Create colormap legend artists.

        Parameters
        --------------------
        legend : Legend
            The legend instance.
        orig_handle : Any
            The original handle used for the legend.
        xdescent : float
            Horizontal offset for the legend element.
        ydescent : float
            Vertical offset for the legend element.
        width : float
            Width of the legend element.
        height : float
            Height of the legend element.
        fontsize : float
            Font size for the legend text.
        trans : Transform
            Transformation applied to the artist.

        Returns
        --------------------
        list[Rectangle]
            A list of rectangles representing the colormap legend.

        Examples
        --------------------
        Used internally for creating custom colormap legend patches.
        """
        stripes = []
        cmap_ndarray = np.linspace(self.vmin, self.vmax, self.num_stripes)
        cmap_list = Colormap(
            cmap=self.cmap, cmap_data=cmap_ndarray, normalize=False, reverse=False
        ).get_split_cmap()

        for i in range(self.num_stripes):
            fc = cmap_list[self.num_stripes - i - 1] if self.reverse else cmap_list[i]
            s = Rectangle(
                (xdescent + i * width / self.num_stripes, ydescent),
                width / self.num_stripes,
                height,
                fc=fc,
                transform=trans,
                **self.kwargs,
            )
            stripes.append(s)
        return stripes


class LegendColormap:
    """
    Adds a colormap legend to a Matplotlib axis.

    Parameters
    --------------------
    ax : Axes
        The target axis for the legend.
    cmap : str, default="viridis"
        The colormap to use.
    label : str | None, default=None
        Label for the legend.
    num_stripes : int, default=8
        Number of stripes in the colormap legend.
    vmin : int | float, default=0
        Minimum value for the colormap.
    vmax : int | float, default=1
        Maximum value for the colormap.
    reverse : bool, default=False
        Whether to reverse the colormap.
    **kwargs : Any
        Additional parameters passed to the handler and artists.

    Examples
    --------------------
    >>> from matplotlib import pyplot as plt
    >>> import numpy as np
    >>> fig, ax = plt.subplots()
    >>> x = np.linspace(0, 10, 100)
    >>> y = np.sin(x)
    >>> ax.plot(x, y, label="Data")
    >>> LegendColormap(ax, cmap="plasma", label="Colormap Legend").legend_colormap()
    >>> plt.show()
    """

    def __init__(
        self,
        ax: Axes,
        cmap: str = "viridis",
        label: str | None = None,
        num_stripes: int = 8,
        vmin: int | float = 0,
        vmax: int | float = 1,
        reverse: bool = False,
        **kwargs: Any,
    ):
        self.ax: Axes = ax
        self.cmap: str = cmap
        self.label: str | None = label
        self.num_stripes: int = num_stripes
        self.vmin: int | float = vmin
        self.vmax: int | float = vmax
        self.reverse: bool = reverse
        self.kwargs: Any = kwargs

        MAX_NUM_STRIPES = 256
        if self.num_stripes > MAX_NUM_STRIPES:
            self.num_stripes = MAX_NUM_STRIPES

        self.handler_colormap = HandlerColormap(
            cmap=self.cmap,
            num_stripes=self.num_stripes,
            reverse=self.reverse,
            vmin=self.vmin,
            vmax=self.vmax,
            **self.kwargs,
        )

    def get_legend_handlers_colormap(
        self,
    ) -> tuple[list[Rectangle], list[str | None], dict[Rectangle, HandlerColormap]]:
        """
        Get legend handlers, labels, and handler mappings for colormap legend.

        Returns
        --------------------
        tuple
            - handles (list[Rectangle]): List of legend handles.
            - labels (list[str | None]): List of legend labels.
            - handlers (dict[Rectangle, HandlerColormap]): Mapping of handles to their handlers.

        Examples
        --------------------
        >>> legend_colormap = LegendColormap(0, cmap="plasma", num_stripes=8)
        >>> handles, labels, handlers = legend_colormap.get_legend_handlers_colormap()
        >>> print(handles, labels, handlers)
        """
        handle = [Rectangle((0, 0), 1, 1)]
        label: list[str | None] = [self.label]

        handler: dict[Rectangle, HandlerColormap] = {handle[0]: self.handler_colormap}
        return handle, label, handler

    @staticmethod
    def create_unique_class_with_handler(base_class, handler, class_name=None):
        """
        Create a unique class that extends a given base class and associates it with a custom handler.

        Parameters
        --------------------
        base_class : type
            The base class to extend.
        handler : HandlerBase
            The custom handler to associate with the new class.
        class_name : str, optional
            Name for the newly created class. If not provided, a unique name is generated.

        Returns
        --------------------
        type
            A new class that extends the base class and is associated with the custom handler.

        Examples
        --------------------
        >>> from matplotlib.patches import Rectangle
        >>> from matplotlib.legend_handler import HandlerBase
        >>> class CustomHandler(HandlerBase):
        ...     pass
        >>> custom_handler = CustomHandler()
        >>> NewRectangle = LegendColormap.create_unique_class_with_handler(Rectangle, custom_handler)
        >>> new_instance = NewRectangle((0, 0), 1, 1)
        >>> print(type(new_instance).__name__)
        CustomRectangle_<unique_id>
        """
        # Create Unique Class
        if class_name is None:
            class_name = f"Custom{base_class.__name__}_{id(handler)}"

        # Create a new class with the given handler
        UniqueClass = type(class_name, (base_class,), {})
        return UniqueClass

    def axis_patch(self):
        """
        Add a dummy patch to the axis to represent the colormap legend.

        Notes
        --------------------
        This method creates a dummy patch using a custom class associated with a colormap handler.
        The patch is invisible but serves as a proxy for the colormap legend entry.

        Examples
        --------------------
        >>> from matplotlib import pyplot as plt
        >>> fig, ax = plt.subplots()
        >>> legend_colormap = LegendColormap(0, cmap="viridis", label="Colormap")
        >>> legend_colormap.axis_patch()
        >>> plt.show()
        """
        UniqueClass = self.create_unique_class_with_handler(
            Rectangle, self.handler_colormap
        )
        cmap_dummy_handle = UniqueClass((0, 0), 0, 0, label=self.label, visible=False)
        self.ax.add_patch(cmap_dummy_handle)
        Lg.update_default_handler_map({cmap_dummy_handle: self.handler_colormap})
        self.ax.legend(handles=[cmap_dummy_handle], labels=[self.label])

    def legend_colormap(self) -> Lg:
        """
        Create and display a colormap legend on the target axis.

        Returns
        --------------------
        matplotlib.legend.Legend
            The created legend object.

        Notes
        --------------------
        This method builds on `axis_patch` to construct and render the legend.

        Examples
        --------------------
        >>> from matplotlib import pyplot as plt
        >>> fig, ax = plt.subplots()
        >>> legend_colormap = LegendColormap(0, cmap="viridis", label="Color Legend")
        >>> legend_colormap.legend_colormap()
        >>> plt.show()
        """
        self.axis_patch()
        return self.ax.legend()


@bind_passed_params()
def legend_colormap(
    ax: Axes,
    cmap: str = "viridis",
    label: str | None = None,
    num_stripes: int = 8,
    vmin: int | float = 0,
    vmax: int | float = 1,
    reverse: bool = False,
    **kwargs: Any,
) -> Lg:
    """
    Create and display a colormap legend on a specified axis.

    Parameters
    --------------------
    ax : Axes
        The target axis for the legend.
    cmap : str, optional
        The colormap to use for the legend (default is 'viridis').
    label : str | None, optional
        The label to display for the colormap in the legend (default is None).
    num_stripes : int, optional
        The number of stripes to divide the colormap into (default is 8).
    vmin : int | float, optional
        The minimum value of the colormap (default is 0).
    vmax : int | float, optional
        The maximum value of the colormap (default is 1).
    reverse : bool, optional
        Whether to reverse the colormap (default is False).
    **kwargs : Any
        Additional keyword arguments for configuring the legend.

    Returns
    --------------------
    matplotlib.legend.Legend
        The created legend object.

    Notes
    --------------------
    This function binds passed parameters and creates a `LegendColormap` instance
    to generate a colormap legend on the specified axis.

    Examples
    --------------------
    >>> import gsplot as gs
    >>> gs.legend_colormap(
    ...     ax=ax,
    ...     cmap="plasma",
    ...     label="Example Legend",
    ...     num_stripes=10,
    ...     vmin=0,
    ...     vmax=100,
    ...     reverse=True,
    ... )
    """

    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    class_params = CreateClassParams(passed_params).get_class_params()

    _legend_colormap = LegendColormap(
        class_params["ax"],
        class_params["cmap"],
        class_params["label"],
        class_params["num_stripes"],
        class_params["vmin"],
        class_params["vmax"],
        class_params["reverse"],
        **class_params["kwargs"],
    )

    return _legend_colormap.legend_colormap()
