from typing import Any

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.text import Text

__all__ = ["title", "title_axes"]


class Title:
    """
    Set the title of the current figure.

    Parameters
    --------------------
    title : str
    **kwargs : Any

    Attributes
    --------------------
    title : str
    kwargs : Any

    Methods
    --------------------
    set_title()
        Set the title of the current figure
    """

    def __init__(self, title: str, **kwargs: Any) -> None:
        self.title: str = title
        self.kwargs: Any = kwargs

    def set_title(self) -> Text:
        """
        Set the title of the current figure.

        Returns
        --------------------
        Text
            The title of the current figure.
        """
        return plt.gcf().suptitle(self.title, **self.kwargs)


def title(title: str, **kwargs: Any) -> Text:
    """
    Set the title of the current figure.

    Parameters
    --------------------
    title : str
        The title of the current figure.
    **kwargs : Any
        Additional keyword arguments to pass to the title.

    Returns
    --------------------
    Text
        The title of the current figure.
    """
    return Title(title=title, **kwargs).set_title()


class TitleAxes:
    """
    Set the title of the current figure.

    Parameters
    --------------------
    ax : Axes
    title : str
    **kwargs : Any

    Attributes
    --------------------
    ax : Axes
    title : str
    kwargs : Any

    Methods
    --------------------
    set_title()
        Set the title of the current figure
    """

    def __init__(self, ax: Axes, title: str, **kwargs: Any) -> None:
        self.ax: Axes = ax
        self.title: str = title
        self.kwargs: Any = kwargs

    def set_title(self) -> Text:
        """
        Set the title of the current figure.

        Returns
        --------------------
        Text
            The title of the current figure.
        """
        return self.ax.set_title(self.title, **self.kwargs)


def title_axes(ax: Axes, title: str, **kwargs: Any) -> Text:
    """
    Set the title of the current figure.

    Parameters
    --------------------
    ax : Axes
        The axes to set the title of.
    title : str
        The title of the current figure.
    **kwargs : Any
        Additional keyword arguments to pass to the title.

    Returns
    --------------------
    Text
        The title of the current figure.
    """
    return TitleAxes(ax=ax, title=title, **kwargs).set_title()
