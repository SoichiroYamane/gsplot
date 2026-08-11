import inspect
from typing import Any

from ..config.config import Config

__all__: list[str] = []


class AliasValidator:
    """
    Validates alias mappings for function parameters and configuration options.

    This class ensures that aliased parameters do not conflict with their original keys
    in both function arguments and configuration entries. If an alias and its original
    key are used simultaneously, an error is raised.

    Parameters
    --------------------
    alias_map : dict of str, Any
        A mapping of alias keys to their original parameter keys.
    passed_params : dict of str, Any
        The parameters explicitly passed to the function, including `kwargs`.

    Attributes
    --------------------
    wrapped_func_name : str
        The name of the wrapped function where the validation is performed.
    alias_map : dict of str, Any
        The mapping of alias keys to original parameter keys.
    passed_params : dict of str, Any
        The explicitly passed parameters, updated during validation.
    config_entry_option : dict of str, Any
        Configuration options for the wrapped function.

    Methods
    --------------------
    get_wrapped_func_name()
        Retrieves the name of the wrapped function.
    get_config_entry_option()
        Retrieves the configuration options for the wrapped function.
    check_duplicate_kwargs()
        Checks and resolves conflicts between alias keys and their original keys
        in both `passed_params` and `config_entry_option`.
    validate()
        Performs the full validation by checking for duplicate aliases and resolving conflicts.

    Examples
    --------------------
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
        """
        Retrieves the name of the wrapped function.

        Returns
        --------------------
        str
            The name of the wrapped function.

        Raises
        --------------------
        Exception
            If the current frame or its ancestors cannot be accessed.
        """
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
        """
        Retrieves the configuration options for the wrapped function.

        Returns
        --------------------
        dict of str, Any
            The configuration options for the wrapped function.
        """
        config_entry_option: dict[str, Any] = Config().get_config_entry_option(
            self.wrapped_func_name
        )
        return config_entry_option

    def check_duplicate_kwargs(self):
        """
        Checks and resolves conflicts between alias keys and their original keys
        in both `passed_params` and `config_entry_option`.

        Raises
        --------------------
        ValueError
            If an alias and its original key are used simultaneously in the
            function call or configuration file.
        """

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
        """
        Performs the full validation by checking for duplicate aliases
        and resolving conflicts in `passed_params` and `config_entry_option`.
        """
        self.check_duplicate_kwargs()
