from typing import Any

import matplotlib.pyplot as plt
# from matplotlib.axes import Axes
from matplotlib.text import Text

__all__ = ["title"]


class Title:
    def __init__(self, title: str, **kwargs: Any) -> None:
        self.title: str = title
        self.kwargs: Any = kwargs

    def set_title(self) -> Text:
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
