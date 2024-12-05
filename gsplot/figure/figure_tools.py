from typing import Any

from matplotlib import pyplot as plt
from numpy.typing import NDArray

__all__: list[str] = ["get_figure_size"]


class FigureLayout:
    """
    A utility class for retrieving the size of the current Matplotlib figure.

    This class provides a method to get the size of the current figure in inches.

    Methods
    --------------------
    get_figure_size()
        Retrieves the size of the current figure in inches.

    Examples
    --------------------
    >>> layout = FigureLayout()
    >>> size = layout.get_figure_size()
    >>> print(size)
    array([10.,  6.])  # Example output (width, height in inches)
    """

    def get_figure_size(self) -> NDArray[Any]:
        """
        Retrieves the size of the current Matplotlib figure in inches.

        Returns
        --------------------
        numpy.ndarray
            The width and height of the current figure in inches as a NumPy array.

        Examples
        --------------------
        >>> layout = FigureLayout()
        >>> size = layout.get_figure_size()
        >>> print(size)
        array([10.,  6.])  # Example output (width, height in inches)
        """
        figure_size = plt.gcf().get_size_inches()
        return figure_size


def get_figure_size() -> NDArray[Any]:
    """
    A convenient function to retrieve the size of the current Matplotlib figure.

    This function is a shorthand for calling `FigureLayout().get_figure_size()`.

    Returns
    --------------------
    numpy.ndarray
        The width and height of the current figure in inches as a NumPy array.

    Examples
    --------------------
    >>> import gsplot as gs
    >>> size = gs.get_figure_size()
    >>> print(size)
    array([10.,  6.])  # Example output (width, height in inches)
    """
    return FigureLayout().get_figure_size()
