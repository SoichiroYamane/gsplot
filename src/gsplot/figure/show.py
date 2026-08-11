from typing import Any

import matplotlib.pyplot as plt

from ..base.base import CreateClassParams, ParamsGetter, bind_passed_params
from .store import StoreSingleton

__all__: list[str] = ["show"]


class Show:
    """
    A utility class for managing figure saving and displaying in Matplotlib.

    This class provides functionality to save the current figure in multiple formats
    and optionally display it.

    Parameters
    --------------------
    name : str, optional
        The base name for saved figure files (default is "gsplot").
    ft_list : list of str, optional
        A list of file formats for saving the figure (default is ["png", "pdf"]).
    dpi : float, optional
        The resolution (dots per inch) for saving the figure (default is 600).
    show : bool, optional
        Whether to display the figure (default is True).
    *args : Any
        Additional positional arguments passed to `plt.savefig`.
    **kwargs : Any
        Additional keyword arguments passed to `plt.savefig`.

    Attributes
    --------------------
    name : str
        The base name for saved figure files.
    ft_list : list of str
        A list of file formats for saving the figure.
    dpi : float
        The resolution for saving the figure.
    show : bool
        Whether to display the figure.
    args : Any
        Additional positional arguments passed to `plt.savefig`.
    kwargs : Any
        Additional keyword arguments passed to `plt.savefig`.
    _store_singleton : StoreSingleton
        A singleton instance for managing the storage state.

    Methods
    --------------------
    store_fig()
        Saves the current figure in the specified formats.
    get_store()
        Retrieves the storage state from the singleton instance.
    show_fig()
        Displays the current figure if `show` is True.

    Examples
    --------------------
    >>> show_instance = Show(name="example", ft_list=["png", "jpg"], dpi=300, show=False)
    >>> show_instance.store_fig()
    >>> show_instance.show_fig()  # Will not display the figure since `show=False`
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

        self._store_singleton: StoreSingleton = StoreSingleton()

    def store_fig(self) -> None:
        """
        Saves the current figure in the specified formats.

        This method uses the provided file formats and resolution to save the figure.

        Raises
        --------------------
        Exception
            If an error occurs during saving, a warning is printed.

        Examples
        --------------------
        >>> show_instance = Show(name="example", ft_list=["png", "jpg"], dpi=300)
        >>> show_instance.store_fig()
        """
        if self.get_store():
            # save figure
            fname_list: list[str] = [f"{self.name}.{ft}" for ft in self.ft_list]

            # !TODO: figure out **kwargs for savefig. None, or *args, **kwargs
            for fname in fname_list:
                try:
                    plt.savefig(
                        fname,
                        bbox_inches="tight",
                        dpi=self.dpi,
                        *self.args,
                        **self.kwargs,
                    )
                except Exception as e:
                    print(f"Error saving figure: {e}")
                    plt.savefig(fname, bbox_inches="tight", dpi=self.dpi)

    def get_store(self) -> bool | int:
        """
        Retrieves the storage state from the singleton instance.

        Returns
        --------------------
        bool or int
            The storage state indicating whether saving is enabled.

        Examples
        --------------------
        >>> show_instance = Show()
        >>> print(show_instance.get_store())
        True
        """

        store: bool | int = self._store_singleton.store
        return store

    def show_fig(self) -> None:
        """
        Displays the current figure if `show` is True.

        Examples
        --------------------
        >>> show_instance = Show(show=True)
        >>> show_instance.show_fig()
        """
        if self.show:
            plt.show()


@bind_passed_params()
def show(
    fname: str = "gsplot",
    ft_list: list[str] = ["png", "pdf"],
    dpi: float = 600,
    show: bool = True,
    *args: Any,
    **kwargs: Any,
) -> None:
    """
    A convenience function to save and optionally display a Matplotlib figure.

    This function wraps the `Show` class for easier access and management of figure
    saving and displaying.

    Parameters
    --------------------
    fname : str, optional
        The base name for saved figure files (default is "gsplot").
    ft_list : list of str, optional
        A list of file formats for saving the figure (default is ["png", "pdf"]).
    dpi : float, optional
        The resolution (dots per inch) for saving the figure (default is 600).
    show : bool, optional
        Whether to display the figure (default is True).
    *args : Any
        Additional positional arguments passed to `plt.savefig`.
    **kwargs : Any
        Additional keyword arguments passed to `plt.savefig`.

    Notes
    --------------------
    This function utilizes the `ParamsGetter` to retrieve bound parameters and
    the `CreateClassParams` class to handle the merging of default, configuration,
    and passed parameters.

    Examples
    --------------------
    >>> import gsplot as gs
    >>> gs.show(fname="example", ft_list=["png", "jpg"], dpi=300, show=True)
    """
    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    class_params = CreateClassParams(passed_params).get_class_params()

    _show: Show = Show(
        class_params["fname"],
        class_params["ft_list"],
        class_params["dpi"],
        class_params["show"],
        *class_params["args"],
        **class_params["kwargs"],
    )

    _show.store_fig()
    _show.show_fig()
