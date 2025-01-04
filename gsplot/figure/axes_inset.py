from typing import Any, cast

from matplotlib.axes import Axes
from matplotlib.transforms import BboxBase, Transform, TransformedBbox
from matplotlib.typing import ColorType
from mpl_toolkits.axes_grid1.inset_locator import (BboxConnector, BboxPatch,
                                                   inset_axes)

from ..base.base import CreateClassParams, ParamsGetter, bind_passed_params
from ..style.label import Label
from ..style.ticks import MinorTicks

__all__ = ["axes_inset", "axes_inset_padding"]


class InsetAxesBase:
    """
    A utility class for managing inset axes in a Matplotlib figure.

    This class provides functionality for configuring and customizing inset axes,
    including zooming, labeling, and enabling minor ticks. It also allows for manual
    control of zoom connectors and axis limits.

    Parameters
    --------------------
    ax : Axes
        The main axis in the figure.
    axins : Axes
        The inset axis in the figure.
    lab_lims : list[Any] | None, optional
        List specifying axis labels and limits for the inset axis.
        Expected format: [x_label, y_label, x_lim_min, x_lim_max, y_lim_min, y_lim_max].
    minor_ticks : bool, default=True
        Whether to enable minor ticks on the inset axis.
    zoom : bool or tuple[tuple[int, int], tuple[int, int]], default=True
        Zoom settings for the inset axis.
        - If True, uses the built-in zoom indication.
        - If a tuple, manually connects the axes with zoom connectors.
    zoom_color : ColorType, default='black'
        Color for the zoom connectors and patches.
    zoom_alpha : int | float, default=0.3
        Transparency for the zoom connectors and patches.
    **kwargs : Any
        Additional keyword arguments for axis label configuration.

    Notes
    --------------------
    This class is designed for cases where inset axes are needed for enhanced
    visualization. It uses helper classes like `Label` and `MinorTicks` to
    streamline customization.

    Methods
    --------------------
    manual_inset_zoom():
        Manually connect the main axis to the inset axis with zoom connectors.

    indicate_inset_zoom():
        Use the built-in Matplotlib method to indicate zoom on the inset axis.

    inset_zoom():
        Automatically apply zoom connectors based on the `zoom` attribute.

    set_minor_ticks():
        Enable minor ticks on the inset axis.

    label():
        Configure and set labels and axis limits for the inset axis.

    Warnings
    --------------------
    - Ensure that `lab_lims` is provided and correctly formatted when calling `label()`.
    - `zoom` should be a tuple of tuples when using `manual_inset_zoom()`.

    Examples
    --------------------
    >>> import matplotlib.pyplot as plt
    >>> fig, ax = plt.subplots()
    >>> axins = ax.inset_axes([0.5, 0.5, 0.4, 0.4])
    >>> inset = InsetAxesBase(
    ...     ax,
    ...     axins,
    ...     lab_lims=["X Label", "Y Label", 0, 1, 0, 1],
    ...     zoom=((1, 2), (3, 4)),
    ... )
    >>> inset.set_minor_ticks()
    >>> inset.label()
    >>> inset.inset_zoom()
    >>> plt.show()
    """

    def __init__(
        self,
        ax,
        axins,
        lab_lims: list[Any] | None = None,
        minor_ticks: bool = True,
        zoom: bool | tuple[tuple[int, int], tuple[int, int]] = True,
        zoom_color: ColorType = "black",
        zoom_alpha: int | float = 0.3,
        **kwargs,
    ) -> None:
        self.ax: Axes = ax
        self.axins: Axes = axins
        self.lab_lims: list[Any] | None = lab_lims
        self.minor_ticks: bool = minor_ticks
        self.zoom: bool | tuple[tuple[int, int], tuple[int, int]] = zoom
        self.zoom_color: ColorType = zoom_color
        self.zoom_alpha: int | float = zoom_alpha
        self.kwargs: Any = kwargs

    def manual_inset_zoom(self):
        """
        Manually connect the main axis to the inset axis with zoom connectors.

        This method adds connectors and a patch between the main and inset axes
        to visually represent the zoomed-in region.

        Raises:
            ValueError: If `zoom` is not a tuple of tuples.

        Notes
        --------------------
        This method is used when manual control over zoom connectors is required.
        """
        if isinstance(self.zoom, bool):
            raise ValueError("locs_zoom must be a tuple of tuples")

        loc1a, loc1b = self.zoom[0]
        loc2a, loc2b = self.zoom[1]
        rect = TransformedBbox(self.axins.viewLim, self.ax.transData)
        pp = BboxPatch(
            rect, fill=False, edgecolor=self.zoom_color, alpha=self.zoom_alpha
        )
        self.ax.add_patch(pp)
        p1 = BboxConnector(
            self.axins.bbox,
            rect,
            loc1=loc1b,
            loc2=loc1a,
            color=self.zoom_color,
            alpha=self.zoom_alpha,
        )
        self.axins.add_patch(p1)
        p1.set_clip_on(False)
        p2 = BboxConnector(
            self.axins.bbox,
            rect,
            loc1=loc2b,
            loc2=loc2a,
            color=self.zoom_color,
            alpha=self.zoom_alpha,
        )
        self.axins.add_patch(p2)
        p2.set_clip_on(False)

    def indicate_inset_zoom(self):
        """
        Use Matplotlib's built-in method to indicate zoom on the inset axis.

        This method creates a zoom indication using a rectangular outline between
        the main and inset axes.

        Notes
        --------------------
        This method is simpler and faster than `manual_inset_zoom` but offers
        less customization.
        """
        self.ax.indicate_inset_zoom(
            self.axins, edgecolor=self.zoom_color, alpha=self.zoom_alpha
        )

    def inset_zoom(self):
        """
        Apply zoom connectors to the inset axis based on the `zoom` attribute.

        If `zoom` is True, the built-in zoom indication method is used.
        If `zoom` is a tuple, manual zoom connectors are created using `manual_inset_zoom`.

        Notes
        --------------------
        This method provides a unified interface for adding zoom connectors.
        """
        if self.zoom is True:
            self.indicate_inset_zoom()
        elif isinstance(self.zoom, tuple):
            self.manual_inset_zoom()

    def set_minor_ticks(self):
        """
        Enable minor ticks on the inset axis.

        This method configures and displays minor ticks on both x and y axes
        of the inset axis.

        Notes
        --------------------
        Minor ticks enhance the readability of the inset axis.
        """
        _minor_ticks = MinorTicks(self.axins)
        _minor_ticks.set_minor_ticks_on(mode="xy")

    def label(
        self,
    ):
        """
        Configure labels and axis limits for the inset axis.

        This method sets the x and y axis labels and applies the specified
        axis limits to the inset axis.

        Raises:
            ValueError: If `lab_lims` is not provided or has an invalid shape.

        Notes
        --------------------
        This method utilizes the `Label` class to simplify axis labeling and limit configuration.

        Examples
        --------------------
        >>> inset = InsetAxesBase(ax, axins, lab_lims=["X", "Y", 0, 1, 0, 1])
        >>> inset.label()
        """
        if not self.lab_lims:
            raise ValueError("lab_lims must be provided")

        _label = Label(
            self.lab_lims,
            minor_ticks_axes=False,
            tight_layout=False,
            **self.kwargs,
        )

        try:
            x_lab, y_lab, *lims = self.lab_lims
        except ValueError:
            raise ValueError("lab_lims has invalid shape")

        # Label the inset axes
        _label.configure_axis_labels(self.axins, x_lab, y_lab, **self.kwargs)
        # Set the axis limits
        _label.configure_axis_limits(self.axins, lims)


