from typing import List, Union, Any
import matplotlib.pyplot as plt

from ..base.base import AttributeSetter
from .store import StoreSingleton


class Show:
    """
    A class for displaying and saving matplotlib figures with customizable options.

    Parameters
    ----------
    name : str, optional
        The base name for the saved figure files (default is "gsplot").
    ft_list : list[str], optional
        A list of file formats to save the figure (default is ["png", "pdf"]).
    dpi : float, optional
        The resolution in dots per inch for the saved figures (default is 600).
    show : bool, optional
        Whether to display the figure using `plt.show()` (default is True).
    *args : Any
        Additional positional arguments for `plt.savefig`.
    **kwargs : Any
        Additional keyword arguments for `plt.savefig`.

    Attributes
    ----------
    name : str
        The base name for the saved figure files.
    ft_list : list[str]
        The list of file formats to save the figure.
    dpi : float
        The resolution in dots per inch for the saved figures.
    show : bool
        Whether to display the figure using `plt.show()`.
    args : Any
        Additional positional arguments for `plt.savefig`.
    kwargs : Any
        Additional keyword arguments for `plt.savefig`.
    __store : StoreSingleton
        Singleton instance managing whether the figure should be stored.

    Methods
    -------
    _store_fig() -> None
        Saves the figure in the specified formats if storing is enabled.
    _get_store() -> Union[bool, int]
        Returns the current store setting from the `StoreSingleton` instance.
    """

    def __init__(
        self,
        name: str = "gsplot",
        ft_list: list[str] = ["png", "pdf"],
        dpi: float = 600,
        show: bool = True,
        *args: Any,
        **kwargs: Any,
    ):

        self.name: str = name
        self.ft_list: list[str] = ft_list
        self.dpi: float = dpi
        self.show: bool = show
        self.args: Any = args
        self.kwargs: Any = kwargs

        attributer = AttributeSetter()
        self.kwargs = attributer.set_attributes(self, locals(), key="show")

        self.__store: StoreSingleton = StoreSingleton()

        if self.show:
            plt.show()

    def _store_fig(self) -> None:
        """
        Saves the figure in the specified formats if storing is enabled.

        The figure is saved with the base name and file formats specified
        during initialization. The `dpi`, `bbox_inches`, and other options
        can be customized.

        Raises
        ------
        Exception
            If an error occurs during the saving process.
        """

        if self._get_store():
            # save figure
            fname_list: list[str] = [f"{self.name}.{ft}" for ft in self.ft_list]

            try:
                for fname in fname_list:
                    plt.savefig(
                        fname,
                        bbox_inches="tight",
                        dpi=self.dpi,
                        *self.args,
                        **self.kwargs,
                    )

            except Exception as e:
                print(f"Exception: {e}")
                for fname in fname_list:
                    plt.savefig(fname, bbox_inches="tight", dpi=self.dpi)

    def _get_store(self) -> Union[bool, int]:
        """
        Returns the current store setting from the `StoreSingleton` instance.

        Returns
        -------
        Union[bool, int]
            The current store setting, which determines whether the figure should be saved.
        """

        store: Union[bool, int] = self.__store.store
        return store


def show(
    fname: str = "gsplot",
    ft_list: list[str] = ["png", "pdf"],
    dpi: float = 600,
    show: bool = True,
    *args: Any,
    **kwargs: Any,
) -> None:
    """
    Displays and saves a matplotlib figure with customizable options.

    This function creates an instance of the `Show` class to handle the display and saving
    of the figure. The figure can be saved in multiple formats and with specified resolution.

    Parameters
    ----------
    fname : str, optional
        The base name for the saved figure files (default is "gsplot").
    ft_list : list[str], optional
        A list of file formats to save the figure (default is ["png", "pdf"]).
    dpi : float, optional
        The resolution in dots per inch for the saved figures (default is 600).
    show : bool, optional
        Whether to display the figure using `plt.show()` (default is True).
    *args : Any
        Additional positional arguments for `plt.savefig`.
    **kwargs : Any
        Additional keyword arguments for `plt.savefig`.

    Returns
    -------
    None
    """

    _show = Show(fname, ft_list, dpi, show, *args, **kwargs)
    _show._store_fig()
