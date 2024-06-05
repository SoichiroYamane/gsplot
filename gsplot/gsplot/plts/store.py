from typing import Union


class Store:
    """
    Store class to manage the saving of plots.

    Attributes
    ----------
    store : bool or int (0 or 1)
        If True or 1, save the plot to a file. If False or 0, do not save the plot. Default is False.
    """

    _store = None

    def __init__(self, store: Union[bool, int] = False):
        """
        Parameters
        ----------
        store : bool or int (0 or 1), optional
            If True or 1, save the plot to a file. If False or 0, do not save the plot. Default is False.
        """
        self.store = store

    @property
    def store(self):
        return Store._store

    @store.setter
    def store(self, store: Union[bool, int]):
        if not isinstance(store, (bool, int)) or store not in [0, 1]:
            raise ValueError("Store must be a boolean or 0 or 1.")
        Store._store = store


if __name__ == "__main__":
    store = Store(1)
    print(store.store)
