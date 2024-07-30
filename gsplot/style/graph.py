from ..figure.axes_base import AxesSingleton
from matplotlib import rcParams

from matplotlib.axes import Axes

from typing import List


class GraphSquare:
    def __init__(self) -> None:
        self.__axes: AxesSingleton = AxesSingleton()
        self._axes: List[Axes] = self.__axes.axes

    def set_square(self, axis_index: int) -> None:
        axis: Axes = self._axes[axis_index]
        axis.set_box_aspect(1)

    def set_square_all(self):
        for axis_index in range(len(self._axes)):
            self.set_square(axis_index)


def graph_square(axis_index: int) -> None:
    GraphSquare().set_square(axis_index)


def graph_square_all() -> None:
    GraphSquare().set_square_all()


class GraphWhite:
    def __init__(self) -> None:
        self.__axes: AxesSingleton = AxesSingleton()
        self._axes: List[Axes] = self.__axes.axes

    def set_white(self, axis_index: int) -> None:
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
        rcParams["text.color"] = "w"
        for axis_index in range(len(self._axes)):
            self.set_white(axis_index)

    def set_white_axis(self, axis_index: int) -> None:
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
        rcParams["text.color"] = "w"
        for axis_index in range(len(self._axes)):
            self.set_white_axis(axis_index)


def graph_white(axis_index: int) -> None:
    GraphWhite().set_white(axis_index)


def graph_white_all() -> None:
    GraphWhite().set_white_all()


def graph_white_axis(axis_index: int) -> None:
    GraphWhite().set_white_axis(axis_index)


def graph_white_axis_all() -> None:
    GraphWhite().set_white_axis_all()


class GraphTransparent:
    def __init__(self) -> None:
        self.__axes = AxesSingleton()
        self._axes = self.__axes.axes

        rcParams.update(
            {
                "figure.facecolor": (1.0, 0.0, 0.0, 0),
                "axes.facecolor": (0.0, 1.0, 0.0, 0),
                "savefig.facecolor": (0.0, 0.0, 1.0, 0),
            }
        )

    def set_transparent(self, axis_index: int) -> None:
        axis: Axes = self._axes[axis_index]
        axis.patch.set_alpha(0)

    def set_transparent_all(self) -> None:
        for axis_index in range(len(self._axes)):
            self.set_transparent(axis_index)


def graph_transparent(axis_index: int) -> None:
    GraphTransparent().set_transparent(axis_index)


def graph_transparent_all() -> None:
    GraphTransparent().set_transparent_all()
