from matplotlib import pyplot as plt
import numpy as np


class FigureLayout:
    """
    A class to manage and retrieve the size of the current matplotlib figure.

    Methods
    -------
    get_figure_size() -> np.ndarray
        Returns the size of the current figure in inches as a NumPy array.
    """

    def get_figure_size(self) -> np.ndarray:
        """
        Returns the size of the current figure in inches as a NumPy array.

        Returns
        -------
        np.ndarray
            A NumPy array containing the width and height of the current figure in inches.
        """

        figure_size = plt.gcf().get_size_inches()
        return figure_size


def get_figure_size() -> np.ndarray:
    """
    Retrieves the size of the current matplotlib figure using the `FigureLayout` class.

    Returns
    -------
    np.ndarray
        A NumPy array containing the width and height of the current figure in inches.
    """

    return FigureLayout().get_figure_size()
