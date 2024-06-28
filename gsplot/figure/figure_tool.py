from matplotlib import pyplot as plt
import numpy as np


class FigureLayout:

    def get_figure_size(self) -> np.ndarray:
        figure_size = plt.gcf().get_size_inches()
        return figure_size