class AxesInset:
    """
    A class to create and manage inset axes in a Matplotlib figure.

    This class simplifies the creation of inset axes, providing options for zooming,
    labeling, minor ticks, and custom axis transformations.

    Parameters
    --------------------
    ax : Axes
        The main axis in the figure.
    bounds : tuple[float, float, float, float]
        Bounds for the inset axis in the format (x0, y0, width, height).
    transform : Transform | None, optional
        The transform to apply to the inset axis. Default is None.
    projection : str | None, optional
        The projection type for the inset axis. Default is None.
    polar : bool, default=False
        If True, the inset axis will use a polar projection.
    lab_lims : list[Any] | None, optional
        List specifying axis labels and limits for the inset axis.
        Expected format: [x_label, y_label, x_lim_min, x_lim_max, y_lim_min, y_lim_max].
    minor_ticks : bool, default=True
        Whether to enable minor ticks on the inset axis.
    zoom : bool or tuple[tuple[int, int], tuple[int, int]], default=True
        Zoom settings for the inset axis.
        - If True, uses the built-in zoom indication.
        - If a tuple, manually connects the axes with zoom connectors.
    zoom_color : ColorType, default='black'
        Color for the zoom connectors and patches.
    zoom_alpha : int | float, default=0.3
        Transparency for the zoom connectors and patches.
    zorder : int | float, default=5
        The z-order of the inset axis.
    **kwargs : Any
        Additional keyword arguments for label configuration or other customizations.

    Methods
    --------------------
    axes_inset() -> Axes:
        Creates and configures the inset axis, applying zoom, labels, and minor ticks.

    Examples
    --------------------
    >>> import matplotlib.pyplot as plt
    >>> fig, ax = plt.subplots()
    >>> bounds = [0.5, 0.5, 0.4, 0.4]
    >>> axins = AxesInset(ax, bounds, lab_lims=["X", "Y", 0, 1, 0, 1]).axes_inset()
    >>> plt.show()
    """

    def __init__(
        self,
        ax: Axes,
        bounds: tuple[float, float, float, float],
        transform: Transform | None = None,
        projection: str | None = None,
        polar: bool = False,
        lab_lims: list[Any] | None = None,
        minor_ticks: bool = True,
        zoom: bool | tuple[tuple[int, int], tuple[int, int]] = True,
        zoom_color: ColorType = "black",
        zoom_alpha: int | float = 0.3,
        zorder: int | float = 5,
        **kwargs: Any,
    ) -> None:
        self.ax: Axes = ax
        self.bounds: tuple[float, float, float, float] = bounds
        self.transform: Transform | None = transform
        self.projection: str | None = projection
        self.polar: bool = polar

        self.lab_lims: list[Any] | None = lab_lims
        self.minor_ticks: bool = minor_ticks
        self.zoom: bool | tuple[tuple[int, int], tuple[int, int]] = zoom
        self.zoom_color: ColorType = zoom_color
        self.zoom_alpha: int | float = zoom_alpha
        self.zorder: int | float = zorder
        self.kwargs: Any = kwargs

    def axes_inset(self) -> Axes:
        """
        Create and configure the inset axis.

        This method creates an inset axis using the specified bounds and properties,
        applies zoom connectors if specified, adds axis labels and limits, and enables
        minor ticks.

        Returns
        --------------------
        axins : Axes
            The created inset axis.

        Notes
        --------------------
        - If `lab_lims` is provided, the inset axis will be labeled and have custom limits.
        - If `zoom` is specified, zoom connectors will be added between the main and inset axes.

        Examples
        --------------------
        >>> axins = AxesInset(ax, bounds).axes_inset()
        >>> axins.plot([0, 1], [0, 1])
        """
        axins = self.ax.inset_axes(
            bounds=self.bounds,
            transform=self.transform,
            projection=self.projection,
            polar=self.polar,
            zorder=self.zorder,
        )
        self._axes_inset_base = InsetAxesBase(
            ax=self.ax,
            axins=axins,
            minor_ticks=self.minor_ticks,
            zoom=self.zoom,
            zoom_color=self.zoom_color,
            zoom_alpha=self.zoom_alpha,
            lab_lims=self.lab_lims,
            **self.kwargs,
        )

        if self.lab_lims:
            self._axes_inset_base.label()
        if self.zoom:
            self._axes_inset_base.inset_zoom()
        self._axes_inset_base.set_minor_ticks()
        return axins


