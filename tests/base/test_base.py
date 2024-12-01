from unittest.mock import MagicMock, patch

import pytest

from gsplot.base.base import AttributeSetter

# from gsplot.params.params import Params, LoadParams

# class TestAttributeSetter:
#
#     @pytest.fixture
#     def attribute_setter(self):
#         return AttributeSetter()
#
#     def test_get_default_values(self, attribute_setter):
#         class TestClass:
#             def __init__(self, param1="default1", param2="default2"):
#                 pass
#
#         defaults = attribute_setter.get_default_values(TestClass())
#         assert defaults == {"param1": "default1", "param2": "default2"}
#
#     def test_get_params_from_config(self, attribute_setter):
#         # This test will depend on your configuration and Params class
#         pass
#
#     def test_update_current_values(self, attribute_setter):
#         class TestClass:
#             def __init__(self):
#                 self.param1 = None
#                 self.param2 = None
#
#         obj = TestClass()
#         attribute_setter.update_current_values(
#             obj, {"param1": "value1", "param2": "value2"}
#         )
#         assert obj.param1 == "value1"
#         assert obj.param2 == "value2"
#
#     def test_get_kwargs(self, attribute_setter):
#         kwargs = {"param1": "value1", "param2": "value2"}
#         defaults = {"param1": "default1", "param2": "default2"}
#         params = {"param1": "param_value1", "param3": "param_value3"}
#         result = attribute_setter.get_kwargs(kwargs, defaults, params)
#         assert result == {"param3": "param_value3"}


class TestAttributeSetter:

    @pytest.fixture
    def attribute_setter(self):
        return AttributeSetter()

    @pytest.fixture
    def mock_obj(self):
        class MockObject:
            def __init__(self, a=1, b=2):
                self.a = a
                self.b = b

        return MockObject()

    def test_get_default_values(self, attribute_setter, mock_obj):
        defaults = attribute_setter.get_default_values(mock_obj)
        assert defaults == {"a": 1, "b": 2}

    @patch("gsplot.params.params.LoadParams")
    @patch("gsplot.params.params.Params")
    def test_get_params_from_config(
        self, mock_params_class, mock_load_params, attribute_setter
    ):
        mock_params_instance = MagicMock()
        mock_params_instance.get_item.return_value = {"a": 10, "b": 20}
        mock_params_class.return_value = mock_params_instance

        result = attribute_setter.get_params_from_config("test_key")

        mock_load_params().load_params.assert_called_once()
        assert result == {"a": 10, "b": 20}

    def test_update_current_values(self, attribute_setter, mock_obj):
        locals_dict = {"a": 5, "b": 10}
        attribute_setter.update_current_values(mock_obj, locals_dict)

        assert mock_obj.a == 5
        assert mock_obj.b == 10

    def test_get_kwargs(self, attribute_setter):
        kwargs = {"c": 3, "d": 4}
        defaults = {"a": 1, "b": 2}
        params = {"a": 10, "b": 20, "c": 30}

        result = attribute_setter.get_kwargs(kwargs, defaults, params)

        assert result == {"c": 3, "d": 4}

    @patch("gsplot.base.base.AttributeSetter.get_default_values")
    @patch("gsplot.base.base.AttributeSetter.get_params_from_config")
    @patch("gsplot.base.base.AttributeSetter.update_current_values")
    @patch("gsplot.base.base.AttributeSetter.get_kwargs")
    def test_set_attributes(
        self,
        mock_get_kwargs,
        mock_update_current_values,
        mock_get_params_from_config,
        mock_get_default_values,
        attribute_setter,
        mock_obj,
    ):
        mock_get_default_values.return_value = {"a": 1, "b": 2}
        mock_get_params_from_config.return_value = {"a": 10, "b": 20}
        mock_get_kwargs.return_value = {"c": 3, "d": 4}

        locals_dict = {"kwargs": {"c": 5, "d": 6}}
        key = "test_key"

        result = attribute_setter.set_attributes(mock_obj, locals_dict, key)

        mock_update_current_values.assert_called_once_with(mock_obj, locals_dict)
        mock_get_default_values.assert_called_once_with(mock_obj)
        mock_get_params_from_config.assert_called_once_with(key)
        mock_get_kwargs.assert_called_once_with(
            locals_dict["kwargs"], {"a": 1, "b": 2}, {"a": 10, "b": 20}
        )

        assert mock_obj.a == 10  # Updated from params
        assert mock_obj.b == 20  # Updated from params
        assert result == {"c": 5, "d": 6}
