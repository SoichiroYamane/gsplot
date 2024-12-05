from __future__ import annotations

import threading

__all__: list[str] = []


class StoreSingleton:
    """
    A thread-safe singleton class for managing a shared storage state.

    This class ensures that a single instance is used to manage the storage state
    across an application. The storage state can be a boolean or an integer (0 or 1),
    providing flexibility for different use cases.

    Attributes
    --------------------
    store : bool or int
        The current storage state, which can be either a boolean or an integer (0 or 1).

    Methods
    --------------------
    store
        Retrieves the current storage state.
    store(value)
        Sets the storage state to a boolean or an integer (0 or 1).

    Examples
    --------------------
    >>> singleton = StoreSingleton()
    >>> print(singleton.store)
    False  # Default value

    >>> singleton.store = True
    >>> print(singleton.store)
    True

    >>> singleton.store = 1
    >>> print(singleton.store)
    1

    >>> singleton.store = "invalid"  # Raises ValueError
    Traceback (most recent call last):
        ...
    ValueError: Store must be a boolean or integer.
    """

    _instance: StoreSingleton | None = None
    _lock: threading.Lock = threading.Lock()  # Lock to ensure thread safety

    def __new__(cls) -> "StoreSingleton":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(StoreSingleton, cls).__new__(cls)
                cls._instance._initialize_store()
        return cls._instance

    def _initialize_store(self) -> None:
        """
        Initializes the storage state to its default value (False).
        """
        # Explicitly initialize the instance variable with a type hint
        self._store: bool | int = False

    @property
    def store(self) -> bool | int:
        """
        Retrieves the current storage state.

        Returns
        --------------------
        bool or int
            The current storage state.

        Examples
        --------------------
        >>> singleton = StoreSingleton()
        >>> print(singleton.store)
        False
        """
        return self._store

    @store.setter
    def store(self, value: bool | int) -> None:
        """
        Sets the storage state.

        Parameters
        --------------------
        value : bool or int
            The new storage state. Must be a boolean or an integer (0 or 1).

        Raises
        --------------------
        ValueError
            If the value is not a boolean or integer, or if an integer is not 0 or 1.

        Examples
        --------------------
        >>> singleton = StoreSingleton()
        >>> singleton.store = True
        >>> print(singleton.store)
        True

        >>> singleton.store = 1
        >>> print(singleton.store)
        1

        >>> singleton.store = "invalid"  # Raises ValueError
        Traceback (most recent call last):
            ...
        ValueError: Store must be a boolean or integer.
        """
        if not isinstance(value, (bool, int)):
            raise ValueError("Store must be a boolean or integer.")
        if isinstance(value, int) and value not in [0, 1]:
            raise ValueError("Store must be 0 or 1 if integer.")

        self._store = value