@bind_passed_params()
def axes_inset(
    ax: Axes,
    bounds: tuple[float, float, float, float],
    transform: Transform | None = None,
    projection: str | None = None,
    polar: bool = False,
    lab_lims: list[Any] | None = None,
    minor_ticks: bool = True,
    zoom: bool | tuple[tuple[int, int], tuple[int, int]] = True,
    zoom_color: ColorType = "black",
    zoom_alpha: int | float = 0.3,
    zorder: int | float = 5,
    **kwargs: Any,
) -> Axes:
    """
    A functional interface to create an inset axis in a Matplotlib figure.

    This function wraps the `AxesInset` class, allowing inset axes to be created
    with a simpler function-based interface.

    Parameters
    --------------------
    ax : Axes
        The main axis in the figure.
    bounds : tuple[float, float, float, float]
        Bounds for the inset axis in the format (x0, y0, width, height).
    transform : Transform | None, optional
        The transform to apply to the inset axis. Default is None.
    projection : str | None, optional
        The projection type for the inset axis. Default is None.
    polar : bool, default=False
        If True, the inset axis will use a polar projection.
    lab_lims : list[Any] | None, optional
        Axis labels and limits for the inset axis.
    minor_ticks : bool, default=True
        Whether to enable minor ticks on the inset axis.
    zoom : bool or tuple[tuple[int, int], tuple[int, int]], default=True
        Zoom settings for the inset axis.
    zoom_color : ColorType, default='black'
        Color for the zoom connectors and patches.
    zoom_alpha : int | float, default=0.3
        Transparency for the zoom connectors and patches.
    zorder : int | float, default=5
        The z-order of the inset axis.
    **kwargs : Any
        Additional keyword arguments for label configuration or other customizations.

    Returns
    --------------------
    axins : Axes
        The created inset axis.

    Notes
    --------------------
    zoom provides manual inset zooming when a tuple is provided.
    zoom = ((1, 2), (3, 4)) will connect the main axis to the inset axis as follows:

    - 1 (main) - 2 (inset)
    - 3 (main) - 3 (inset)

    The indices represent the corners of the axes, with 1 being the bottom left corner

    Examples
    --------------------
    >>> import matplotlib.pyplot as plt
    >>> fig, ax = plt.subplots()
    >>> axins = axes_inset(ax, [0.5, 0.5, 0.4, 0.4], lab_lims=["X", "Y", 0, 1, 0, 1])
    >>> axins.plot([0, 1], [0, 1])
    """

    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    class_params = CreateClassParams(passed_params).get_class_params()

    _axes_inset = AxesInset(
        class_params["ax"],
        class_params["bounds"],
        class_params["transform"],
        class_params["projection"],
        class_params["polar"],
        class_params["lab_lims"],
        class_params["minor_ticks"],
        class_params["zoom"],
        class_params["zoom_color"],
        class_params["zoom_alpha"],
        class_params["zorder"],
        **class_params["kwargs"],
    )
    axins = _axes_inset.axes_inset()
    return axins


