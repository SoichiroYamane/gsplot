from typing import Any
import inspect

from ..config.config import Config


class AliasValidator:
    """
    A class for validating aliases on passed_params.

    Examples

    --------
    >>> @bind_passed_params()
    >>> def example_func(p1, p2, p3):
    >>>     passed_params: dict[str, Any] = ParamsGetter(
    >>>      "passed_params"
    >>>     ).get_bound_params()
    >>> AliasValidator(alias_map, passed_params).validate()
    >>> class_params: dict[str, Any] = CreateClassParams(passed_params).get_class_params()
    """

    def __init__(
        self,
        alias_map: dict[str, Any],
        passed_params: dict[str, Any],
    ) -> None:
        self.wrapped_func_name: str = self.get_wrapped_func_name()

        self.alias_map: dict[str, Any] = alias_map
        self.passed_params: dict[str, Any] = passed_params
        self.config_entry_option: dict[str, Any] = self.get_config_entry_option()

    def get_wrapped_func_name(self) -> str:
        current_frame = inspect.currentframe()

        # Ensure that the frames to the wrapped function can be accessed.
        if (
            not current_frame
            or not current_frame.f_back
            or not current_frame.f_back.f_back
        ):
            raise Exception("Cannot get current frame")

        wrapped_func_frame = current_frame.f_back.f_back

        wrapped_func_name = wrapped_func_frame.f_code.co_name
        return wrapped_func_name

    def get_config_entry_option(self) -> dict[str, Any]:
        config_entry_option: dict[str, Any] = Config().get_config_entry_option(
            self.wrapped_func_name
        )
        return config_entry_option

    def check_duplicate_kwargs(self):
        def checker_passed_params():
            for alias, key in self.alias_map.items():
                if alias in self.passed_params["kwargs"]:
                    if key in self.passed_params:
                        raise ValueError(
                            f"The parameters '{alias}' and '{key}' cannot both be used simultaneously in the '{self.wrapped_func_name}' function."
                        )
                    self.passed_params[key] = self.passed_params["kwargs"][alias]
                    del self.passed_params["kwargs"][alias]

        def checker_config_entry_option(config_entry_option: dict[str, Any]):
            for alias, key in self.alias_map.items():
                if alias in config_entry_option:
                    if key in config_entry_option:
                        raise ValueError(
                            f"The parameters '{alias}' and '{key}' cannot both be used simultaneously in the '{self.wrapped_func_name}' in the configuration file."
                        )
                    Config().config_dict[self.wrapped_func_name][key] = (
                        config_entry_option[alias]
                    )
                    del Config().config_dict[self.wrapped_func_name][alias]

        # Check for duplicate kwargs in passed_params and config_entry_option
        checker_passed_params()
        checker_config_entry_option(self.config_entry_option)

    def validate(self):
        self.check_duplicate_kwargs()
