from typing import (
    cast,
    Callable,
    Any,
    Literal,
    Callable,
    TypeVar,
)


from numpy.typing import ArrayLike, NDArray
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.transforms import Bbox
from ..figure.axes_base import (
    AxisRangeController,
    AxesRangeSingleton,
    AxisRangeManager,
)
from ..base.base import bind_passed_params, ParamsGetter, CreateClassParams


from .ticks import MinorTicksAll

import warnings
from functools import wraps

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

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

    def __init__(
        self,
        position: Literal["in", "out", "corner"] = "out",
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
        self.position = position
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

    @staticmethod
    def int_to_roman(n: int) -> str:
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

        for i, axis in enumerate(self._axes):
            position = self._get_render_position(axis)
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
    position: Literal["in", "out", "corner"] = "out",
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
    Add index labels to a plot at specified positions.

    This function adds labels (e.g., alphabetic, numeric, or other glyphs) to a
    plot, with options to adjust position, offset, alignment, font size, and case.

    Parameters
    ----------
    position : {"in", "out", "corner"}, optional
        The relative position of the labels:
        - "in": Inside the plot.
        - "out": Outside the plot.
        - "corner": Positioned at the corners. Default is "out".
    x_offset : float, optional
        The horizontal offset of the label relative to the specified position.
        Default is 0.
    y_offset : float, optional
        The vertical offset of the label relative to the specified position.
        Default is 0.
    ha : str, optional
        The horizontal alignment of the label. Common values include "center",
        "left", or "right". Default is "center".
    va : str, optional
        The vertical alignment of the label. Common values include "center",
        "top", or "bottom". Default is "center".
    fontsize : float or str, optional
        The font size of the label. Can be a numeric value or a predefined size
        like "small", "medium", or "large". Default is "large".
    glyph : {"alphabet", "roman", "number", "hiragana"}, optional
        The type of glyph used for the labels:
        - "alphabet": Alphabetic (A, B, C...).
        - "roman": Roman numerals (I, II, III...).
        - "number": Numeric (1, 2, 3...).
        - "hiragana": Hiragana characters. Default is "alphabet".
    capitalize : bool, optional
        If True, capitalize the labels (applies only to "alphabet" glyph). Default
        is False.
    *args : Any
        Additional positional arguments for the labeling process.
    **kwargs : Any
        Additional keyword arguments for customizing the labels.

    Returns
    -------
    None
        This function does not return anything.

    Notes
    -----
    - This function uses the `LabelAddIndex` class to handle label creation and
      placement.
    - Offset values (`x_offset`, `y_offset`) are applied relative to the specified
      position, allowing fine-grained control over label placement.
    - Alignment options (`ha`, `va`) can be used to adjust label alignment within
      their position.

    Examples
    --------
    Add labels with default settings:

    >>> label_add_index()

    Add labels at the corners with an offset:

    >>> label_add_index(position="corner", x_offset=0.1, y_offset=0.1)

    Use numeric labels with larger font size:

    >>> label_add_index(glyph="number", fontsize=14)

    Capitalize alphabetic labels and adjust alignment:

    >>> label_add_index(glyph="alphabet", capitalize=True, ha="left", va="top")
    """

    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    class_params = CreateClassParams(passed_params).get_class_params()

    _label_add_index: LabelAddIndex = LabelAddIndex(
        class_params["position"],
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

        self._axes: list[Axes] = plt.gcf().axes

    def set_xticks(
        self, axis: Axes, base: float | None = None, num_minor: int | None = None
    ) -> None:

        if base is not None:
            axis.xaxis.set_major_locator(plticker.MultipleLocator(base=base))
        if num_minor is not None:
            axis.xaxis.set_minor_locator(plticker.AutoMinorLocator(num_minor))

    def set_yticks(
        self, axis: Axes, base: float | None = None, num_minor: int | None = None
    ) -> None:

        if base is not None:
            axis.yaxis.set_major_locator(plticker.MultipleLocator(base=base))
        if num_minor is not None:
            axis.yaxis.set_minor_locator(plticker.AutoMinorLocator(num_minor))

    def remove_xlabels(self, axis: Axes) -> None:

        axis.set_xlabel("")
        axis.tick_params(labelbottom=False)

    def remove_ylabels(self, axis: Axes) -> None:

        axis.set_ylabel("")
        axis.tick_params(labelleft=False)

    def add_minor_ticks_all(self) -> None:

        if self.minor_ticks_all:
            MinorTicksAll().set_minor_ticks_all()

    def configure_axis_labels(self, axis, x_lab, y_lab):
        if x_lab:
            axis.set_xlabel(x_lab)
        else:
            self.remove_xlabels(axis)

        if y_lab:
            axis.set_ylabel(y_lab)
        else:
            self.remove_ylabels(axis)

    def configure_axis_limits(self, axis, lims, final_axes_range=None, index=None):
        if lims:
            x_lims, y_lims = lims

            # Set axis limits
            for lim, val in zip(
                ["xmin", "xmax", "ymin", "ymax"],
                [x_lims[0], x_lims[1], y_lims[0], y_lims[1]],
            ):
                if val != "":
                    axis.axis(**{lim: val})

            # Configure x-axis scale or ticks
            if len(x_lims) > 2:
                if isinstance(x_lims[2], str):
                    axis.set_xscale(x_lims[2])
                else:
                    self.set_xticks(axis, num_minor=x_lims[2])
                    if len(x_lims) > 3:
                        self.set_xticks(axis, base=x_lims[3])

            # Configure y-axis scale or ticks
            if len(y_lims) > 2:
                if isinstance(y_lims[2], str):
                    axis.set_yscale(y_lims[2])
                else:
                    self.set_yticks(axis, num_minor=y_lims[2])
                    if len(y_lims) > 3:
                        self.set_yticks(axis, base=y_lims[3])
        elif final_axes_range and index is not None:
            final_axis_range = final_axes_range[index]
            axis.axis(
                xmin=final_axis_range[0][0],
                xmax=final_axis_range[0][1],
                ymin=final_axis_range[1][0],
                ymax=final_axis_range[1][1],
            )

    def set_labels(self):
        final_axes_range = self._get_final_axes_range()

        for i, (x_lab, y_lab, *lims) in enumerate(self.lab_lims):
            axis = self._axes[i]

            # Configure axis labels
            self.configure_axis_labels(axis, x_lab, y_lab)

            # Configure axis limits and scales
            self.configure_axis_limits(axis, lims, final_axes_range, i)

            self._get_final_axes_range()

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
        for axis_index in range(len(self._axes)):
            xrange = AxisRangeController(axis_index).get_axis_xrange()
            yrange = AxisRangeController(axis_index).get_axis_yrange()
            axes_ranges_current.append([xrange, yrange])
        return axes_ranges_current

    def _get_final_axes_range(self) -> list[list[NDArray[Any]]]:

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
    def apply_tight_layout(self) -> None:

        if self.tight_layout:
            try:
                plt.tight_layout(
                    w_pad=self.x_pad, h_pad=self.y_pad, *self.args, **self.kwargs
                )
            except Exception:
                plt.tight_layout(w_pad=self.x_pad, h_pad=self.y_pad)

    def label(self) -> None:

        self.add_minor_ticks_all()
        self.set_labels()
        self.apply_tight_layout()


# TODO: modify the docstring
@bind_passed_params()
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
    Add labels and adjust axis limits and layout for a plot.

    This function adds labels to a plot and adjusts the axis limits and layout
    according to the provided parameters. It supports customizing padding, minor
    tick marks, and layout constraints.

    Parameters
    ----------
    lab_lims : list[Any]
        A list specifying the limits or labels for the axes. This can include
        axis ranges, tick labels, or other relevant specifications.
    x_pad : int, optional
        The padding applied to the x-axis labels. Default is 2.
    y_pad : int, optional
        The padding applied to the y-axis labels. Default is 2.
    minor_ticks_all : bool, optional
        If True, enable minor tick marks for all axes. Default is True.
    tight_layout : bool, optional
        If True, adjust the layout of the plot to minimize overlap between
        elements. Default is True.
    *args : Any
        Additional positional arguments passed to the labeling process.
    **kwargs : Any
        Additional keyword arguments for customizing the labeling process.

    Returns
    -------
    None
        This function does not return anything.

    Notes
    -----
    - This function uses the `Label` class to handle label creation and axis
      adjustments.
    - The `lab_lims` parameter provides flexibility in defining axis limits,
      labels, or other configurations.
    - Padding (`x_pad`, `y_pad`) allows fine-tuned spacing between labels and
      axis ticks.
    - Enabling `tight_layout` is useful for ensuring a clean and uncluttered
      appearance in plots with dense elements.

    Examples
    --------
    Add labels with default settings:

    >>> label(lab_lims=[(0, 10), (0, 5)])

    Customize padding and disable minor ticks:

    >>> label(lab_lims=[(0, 10), (0, 5)], x_pad=5, y_pad=5, minor_ticks_all=False)

    Adjust axis limits and enable tight layout:

    >>> label(lab_lims=[(0, 20), (0, 15)], tight_layout=True)

    Pass additional arguments for advanced customization:

    >>> label(lab_lims=[(0, 10), (0, 5)], fontsize=12, rotation=45)
    """

    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    class_params = CreateClassParams(passed_params).get_class_params()

    _label = Label(
        class_params["lab_lims"],
        class_params["x_pad"],
        class_params["y_pad"],
        class_params["minor_ticks_all"],
        class_params["tight_layout"],
        *class_params["args"],
        **class_params["kwargs"],
    )

    _label.label()