class AxesInsetPadding:
    """
    A class to create and manage inset axes with padding in a Matplotlib figure.

    This class facilitates the creation of inset axes with precise control over
    size, location, and additional padding. It also supports zooming, labeling,
    and minor tick customization.

    Parameters
    --------------------
    ax : Axes
        The parent axis where the inset axis will be placed.
    width : str or float
        The width of the inset axis. Can be a float (absolute size) or a string
        (e.g., "30%" relative to the parent axis).
    height : str or float
        The height of the inset axis. Can be a float (absolute size) or a string
        (e.g., "30%" relative to the parent axis).
    loc : str, default="upper right"
        The location of the inset axis relative to the parent axis. Accepted values are:
        "upper right", "upper left", "lower left", "lower right", etc.
    borderpad : float, default=0.5
        Padding between the parent axis and the inset axis.
    bbox_to_anchor : tuple[float, float] | BboxBase | None, optional
        The bounding box to anchor the inset axis.
    bbox_transform : Transform | None, optional
        Transformation for the bounding box anchor.
    axes_kwargs : dict[str, Any] | None, optional
        Additional keyword arguments to pass to the inset axis creation.
    lab_lims : list[Any] | None, optional
        Axis labels and limits for the inset axis.
        Expected format: [x_label, y_label, x_lim_min, x_lim_max, y_lim_min, y_lim_max].
    minor_ticks : bool, default=True
        Whether to enable minor ticks on the inset axis.
    zoom : bool or tuple[tuple[int, int], tuple[int, int]], default=True
        Zoom settings for the inset axis.
        - If True, uses the built-in zoom indication.
        - If a tuple, manually connects the axes with zoom connectors.
    zoom_color : ColorType, default="black"
        Color for the zoom connectors and patches.
    zoom_alpha : int | float, default=0.3
        Transparency for the zoom connectors and patches.
    **kwargs : Any
        Additional keyword arguments for label configuration or other customizations.

    Methods
    --------------------
    axes_inset() -> Axes:
        Creates and configures the inset axis with the specified parameters.

    Examples
    --------------------
    >>> import matplotlib.pyplot as plt
    >>> from mpl_toolkits.axes_grid1.inset_locator import inset_axes
    >>> fig, ax = plt.subplots()
    >>> axins = AxesInsetPadding(ax, width="30%", height="30%", loc="upper right").axes_inset()
    >>> axins.plot([0, 1], [0, 1])
    >>> plt.show()
    """

    def __init__(
        self,
        ax: Axes,
        width: str | float,
        height: str | float,
        loc: str = "upper right",
        borderpad: float = 0.5,
        bbox_to_anchor: tuple[float, float] | BboxBase | None = None,
        bbox_transform: Transform | None = None,
        axes_kwargs: dict[str, Any] | None = None,
        lab_lims: list[Any] | None = None,
        minor_ticks: bool = True,
        zoom: bool | tuple[tuple[int, int], tuple[int, int]] = True,
        zoom_color: ColorType = "black",
        zoom_alpha: int | float = 0.3,
        **kwargs: Any,
    ) -> None:
        self.ax: Axes = ax
        self.width: str | float = width
        self.height: str | float = height
        self.loc: str = loc
        self.borderpad: float = borderpad
        self.bbox_to_anchor: tuple[float, float] | BboxBase | None = bbox_to_anchor
        self.bbox_transform: Transform | None = bbox_transform
        self.axes_kwargs: dict[str, Any] | None = axes_kwargs

        self.lab_lims: list[Any] | None = lab_lims
        self.minor_ticks: bool = minor_ticks
        self.zoom: bool | tuple[tuple[int, int], tuple[int, int]] = zoom
        self.zoom_color: ColorType = zoom_color
        self.zoom_alpha: int | float = zoom_alpha
        self.kwargs: Any = kwargs

    def axes_inset(self) -> Axes:
        """
        Create and configure an inset axis with padding.

        This method uses `inset_axes` to create an inset axis with the specified
        width, height, and padding. It applies zoom connectors, labels, and minor
        ticks if specified.

        Returns
        --------------------
        axins : Axes
            The created inset axis.

        Notes
        --------------------
        - If `lab_lims` is provided, the inset axis will be labeled and have custom limits.
        - If `zoom` is specified, zoom connectors will be added between the main and inset axes.

        Examples
        --------------------
        >>> axins = AxesInsetPadding(ax, "30%", "30%", loc="upper right").axes_inset()
        >>> axins.plot([0, 1], [0, 1])
        """
        axins = inset_axes(
            parent_axes=self.ax,
            width=self.width,
            height=self.height,
            loc=self.loc,
            borderpad=self.borderpad,
            bbox_to_anchor=self.bbox_to_anchor,
            bbox_transform=self.bbox_transform,
            axes_kwargs=self.axes_kwargs,
        )
        self._axes_inset_base = InsetAxesBase(
            ax=self.ax,
            axins=axins,
            minor_ticks=self.minor_ticks,
            zoom=self.zoom,
            zoom_color=self.zoom_color,
            zoom_alpha=self.zoom_alpha,
            lab_lims=self.lab_lims,
            **self.kwargs,
        )

        if self.lab_lims:
            self._axes_inset_base.label()
        if self.zoom:
            self._axes_inset_base.inset_zoom()
        self._axes_inset_base.set_minor_ticks()
        return cast(Axes, axins)


