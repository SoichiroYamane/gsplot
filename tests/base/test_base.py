import pytest
from gsplot.base.base import AttributeSetter


class TestAttributeSetter:

    @pytest.fixture
    def attribute_setter(self):
        return AttributeSetter()

    def test_get_default_values(self, attribute_setter):
        class TestClass:
            def __init__(self, param1="default1", param2="default2"):
                pass

        defaults = attribute_setter.get_default_values(TestClass())
        assert defaults == {"param1": "default1", "param2": "default2"}

    def test_get_params_from_config(self, attribute_setter):
        # This test will depend on your configuration and Params class
        pass

    def test_update_current_values(self, attribute_setter):
        class TestClass:
            def __init__(self):
                self.param1 = None
                self.param2 = None

        obj = TestClass()
        attribute_setter.update_current_values(
            obj, {"param1": "value1", "param2": "value2"}
        )
        assert obj.param1 == "value1"
        assert obj.param2 == "value2"

    def test_get_kwargs(self, attribute_setter):
        kwargs = {"param1": "value1", "param2": "value2"}
        defaults = {"param1": "default1", "param2": "default2"}
        params = {"param1": "param_value1", "param3": "param_value3"}
        result = attribute_setter.get_kwargs(kwargs, defaults, params)
        assert result == {"param3": "param_value3"}
