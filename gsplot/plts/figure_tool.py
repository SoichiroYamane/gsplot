from matplotlib import pyplot as plt
import numpy as np


class FigureLayout:
    def __init__(self):
        pass

    def get_figure_size(self) -> np.ndarray:
        return plt.gcf().get_size_inches()
