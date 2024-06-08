from ..params.params import Params
from ..base.base import AttributeSetter

from .axes import _Axes
from .store import Store

import matplotlib.pyplot as plt


class Show:
    """
    A class used to manage the display and storage of a plot.

    ...

    Attributes
    ----------
    _kwargs : dict
        a dictionary of keyword arguments passed to the class
    args : tuple
        a tuple of positional arguments passed to the class
    __store : Store
        an instance of the Store class
    __axes : _Axes
        an instance of the _Axes class

    Methods
    -------
    _store_fig():
        Stores the figure in the specified file types if the store flag is set.
    main():
        Executes the main functionality of the class.
    """

    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """
        Constructs all the necessary attributes for the Show object.

        Parameters
        ----------
            args : tuple
                a tuple of positional arguments
            kwargs : dict
                a dictionary of keyword arguments
        """

        defaults = {
            "name": "gsplot",
            "ft_list": ["png", "pdf"],
            "dpi": 600,
            "show": True,
        }

        params = Params().getitem("show")

        attribute_setter = AttributeSetter(defaults, params, **kwargs)

        self._args = args
        self._kwargs = attribute_setter.set_attributes(self)

        self.__store = Store()
        self.__axes = _Axes()

        # run main
        self.main()

        if self.show:
            plt.show()

    def _store_fig(self):
        """
        Stores the figure in the specified file types if the store flag is set.

        Parameters
        ----------
            None
        """

        if self.__store.store:
            # save figure
            fname_list = [f"{self.name}.{ft}" for ft in self.ft_list]

            try:
                for fname in fname_list:
                    plt.savefig(
                        fname,
                        bbox_inches="tight",
                        dpi=self.dpi,
                        *self._args,
                        **self._kwargs,
                    )
            except:
                for fname in fname_list:
                    plt.savefig(fname, bbox_inches="tight", dpi=self.dpi)

    def main(self):
        """
        Executes the main functionality of the class. This includes storing the figure if the store flag is set.

        Parameters
        ----------
            None
        """

        self._store_fig()
