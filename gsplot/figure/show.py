from typing import List, Union, Any

import matplotlib.pyplot as plt

from ..base.base import AttributeSetter
from .store import StoreSingleton


class Show:

    def __init__(
        self,
        name: str = "gsplot",
        ft_list: List[str] = ["png", "pdf"],
        dpi: float = 600,
        show: bool = True,
        *args: Any,
        **kwargs: Any,
    ):

        self.name: str = name
        self.ft_list: List[str] = ft_list
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

        if self._get_store():
            # save figure
            fname_list: List[str] = [f"{self.name}.{ft}" for ft in self.ft_list]

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
        store: Union[bool, int] = self.__store.store
        return store


def show(
    fname: str = "gsplot",
    ft_list: List[str] = ["png", "pdf"],
    dpi: float = 600,
    show: bool = True,
    *args: Any,
    **kwargs: Any,
) -> None:
    _show = Show(fname, ft_list, dpi, show, *args, **kwargs)
    _show._store_fig()
