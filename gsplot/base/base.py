from typing import Any, Dict, Callable
from functools import wraps
import numpy as np

import inspect

from ..config.config import Config


class GetPassedParams:
    def __init__(self, func: Callable, *args, **kwargs) -> None:
        self.func = func
        self.passed_params: dict[str, Any] = {}
        self.args = args
        self.kwargs = kwargs

    def count_default_params(self, bound_arguments: dict[str, Any]) -> int:
        filtered_bound_arguments = {
            k: v for k, v in bound_arguments.items() if k not in ["args", "kwargs"]
        }
        return len(filtered_bound_arguments)

    def create_passed_args(self, bound_arguments: dict[str, Any]) -> dict[str, Any]:
        args_len = len(self.args)
        default_params_len = self.count_default_params(bound_arguments)
        # directly iterate over dictionary items without kwargs key
        passed_args = {
            k: v
            for i, (k, v) in enumerate(bound_arguments.items())
            if i < args_len and i < default_params_len
        }
        passed_args["args"] = bound_arguments.get("args", [])
        return passed_args

    def crete_passed_kwargs(self, bound_arguments: dict[str, Any]) -> dict[str, Any]:
        passed_kwargs = {k: v for k, v in bound_arguments.items() if k in self.kwargs}

        passed_kwargs["kwargs"] = bound_arguments.get("kwargs", {})
        return passed_kwargs

    def get_passed_params(self) -> dict[str, Any]:
        sig = inspect.signature(self.func)
        self.sig = sig
        bound_args = sig.bind_partial(*self.args, **self.kwargs)
        bound_args.apply_defaults()

        bound_arguments = bound_args.arguments

        passe_args = self.create_passed_args(bound_arguments)
        passed_kwargs = self.crete_passed_kwargs(bound_arguments)

        passed_params = {**passe_args, **passed_kwargs}

        self.passed_params = passed_params
        return self.passed_params


# class CreateClassParams:
#     def __init__(self, func: Callable, passed_params: dict[str, Any]) -> None:
#         self.func: Callable = func
#         self.passed_params: dict[str, Any] = passed_params
#
#         self.default_params = self.get_default_params()
#         self.config_entry_params = self.get_config_entry_params(self.func.__name__)
#
#     def get_default_params(self) -> dict[str, Any]:
#         sig = inspect.signature(self.func)
#         default_params = {
#             name: param.default
#             for name, param in sig.parameters.items()
#             if param.default is not inspect.Parameter.empty
#         }
#         default_params = default_params
#         return default_params
#
#     def get_config_entry_params(self, key: str) -> dict[str, Any]:
#         config_entry_option: dict[str, Any] = Config().get_config_entry_option(key)
#
#         # decompose the config_entry_option following the structure of defaults_params
#         config_entry_params = {
#             key: config_entry_option[key]
#             for key in config_entry_option
#             if key in self.default_params
#         }
#
#         config_entry_params["kwargs"] = {
#             key: value
#             for key, value in config_entry_option.items()
#             if key not in self.default_params
#         }
#         return config_entry_params
#
#     def get_class_params(self) -> dict[str, Any]:
#         defaults_params = self.default_params
#         config_entry_params = self.config_entry_params
#         passed_params = self.passed_params
#
#         class_params = {
#             **defaults_params,
#             **config_entry_params,
#             **passed_params,
#         }
#
#         class_params["kwargs"] = {
#             **config_entry_params.get("kwargs", {}),
#             **passed_params.get("kwargs", {}),
#         }
#         return class_params


