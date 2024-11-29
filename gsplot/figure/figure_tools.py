from numpy.typing import NDArray
from typing import Any

from matplotlib import pyplot as plt


class FigureLayout:
    def get_figure_size(self) -> NDArray[Any]:

        figure_size = plt.gcf().get_size_inches()
        return figure_size


def get_figure_size() -> NDArray[Any]:

    return FigureLayout().get_figure_size()
