from typing import List, Union

import matplotlib.pyplot as plt

from ..params.params import Params
from ..base.base import AttributeSetter
from .store import StoreSingleton


# TODO: fix main
class Show:

    def __init__(
        self,
        *args,
        **kwargs,
    ):

        self.name: str = "gsplot"
        self.ft_list: List[str] = ["png", "pdf"]
        self.dpi: float = 600
        self.show: bool = True

        defaults = {
            "name": self.name,
            "ft_list": self.ft_list,
            "dpi": self.dpi,
            "show": self.show,
        }

        params: dict = Params().getitem("show")

        attribute_setter: AttributeSetter = AttributeSetter(defaults, params, **kwargs)

        self._args = args
        self._kwargs: dict = attribute_setter.set_attributes(self)

        self.__store: StoreSingleton = StoreSingleton()

        # run main
        self.main()

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
                        *self._args,
                        **self._kwargs,
                    )

            except Exception as e:
                print(f"Exception: {e}")
                for fname in fname_list:
                    plt.savefig(fname, bbox_inches="tight", dpi=self.dpi)

    def _get_store(self) -> Union[bool, int]:
        store: Union[bool, int] = self.__store.store
        return store

    def main(self) -> None:
        self._store_fig()