class CreateClassParams:
    def __init__(self, passed_params: dict[str, Any]) -> None:
        self.passed_params: dict[str, Any] = passed_params

        self.wrapped_func_frame = self.get_wrapped_func_frame()
        self.wrapped_func_name: str = self.get_wrapped_func_name()
        self.wrapped_func: Callable = self.get_wrapped_func()

        self.default_params: dict[str, Any] = self.get_default_params()
        self.config_entry_params: dict[str, Any] = self.get_config_entry_params()
        # print("default", self.default_params)
        # print("config", self.config_entry_params)

    def get_wrapped_func_frame(self):
        current_frame = inspect.currentframe()

        if (
            not current_frame
            or not current_frame.f_back
            or not current_frame.f_back.f_back
        ):
            raise Exception("Cannot get current frame")

        wrapped_func_frame = current_frame.f_back.f_back
        return wrapped_func_frame

    def get_wrapped_func_name(self) -> str:
        wrapped_func_name = self.wrapped_func_frame.f_code.co_name
        return wrapped_func_name

    def get_wrapped_func(self) -> Callable:
        wrapped_func = self.wrapped_func_frame.f_globals[self.wrapped_func_name]
        return wrapped_func

    def get_default_params(self) -> dict[str, Any]:
        sig = inspect.signature(self.wrapped_func)
        default_params = {
            name: param.default
            for name, param in sig.parameters.items()
            if param.default is not inspect.Parameter.empty
        }
        return default_params

    def get_config_entry_params(self) -> dict[str, Any]:
        config_entry_option: dict[str, Any] = Config().get_config_entry_option(
            self.wrapped_func_name
        )

        # decompose the config_entry_option following the structure of defaults_params
        config_entry_params = {
            key: config_entry_option[key]
            for key in config_entry_option
            if key in self.default_params
        }

        config_entry_params["kwargs"] = {
            key: value
            for key, value in config_entry_option.items()
            if key not in self.default_params
        }
        return config_entry_params

    def get_class_params(self) -> dict[str, Any]:
        defaults_params = self.default_params
        config_entry_params = self.config_entry_params
        passed_params = self.passed_params

        class_params = {
            **defaults_params,
            **config_entry_params,
            **passed_params,
        }
        class_params["kwargs"] = {
            **config_entry_params.get("kwargs", {}),
            **passed_params.get("kwargs", {}),
        }
        return class_params


def get_passed_params() -> Callable:
    def wrapped(func: Callable) -> Callable:

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # get passed parameters from the function call wrapped by the decorator
            passed_params = GetPassedParams(func, *args, **kwargs).get_passed_params()
            setattr(wrapper, "passed_params", passed_params)

            # get class parameters obtained from default values, configuration, and passed parameters to a class object
            # class_params = CreateClassParams(func, passed_params).get_class_params()
            # setattr(wrapper, "class_params", class_params)

            return func(*args, **kwargs)

        return wrapper

    return wrapped


class AttributeSetter:
    def set_attributes(self, obj, local_vars, key: str):
        pass


# class ParamsVerifier:
#     def __init__(
#         self, list_of_params: list[dict[str, Any] | None],
#     ) -> None:
#         self.passed_params = passed_params
#         self.class_params = class_params
#
#     def verify(self) -> tuple[dict[str, Any], dict[str, Any]]:
#         if self.passed_params is None:
#             raise ValueError("Passed params is None")
#         if self.class_params is None:
#             raise ValueError("Class params is None")
#         return self.passed_params, self.class_params


# class ParamsVerifier:
#     def __init__(
#         self,
#         *args: dict[str, Any] | None,
#     ):
#         self.args = args
#
#     def verify(self) -> tuple[dict[str, Any], ...]:
#         for arg in self.args:
#             if arg is None:
#                 raise ValueError("Passed params is None")
#         return self.args


# class ParamsVerifier:
#     def __init__(self, *args: dict[str, Any] | None):
#         self.args = args
#
#     def verify(self) -> tuple[dict[str, Any], ...]:
#         # return tuple of verified arguments without None
#         verified_args = tuple(arg for arg in self.args if arg is not None)
#         if len(verified_args) != len(self.args):
#             raise ValueError("Passed params contains None")
#         return verified_args


class ParamsGetter:
    def __init__(self, var: str) -> None:
        self.var = var

    def get_wrapped_frame(self):
        current_frame = inspect.currentframe()
        if (
            not current_frame
            or not current_frame.f_back
            or not current_frame.f_back.f_back
        ):
            raise Exception("Cannot get current frame")
        wrapped_frame = current_frame.f_back.f_back
        return wrapped_frame

    def verify(self, params: dict[str, Any] | None) -> dict[str, Any]:
        if params is None:
            raise ValueError("Params is None")
        return params

    def get_params(self) -> dict[str, Any]:
        wrapped_frame = self.get_wrapped_frame()
        wrapped_func_name = wrapped_frame.f_code.co_name
        func = wrapped_frame.f_globals[wrapped_func_name]

        params: dict[str, Any] | None = getattr(func, self.var, None)
        params = self.verify(params)
        return params
