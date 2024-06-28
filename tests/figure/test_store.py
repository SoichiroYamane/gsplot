import pytest
from typing import Any
from gsplot.figure.store import StoreSingleton


class TestStoreSingleton:

    def test_store_property_initial_value(self):
        store_instance = StoreSingleton()
        assert store_instance.store is False  # Initial value should be False

    def test_store_property_setter(self):
        store_instance = StoreSingleton()

        store_instance.store = True
        assert store_instance.store is True

        store_instance.store = 1
        assert store_instance.store == 1

        store_instance.store = False
        assert store_instance.store is False

        store_instance.store = 0
        assert store_instance.store == 0

    def test_store_property_setter_invalid_value(self):
        store_instance = StoreSingleton()

        self._assign_invalid_value(store_instance, "invalid_value")
        self._assign_invalid_value(store_instance, 2)

    @staticmethod
    def _assign_invalid_value(instance: StoreSingleton, value: Any) -> None:
        with pytest.raises(ValueError):
            instance.store = value