@bind_passed_params()
def axes_inset_padding(
    ax: Axes,
    width: str | float,
    height: str | float,
    loc: str = "upper right",
    borderpad: float = 0.5,
    bbox_to_anchor: tuple[float, float] | BboxBase | None = None,
    bbox_transform: Transform | None = None,
    axes_kwargs: dict[str, Any] | None = None,
    lab_lims: list[Any] | None = None,
    minor_ticks: bool = True,
    zoom: bool | tuple[tuple[int, int], tuple[int, int]] = True,
    zoom_color: ColorType = "black",
    zoom_alpha: int | float = 0.3,
    **kwargs: Any,
) -> Axes:
    """
    A functional interface to create an inset axis with padding in a Matplotlib figure.

    This function wraps the `AxesInsetPadding` class, allowing inset axes to be created
    with a simpler function-based interface.

    Parameters
    --------------------
    ax : Axes
        The parent axis where the inset axis will be placed.
    width : str or float
        The width of the inset axis.
    height : str or float
        The height of the inset axis.
    loc : str, default="upper right"
        The location of the inset axis relative to the parent axis.
    borderpad : float, default=0.5
        Padding between the parent axis and the inset axis.
    bbox_to_anchor : tuple[float, float] | BboxBase | None, optional
        Bounding box to anchor the inset axis.
    bbox_transform : Transform | None, optional
        Transformation for the bounding box anchor.
    axes_kwargs : dict[str, Any] | None, optional
        Additional keyword arguments for the inset axis creation.
    lab_lims : list[Any] | None, optional
        Axis labels and limits for the inset axis.
    minor_ticks : bool, default=True
        Whether to enable minor ticks on the inset axis.
    zoom : bool or tuple[tuple[int, int], tuple[int, int]], default=True
        Zoom settings for the inset axis.
    zoom_color : ColorType, default="black"
        Color for the zoom connectors and patches.
    zoom_alpha : int | float, default=0.3
        Transparency for the zoom connectors and patches.
    **kwargs : Any
        Additional keyword arguments for label configuration or other customizations.

    Returns
    --------------------
    axins : Axes
        The created inset axis.


    Notes
    --------------------
    zoom provides manual inset zooming when a tuple is provided.
    zoom = ((1, 2), (3, 4)) will connect the main axis to the inset axis as follows:

    - 1 (main) - 2 (inset)
    - 3 (main) - 3 (inset)

    The indices represent the corners of the axes, with 1 being the bottom left corner

    Examples
    --------------------
    >>> import matplotlib.pyplot as plt
    >>> fig, ax = plt.subplots()
    >>> axins = axes_inset_padding(ax, "30%", "30%", loc="upper right", zoom=False)
    >>> axins.plot([0, 1], [0, 1])
    """

    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    class_params = CreateClassParams(passed_params).get_class_params()

    _axes_inset_padding = AxesInsetPadding(
        class_params["ax"],
        class_params["width"],
        class_params["height"],
        class_params["loc"],
        class_params["borderpad"],
        class_params["bbox_to_anchor"],
        class_params["bbox_transform"],
        class_params["axes_kwargs"],
        class_params["lab_lims"],
        class_params["minor_ticks"],
        class_params["zoom"],
        class_params["zoom_color"],
        class_params["zoom_alpha"],
        **class_params["kwargs"],
    )
    axins = _axes_inset_padding.axes_inset()
    return axins
