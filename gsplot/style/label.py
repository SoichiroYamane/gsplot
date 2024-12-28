import warnings
from functools import wraps
from typing import Any, Callable, Literal, TypeVar, cast

import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import numpy as np
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.transforms import Bbox
from numpy.typing import NDArray
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ..base.base import CreateClassParams, ParamsGetter, bind_passed_params
from ..figure.axes_range_base import (AxesRangeSingleton, AxisRangeController,
                                      AxisRangeManager)
from .ticks import MinorTicksAxes

__all__ = ["label", "label_add_index"]


console = Console()


F = TypeVar("F", bound=Callable[..., Any])


# !TODO: When label is removed from script with index, and the script is called to repl, it will throw warning.
# fix this behavior.
class FuncOrderManager:
    def __init__(
        self,
    ) -> None:
        self.last_called: str | None = None
        self.rules: dict = {}

    def add_rule(self, func_a: str, func_b: str, warning_message: str) -> None:
        self.rules[(func_b, func_a)] = warning_message

    def track(self, func_name: str) -> None:
        if self.last_called is not None:
            if (self.last_called, func_name) in self.rules:
                warning_message = self.rules[(self.last_called, func_name)]
                warning_text = Text.from_markup(warning_message, justify="center")
                console.print(
                    Panel(
                        warning_text,
                        title="[bold yellow]Warning",
                        style="bold yellow",
                    )
                )

            self.reset()
        else:
            self.last_called = func_name

    def reset(self) -> None:
        self.last_called = None


order_manager = FuncOrderManager()
order_manager.add_rule(
    "label",
    "label_add_index",
    "[bold green]label_add_index[bold yellow] should be called after [bold red]label",
)


def track_order(func: F) -> F:

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        func_name = func.__name__
        order_manager.track(func_name)
        return func(*args, **kwargs)

    return cast(F, wrapper)


