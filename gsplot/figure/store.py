from typing import Union


class StoreSingleton:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StoreSingleton, cls).__new__(cls)
            cls._instance._initialize_store()
        return cls._instance

    def _initialize_store(self) -> None:
        # Explicitly initialize the instance variable with a type hint
        self._store: Union[bool, int] = False

    @property
    def store(self) -> Union[bool, int]:
        return self._store

    @store.setter
    def store(self, value: Union[bool, int]) -> None:
        if not isinstance(value, (bool, int)):
            raise ValueError("Store must be a boolean or integer.")
        if isinstance(value, int) and value not in [0, 1]:
            raise ValueError("Store must be 0 or 1 if integer.")
        self._store = value
