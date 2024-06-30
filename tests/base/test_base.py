import pytest
from gsplot.base.base import AttributeSetter


class TestAttributeSetter:
    class TestClass:
        pass

    def setup_method(self):
        self.defaults = {"a": 1, "b": 2}
        self.params = {"a": 3}
        self.kwargs = {"b": 4}
        self.test_obj = self.TestClass()
        self.attribute_setter = AttributeSetter(
            self.defaults, self.params, **self.kwargs
        )

    def test_set_attributes(self):
        extra_attributes = self.attribute_setter.set_attributes(self.test_obj)

        assert (
            self.test_obj.a == 3  # type: ignore
        ), "The 'a' attribute should be set to the value from params"
        assert (
            self.test_obj.b == 4  # type: ignore
        ), "The 'b' attribute should be set to the value from kwargs"
        assert extra_attributes == {}, "There should be no extra attributes"

    def test_set_attributes_with_extra_kwargs(self):
        self.kwargs = {"b": 4, "c": 5}
        self.attribute_setter = AttributeSetter(
            self.defaults, self.params, **self.kwargs
        )
        extra_attributes = self.attribute_setter.set_attributes(self.test_obj)

        assert (
            self.test_obj.a == 3  # type: ignore
        ), "The 'a' attribute should be set to the value from params"
        assert (
            self.test_obj.b == 4  # type: ignore
        ), "The 'b' attribute should be set to the value from kwargs"
        assert extra_attributes == {
            "c": 5
        }, "The 'c' attribute should be in the extra attributes"