class LabelAddIndex:
    """
    A class to add index labels to axes in a Matplotlib figure.

    This class allows labeling axes with indices in customizable positions, glyphs,
    and styles.

    Parameters
    --------------------
    loc : {'in', 'out', 'corner'}, default='out'
        Location of the label relative to the axes:
        - 'in': Inside the axes.
        - 'out': Outside the axes.
        - 'corner': Top-left corner of the axes.
    x_offset : float, default=0
        Horizontal offset for the label position.
    y_offset : float, default=0
        Vertical offset for the label position.
    ha : str, default='center'
        Horizontal alignment of the label.
    va : str, default='top'
        Vertical alignment of the label.
    fontsize : str or float, default='large'
        Font size of the label.
    glyph : {'alphabet', 'roman', 'number', 'hiragana'}, default='alphabet'
        Style of the label:
        - 'alphabet': Letters (a, b, c, ...).
        - 'roman': Roman numerals (i, ii, iii, ...).
        - 'number': Numbers (1, 2, 3, ...).
        - 'hiragana': Japanese Hiragana (あ, い, う, ...).
    capitalize : bool, default=False
        If True, capitalize the label (e.g., A, B, C instead of a, b, c).
    *args : Any
        Additional arguments for `matplotlib.text.Text`.
    **kwargs : Any
        Additional keyword arguments for `matplotlib.text.Text`.

    Attributes
    --------------------
    fig : matplotlib.figure.Figure
        The current figure object.
    _axes : list[matplotlib.axes.Axes]
        List of axes in the current figure.
    renderer : matplotlib.backends.backend_agg.RendererAgg
        Renderer for the figure.
    fig_width : float
        Width of the figure in pixels.
    fig_height : float
        Height of the figure in pixels.
    canvas_width : int
        Width of the canvas in pixels.
    canvas_height : int
        Height of the canvas in pixels.
    normalization_factors : numpy.ndarray
        Factors for normalizing coordinates.

    Methods
    --------------------
    add_index() -> None
        Adds index labels to the axes.
    """

    def __init__(
        self,
        loc: Literal["in", "out", "corner"] = "out",
        x_offset: float = 0,
        y_offset: float = 0,
        ha: str = "center",
        va: str = "top",
        fontsize: str | float = "large",
        glyph: Literal["alphabet", "roman", "number", "hiragana"] = "alphabet",
        capitalize: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.loc = loc
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.ha = ha
        self.va = va
        self.fontsize = fontsize
        self.glyph = glyph
        self.capitalize = capitalize

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

    def _get_render_position(self, ax: Axes) -> tuple[float, float] | None:
        """
        Calculates the position for the index label based on the location.

        Parameters
        --------------------
        ax : matplotlib.axes.Axes
            The axis for which to calculate the label position.

        Returns
        --------------------
        tuple[float, float] or None
            The (x, y) coordinates of the label in figure-relative coordinates,
            or None if the bounding box is unavailable.

        Raises
        --------------------
        ValueError
            If the specified location (`loc`) is invalid.
        """
        bbox: Bbox | None = None
        PADDING_X: float = 0
        PADDING_Y: float = 0

        if self.loc == "out":
            # Coordinate: device coordinates
            bbox = ax.get_tightbbox(self.renderer)
            PADDING_X, PADDING_Y = 0, -5
        elif self.loc == "in":
            # Coordinate: device coordinates
            bbox = ax.get_window_extent(self.renderer)
            PADDING_X, PADDING_Y = 30, -30
        elif self.loc == "corner":
            bbox = ax.get_window_extent(self.renderer)
        else:
            raise ValueError(
                f"Invalid position: {self.loc}, must be 'in', 'out', or 'corner'"
            )

        # Ensure that padding does not depend on the figure size
        PADDING_X = PADDING_X / self.canvas_width
        PADDING_Y = PADDING_Y / self.canvas_height

        if bbox is None:
            print(f"No bounding box available for the axis. axis: {ax}")
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

    @staticmethod
    def int_to_roman(n: int) -> str:
        """
        Converts an integer to its Roman numeral representation.

        Parameters
        --------------------
        n : int
            The integer to convert.

        Returns
        --------------------
        str
            The Roman numeral representation.

        Examples
        --------------------
        >>> LabelAddIndex.int_to_roman(3)
        'iii'
        """
        roman_numerals = {
            1: "i",
            2: "ii",
            3: "iii",
            4: "iv",
            5: "v",
            6: "vi",
            7: "vii",
            8: "viii",
            9: "ix",
            10: "x",
            11: "xi",
            12: "xii",
            13: "xiii",
            14: "xiv",
            15: "xv",
            16: "xvi",
            17: "xvii",
            18: "xviii",
        }
        return roman_numerals.get(n, "")

    def get_index_glyph(self, n: int) -> str:
        """
        Retrieves the glyph representation of the index.

        Parameters
        --------------------
        n : int
            The index of the current axis (0-based).

        Returns
        --------------------
        str
            The glyph for the index.

        Raises
        --------------------
        ValueError
            If the specified glyph style (`glyph`) is invalid.

        Examples
        --------------------
        >>> LabelAddIndex(glyph='alphabet').get_index_glyph(0)
        'a'
        >>> LabelAddIndex(glyph='number').get_index_glyph(2)
        '3'
        """
        index_glyph: str = ""
        if self.glyph == "alphabet":
            index_glyph = "abcdefghijklmnopqrstuvwxyz"[n]
        elif self.glyph == "roman":
            index_glyph = self.int_to_roman(n + 1)
        elif self.glyph == "number":
            index_glyph = str(n + 1)
        elif self.glyph == "hiragana":
            index_glyph = "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよん"[
                n
            ]
        else:
            raise ValueError(
                f"Invalid glyph: {self.glyph}, must be 'alphabet', 'roman', 'number', or 'hiragana'"
            )
        if self.capitalize:
            index_glyph = index_glyph.upper()
        return index_glyph

    def add_index(self) -> None:
        """
        Adds index labels to all axes in the current figure.

        The labels are positioned according to the specified location (`loc`),
        offsets, and alignment.

        Returns
        --------------------
        None
        """
        for i, ax in enumerate(self._axes):
            position = self._get_render_position(ax)
            if position is None:
                continue
            x, y = position

            glyph = self.get_index_glyph(i)
            self.fig.text(
                x,
                y,
                f"($\\,${glyph}$\\,$)",
                ha=self.ha,
                va=self.va,
                fontsize=self.fontsize,
                transform=self.fig.transFigure,
                *self.args,
                **self.kwargs,
            )


@bind_passed_params()
@track_order
def label_add_index(
    loc: Literal["in", "out", "corner"] = "out",
    x_offset: float = 0,
    y_offset: float = 0,
    ha: str = "center",
    va: str = "center",
    fontsize: float | str = "large",
    glyph: Literal["alphabet", "roman", "number", "hiragana"] = "alphabet",
    capitalize: bool = False,
    *args: Any,
    **kwargs: Any,
) -> None:
    """
    Adds index labels to axes in a Matplotlib figure.

    This function is a wrapper for the `LabelAddIndex` class.

    Parameters
    --------------------
    loc : {'in', 'out', 'corner'}, default='out'
        Location of the label relative to the axes.
    x_offset : float, default=0
        Horizontal offset for the label position.
    y_offset : float, default=0
        Vertical offset for the label position.
    ha : str, default='center'
        Horizontal alignment of the label.
    va : str, default='center'
        Vertical alignment of the label.
    fontsize : str or float, default='large'
        Font size of the label.
    glyph : {'alphabet', 'roman', 'number', 'hiragana'}, default='alphabet'
        Style of the label.
    capitalize : bool, default=False
        If True, capitalize the label.
    *args : Any
        Additional arguments for `matplotlib.text.Text`.
    **kwargs : Any
        Additional keyword arguments for `matplotlib.text.Text`.

    Notes
    --------------------
    This function utilizes the `ParamsGetter` to retrieve bound parameters
    and the `CreateClassParams` class to handle the merging of default,
    configuration, and passed parameters.

    Returns
    --------------------
    None

    Warnings
    --------------------
    This function should be called after the :func:`gsplot.label <gsplot.style.label.label>` function

    Examples
    --------------------
    >>> import gsplot as gs
    >>> gs.label_add_index(loc='out', glyph='roman', fontsize=12)
    >>> gs.label_add_index(loc='corner', capitalize=True)
    """
    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    class_params = CreateClassParams(passed_params).get_class_params()

    _label_add_index: LabelAddIndex = LabelAddIndex(
        class_params["loc"],
        class_params["x_offset"],
        class_params["y_offset"],
        class_params["ha"],
        class_params["va"],
        class_params["fontsize"],
        class_params["glyph"],
        class_params["capitalize"],
        *class_params["args"],
        **class_params["kwargs"],
    )
    _label_add_index.add_index()


class Label:
    """
    A class to configure labels, limits, and ticks for Matplotlib axes.

    This class facilitates the customization of axis labels, limits, tick marks,
    and layouts for multiple axes in a Matplotlib figure.

    Parameters
    --------------------
    lab_lims : list[Any]
        A list specifying labels and limits for each axis in the figure. Each entry
        should be a tuple of the form `(x_label, y_label, x_limits, y_limits)`.
    x_pad : int, default=2
        Horizontal padding for tight layout.
    y_pad : int, default=2
        Vertical padding for tight layout.
    minor_ticks_axes : bool, default=True
        Whether to add minor ticks to all axes.
    tight_layout : bool, default=True
        Whether to apply `tight_layout` to the figure.
    *args : Any
        Additional arguments for `plt.tight_layout`.
    **kwargs : Any
        Additional keyword arguments for `plt.tight_layout`.

    Attributes
    --------------------
    lab_lims : list[Any]
        The labels and limits configuration for the axes.
    x_pad : int
        Horizontal padding for tight layout.
    y_pad : int
        Vertical padding for tight layout.
    minor_ticks_axes : bool
        Whether minor ticks are enabled for axes.
    tight_layout : bool
        Whether `tight_layout` is applied.
    _axes : list[Axes]
        List of axes in the current figure.

    Methods
    --------------------
    set_xticks(ax, base=None, num_minor=None) -> None
        Configures the major and minor ticks for the x-axis.
    set_yticks(ax, base=None, num_minor=None) -> None
        Configures the major and minor ticks for the y-axis.
    remove_xlabels(ax) -> None
        Removes the x-axis labels for a given axis.
    remove_ylabels(ax) -> None
        Removes the y-axis labels for a given axis.
    add_minor_ticks_axes() -> None
        Adds minor ticks to all axes in the figure.
    configure_axis_labels(ax, x_lab, y_lab) -> None
        Configures the labels for a given axis.
    configure_axis_limits(ax, lims, final_axes_ranges=None) -> None
        Configures the limits and scales for a given axis.
    set_labels() -> None
        Applies labels, limits, and scales to all axes based on the configuration.
    apply_tight_layout() -> None
        Applies `tight_layout` to the figure.
    label() -> None
        Adds labels, limits, and layouts to the figure's axes.
    """

    def __init__(
        self,
        lab_lims: list[Any],
        x_pad: int = 2,
        y_pad: int = 2,
        minor_ticks_axes: bool = True,
        tight_layout: bool = True,
        *args: Any,
        **kwargs: Any,
    ) -> None:

        self.lab_lims: list[Any] = lab_lims
        self.x_pad: int = x_pad
        self.y_pad: int = y_pad
        self.minor_ticks_axes: bool = minor_ticks_axes
        self.tight_layout: bool = tight_layout
        self.args: Any = args
        self.kwargs: Any = kwargs

        self._axes: list[Axes] = plt.gcf().axes

    def set_xticks(
        self, ax: Axes, base: float | None = None, num_minor: int | None = None
    ) -> None:
        """
        Configures the major and minor ticks for the x-axis.

        Parameters
        --------------------
        ax : matplotlib.axes.Axes
            The axis for which to configure ticks.
        base : float, optional
            Interval for the major ticks.
        num_minor : int, optional
            Number of minor ticks between consecutive major ticks.

        Returns
        --------------------
        None
        """

        if base is not None:
            ax.xaxis.set_major_locator(plticker.MultipleLocator(base=base))
        if num_minor is not None:
            ax.xaxis.set_minor_locator(plticker.AutoMinorLocator(num_minor))

    def set_yticks(
        self, ax: Axes, base: float | None = None, num_minor: int | None = None
    ) -> None:
        """
        Configures the major and minor ticks for the y-axis.

        Parameters
        --------------------
        ax : matplotlib.axes.Axes
            The axis for which to configure ticks.
        base : float, optional
            Interval for the major ticks.
        num_minor : int, optional
            Number of minor ticks between consecutive major ticks.

        Returns
        --------------------
        None
        """

        if base is not None:
            ax.yaxis.set_major_locator(plticker.MultipleLocator(base=base))
        if num_minor is not None:
            ax.yaxis.set_minor_locator(plticker.AutoMinorLocator(num_minor))

    def remove_xlabels(self, ax: Axes) -> None:
        """
        Removes the x-axis label for a given axis.

        Parameters
        --------------------
        ax : matplotlib.axes.Axes
            The axis for which to remove the x-axis label.

        Returns
        --------------------
        None
        """

        ax.set_xlabel("")
        ax.tick_params(labelbottom=False)

    def remove_ylabels(self, ax: Axes) -> None:
        """
        Removes the y-axis label for a given axis.

        Parameters
        --------------------
        ax : matplotlib.axes.Axes
            The axis for which to remove the y-axis label.

        Returns
        --------------------
        None
        """

        ax.set_ylabel("")
        ax.tick_params(labelleft=False)

    def add_minor_ticks_axes(self) -> None:
        """
        Adds minor ticks to all axes in the figure.

        Returns
        --------------------
        None
        """

        if self.minor_ticks_axes:
            MinorTicksAxes().set_minor_ticks_axes()

    def configure_axis_labels(self, ax: Axes, x_lab: str | None, y_lab: str | None):
        """
        Configures the labels for a given axis.

        Parameters
        --------------------
        ax : matplotlib.axes.Axes
            The axis to configure labels for.
        x_lab : str, optional
            The label for the x-axis. If `None`, the x-axis label is removed.
        y_lab : str, optional
            The label for the y-axis. If `None`, the y-axis label is removed.

        Returns
        --------------------
        None
        """
        if x_lab:
            ax.set_xlabel(x_lab)
        else:
            self.remove_xlabels(ax)

        if y_lab:
            ax.set_ylabel(y_lab)
        else:
            self.remove_ylabels(ax)

    def configure_axis_limits(
        self,
        ax: Axes,
        lims: list[Any],
        final_axes_ranges: dict[Axes, list] | None = None,
    ):
        """
        Configures the limits and scales for a given axis.

        Parameters
        --------------------
        ax : matplotlib.axes.Axes
            The axis to configure limits for.
        lims : list, optional
            The limits for the axis in the form `[x_lims, y_lims]`.
        final_axes_ranges : dict[matplotlib.axes.Axes, list], optional
            The final axes ranges for all axes.
        index : int, optional
            The index of the current axis.

        Returns
        --------------------
        None
        """
        if lims:
            x_lims, y_lims = lims

            # Set axis limits
            for lim, val in zip(
                ["xmin", "xmax", "ymin", "ymax"],
                [x_lims[0], x_lims[1], y_lims[0], y_lims[1]],
            ):
                if val != "":
                    ax.axis(**{lim: val})

            # Configure x-axis scale or ticks
            if len(x_lims) > 2:
                if isinstance(x_lims[2], str):
                    ax.set_xscale(x_lims[2])
                else:
                    self.set_xticks(ax, num_minor=x_lims[2])
                    if len(x_lims) > 3:
                        self.set_xticks(ax, base=x_lims[3])

            # Configure y-axis scale or ticks
            if len(y_lims) > 2:
                if isinstance(y_lims[2], str):
                    ax.set_yscale(y_lims[2])
                else:
                    self.set_yticks(ax, num_minor=y_lims[2])
                    if len(y_lims) > 3:
                        self.set_yticks(ax, base=y_lims[3])
        elif final_axes_ranges is not None:
            final_axis_range = final_axes_ranges[ax]
            ax.axis(
                xmin=final_axis_range[0][0],
                xmax=final_axis_range[0][1],
                ymin=final_axis_range[1][0],
                ymax=final_axis_range[1][1],
            )

    def set_labels(self):
        final_axes_ranges = self._get_final_axes_ranges()

        for i, (x_lab, y_lab, *lims) in enumerate(self.lab_lims):
            ax = self._axes[i]

            # Configure axis labels
            self.configure_axis_labels(ax, x_lab, y_lab)

            # Configure axis limits and scales
            self.configure_axis_limits(ax, lims, final_axes_ranges)

    def _calculate_padding_range(self, range: NDArray[Any]) -> NDArray[Any]:

        PADDING_FACTOR: float = 0.05
        span: float = range[1] - range[0]
        return np.array(
            range + np.array([-PADDING_FACTOR, PADDING_FACTOR]) * span, dtype=np.float64
        )

    def _get_wider_range(
        self, range1: NDArray[Any], range2: NDArray[Any]
    ) -> NDArray[Any]:

        new_range = np.array([min(range1[0], range2[0]), max(range1[1], range2[1])])
        return new_range

    def _get_axes_ranges_current(self) -> list[list[NDArray[Any]]]:

        axes_ranges_current = []
        for ax in self._axes:
            xrange = AxisRangeController(ax).get_axis_xrange()
            yrange = AxisRangeController(ax).get_axis_yrange()
            axes_ranges_current.append([xrange, yrange])
        return axes_ranges_current

    def _get_final_axes_ranges(self) -> dict[Axes, list[NDArray[Any]]]:
        _axes_range_singleton = AxesRangeSingleton()

        axes_ranges_current = self._get_axes_ranges_current()

        final_axes_ranges = {}
        for ax, (xrange, yrange) in zip(self._axes, axes_ranges_current):
            xrange_singleton, yrange_singleton = _axes_range_singleton.get_axes_range(
                ax
            )

            is_init_axis = AxisRangeManager(ax).is_init_axis()

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

            final_axes_ranges[ax] = [new_xrange, new_yrange]
        return final_axes_ranges

    #! Xpad and Ypad will change the size of the axis
    def apply_tight_layout(self) -> None:

        if self.tight_layout:
            # Ignore this warning when using inset_axes:
            # UserWarning: This figure includes Axes that are not compatible with tight_layout, so results might be incorrect
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    plt.tight_layout(
                        w_pad=self.x_pad, h_pad=self.y_pad, *self.args, **self.kwargs
                    )
                except Exception:
                    plt.tight_layout(w_pad=self.x_pad, h_pad=self.y_pad)

    def label(self) -> None:

        self.add_minor_ticks_axes()
        self.set_labels()
        self.apply_tight_layout()


@bind_passed_params()
@track_order
def label(
    lab_lims: list[Any],
    x_pad: int = 2,
    y_pad: int = 2,
    minor_ticks_axes: bool = True,
    tight_layout: bool = True,
    *args: Any,
    **kwargs: Any,
) -> None:
    """
    Configures labels, limits, ticks, and layouts for Matplotlib axes.

    This function is a wrapper for the `Label` class.

    Parameters
    --------------------
    lab_lims : list[Any]
        A list specifying labels and limits for each axis in the figure. Each entry
        should be a tuple of the form `(x_label, y_label, x_limits, y_limits)`.
    x_pad : int, default=2
        Horizontal padding for tight layout.
    y_pad : int, default=2
        Vertical padding for tight layout.
    minor_ticks_axes : bool, default=True
        Whether to add minor ticks to all axes.
    tight_layout : bool, default=True
        Whether to apply `tight_layout` to the figure.
    *args : Any
        Additional arguments for `plt.tight_layout`.
    **kwargs : Any
        Additional keyword arguments for `plt.tight_layout`.

    Notes
    --------------------
    This function utilizes the `ParamsGetter` to retrieve bound parameters
    and the `CreateClassParams` class to handle the merging of default,
    configuration, and passed parameters.

    Returns
    --------------------
    None

    Warnings
    --------------------
    This function should be called before the :func:`gsplot.label_add_index <gsplot.style.label.label_add_index>` function

    Examples
    --------------------
    >>> import gsplot as gs
    >>> gs.label(
    >>>     lab_lims=[("X Label", "Y Label", [1, 10, "log"], [1, 20, 2])],
    >>>     x_pad=5,
    >>>     y_pad=5,
    >>> )
    """

    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    class_params = CreateClassParams(passed_params).get_class_params()

    _label = Label(
        class_params["lab_lims"],
        class_params["x_pad"],
        class_params["y_pad"],
        class_params["minor_ticks_axes"],
        class_params["tight_layout"],
        *class_params["args"],
        **class_params["kwargs"],
    )

    _label.label()
