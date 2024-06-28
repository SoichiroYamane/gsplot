from ..figure.axes_base import AxesSingleton
from matplotlib import rcParams


class GraphSquare:
    def __init__(self):
        self.__axes = AxesSingleton()
        self._axes = self.__axes.axes

    def set_square(self, axis_index: int):
        axis = self._axes[axis_index]
        axis.set_box_aspect(1)

    def set_square_all(self):
        for axis_index in range(len(self._axes)):
            self.set_square(axis_index)


class GraphWhite:
    def __init__(self):
        self.__axes = AxesSingleton()
        self._axes = self.__axes.axes

    def set_white(self, axis_index: int):
        axis = self._axes[axis_index]

        axis.xaxis.label.set_color("w")
        axis.yaxis.label.set_color("w")
        axis.title.set_color("w")
        for child in axis.get_children():
            if hasattr(child, "set_color"):
                child.set_color("w")
        axis.tick_params(axis="x", which="both", colors="w")
        axis.tick_params(axis="y", which="both", colors="w")

        axis.patch.set_alpha(0)

    def set_white_all(self):
        rcParams["text.color"] = "w"
        for axis_index in range(len(self._axes)):
            self.set_white(axis_index)

    def set_white_axis(self, axis_index: int):
        axis = self._axes[axis_index]

        axis.xaxis.label.set_color("w")
        axis.yaxis.label.set_color("w")
        axis.title.set_color("w")

        for spine in axis.spines.values():
            spine.set_edgecolor("w")

        axis.tick_params(axis="x", which="both", colors="w")
        axis.tick_params(axis="y", which="both", colors="w")

        axis.patch.set_alpha(0)

    def set_white_axis_all(self):
        rcParams["text.color"] = "w"
        for axis_index in range(len(self._axes)):
            self.set_white_axis(axis_index)


class GraphTransparent:
    def __init__(self):
        self.__axes = AxesSingleton()
        self._axes = self.__axes.axes

        rcParams.update(
            {
                "figure.facecolor": (1.0, 0.0, 0.0, 0),
                "axes.facecolor": (0.0, 1.0, 0.0, 0),
                "savefig.facecolor": (0.0, 0.0, 1.0, 0),
            }
        )

    def set_transparent(self, axis_index: int):
        axis = self._axes[axis_index]
        axis.patch.set_alpha(0)

    def set_transparent_all(self):
        for axis_index in range(len(self._axes)):
            self.set_transparent(axis_index)
