from typing import Union


class StoreSingleton:
    """
    A singleton class for managing a shared store state, which can be either a boolean or an integer.

    This class is designed to maintain a single shared instance that controls whether certain operations
    (like saving a figure) should be performed. The store state can be either a boolean or an integer (0 or 1).

    Attributes
    ----------
    _instance : StoreSingleton
        The singleton instance of the class.
    _store : Union[bool, int]
        The current store state, which determines whether an operation should be performed.

    Methods
    -------
    store -> Union[bool, int]
        Gets the current store state.
    store(value: Union[bool, int]) -> None
        Sets the store state to a new value.
    """

    _instance = None

    def __new__(cls) -> "StoreSingleton":
        if cls._instance is None:
            cls._instance = super(StoreSingleton, cls).__new__(cls)
            cls._instance._initialize_store()
        return cls._instance

    def _initialize_store(self) -> None:
        """
        Initializes the store state to a default value.

        The store state is initialized to `False`, indicating that by default, the operation should not be performed.
        """

        # Explicitly initialize the instance variable with a type hint
        self._store: Union[bool, int] = False

    @property
    def store(self) -> Union[bool, int]:
        """
        Gets the current store state.

        Returns
        -------
        Union[bool, int]
            The current store state, which is either a boolean or an integer (0 or 1).
        """

        return self._store

    @store.setter
    def store(self, value: Union[bool, int]) -> None:
        """
        Sets the store state to a new value.

        Parameters
        ----------
        value : Union[bool, int]
            The new value for the store state, which must be either a boolean or an integer (0 or 1).

        Raises
        ------
        ValueError
            If the value is not a boolean or integer, or if an integer value is not 0 or 1.
        """

        if not isinstance(value, (bool, int)):
            raise ValueError("Store must be a boolean or integer.")
        if isinstance(value, int) and value not in [0, 1]:
            raise ValueError("Store must be 0 or 1 if integer.")

        self._store = value
