from typing import Union


class StoreSingleton:
    """
    A singleton class used to manage a store flag.

    ...

    Attributes
    ----------
    _instance : StoreSingleton
        the single instance of the StoreSingleton class
    _store : bool or int
        a flag indicating whether to store or not

    Methods
    -------
    store:
        Property that gets or sets the _store attribute.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Creates a new instance of the StoreSingleton class if one does not already exist.
        """
        if cls._instance is None:
            cls._instance = super(StoreSingleton, cls).__new__(cls)
            cls._instance._store = False
        return cls._instance

    @property
    def store(self):
        """
        Gets the _store attribute.

        Returns
        -------
        bool or int
            The store flag.
        """
        return self._instance._store

    @store.setter
    def store(self, store: Union[bool, int]):
        """
        Sets the _store attribute.

        Parameters
        ----------
        store : bool or int
            The new store flag.

        Raises
        ------
        ValueError
            If store is not a boolean or 0 or 1.
        """
        if not isinstance(store, (bool, int)) or store not in [0, 1]:
            raise ValueError("Store must be a boolean or 0 or 1.")
        self._instance._store = store
