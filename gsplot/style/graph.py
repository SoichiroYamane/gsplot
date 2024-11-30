from matplotlib import rcParams
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib.pyplot as plt
from ..figure.axes_base import AxesResolver


class GraphSquare:
    def __init__(self) -> None:
        self._axes: list[Axes] = plt.gcf().axes

    def set_square(self, axis_target: int | Axes) -> None:

        axis: Axes = AxesResolver(axis_target).axis
        axis.set_box_aspect(1)

    def set_square_axes(self) -> None:

        for axis in self._axes:
            axis.set_box_aspect(1)


def graph_square(axis_target: int | Axes) -> None:

    GraphSquare().set_square(axis_target)


def graph_square_axes() -> None:

    GraphSquare().set_square_axes()


# TODO: remove set_white_axis
class GraphWhite:

    def __init__(self) -> None:
        self._axes: list[Axes] = plt.gcf().axes

    def set_white(self, axis_target: int | Axes) -> None:

        axis: Axes = AxesResolver(axis_target).axis

        axis.xaxis.label.set_color("w")
        axis.yaxis.label.set_color("w")
        axis.title.set_color("w")

        for spine in axis.spines.values():
            spine.set_edgecolor("w")

        axis.tick_params(axis="x", which="both", colors="w")
        axis.tick_params(axis="y", which="both", colors="w")

        axis.patch.set_alpha(0)

    def set_white_axes(self) -> None:

        rcParams["text.color"] = "w"
        for axis_index in range(len(self._axes)):
            self.set_white(axis_index)


def graph_white(axis_target: int | Axes) -> None:

    GraphWhite().set_white(axis_target)


def graph_white_axes() -> None:

    GraphWhite().set_white_axes()


class GraphTransparent:

    def __init__(self) -> None:
        self._axes: list[Axes] = plt.gcf().axes

        rcParams.update(
            {
                "figure.facecolor": (1.0, 0.0, 0.0, 0),
                "axes.facecolor": (0.0, 1.0, 0.0, 0),
                "savefig.facecolor": (0.0, 0.0, 1.0, 0),
            }
        )

    def set_transparent(self, axis_target: int | Axes) -> None:

        axis: Axes = AxesResolver(axis_target).axis
        axis.patch.set_alpha(0)

    def set_transparent_axes(self) -> None:

        for axis in self._axes:
            self.set_transparent(axis)


def graph_transparent(axis_target: int | Axes) -> None:

    GraphTransparent().set_transparent(axis_target)


def graph_transparent_axes() -> None:

    GraphTransparent().set_transparent_axes()


class GraphFaceColor:
    def __init__(self) -> None:
        self.fig: Figure = plt.gcf()

    def set_facecolor(self, color: str = "black") -> None:
        self.fig.patch.set_facecolor(color)


def graph_facecolor(color: str = "black") -> None:
    GraphFaceColor().set_facecolor(color)
