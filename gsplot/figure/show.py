from typing import Any
import matplotlib.pyplot as plt

from .store import StoreSingleton
from ..base.base import bind_passed_params, ParamsGetter, CreateClassParams


class Show:

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

        if self.show:
            plt.show()

    def store_fig(self) -> None:

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

        store: bool | int = self._store_singleton.store
        return store


# TODO: Modify docstring
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
    Save and optionally display a Matplotlib figure with customizable settings.

    This function saves the current Matplotlib figure to one or more file formats
    with the specified filename and resolution. It also optionally displays the
    figure in a graphical interface.

    Parameters
    ----------
    fname : str, optional
        The base filename to use when saving the figure. Default is "gsplot".
    ft_list : list[str], optional
        A list of file formats to save the figure in (e.g., ["png", "pdf"]). Default is ["png", "pdf"].
    dpi : float, optional
        The resolution of the saved figure in dots per inch (DPI). Default is 600.
    show : bool, optional
        If True, display the figure in a graphical interface after saving. Default is True.
    *args : Any
        Additional positional arguments passed to the save or display process.
    **kwargs : Any
        Additional keyword arguments for figure saving or display customization.

    Returns
    -------
    None
        This function does not return anything.

    Notes
    -----
    - The function uses the `Show` class to manage the figure saving and displaying processes.
    - Multiple file formats can be specified in `ft_list`, and the figure will be saved
      in each format with the specified filename and DPI.

    Examples
    --------
    Save the current figure as "output.png" and "output.pdf":

    >>> show(fname="output", ft_list=["png", "pdf"])

    Save the figure in high resolution (1200 DPI):

    >>> show(dpi=1200)

    Display the figure without saving it:

    >>> show(show=True, ft_list=[])

    Pass additional arguments for customization:

    >>> show(fname="plot", dpi=300, bbox_inches="tight")
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
