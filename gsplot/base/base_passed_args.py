import inspect
import numpy as np
from functools import update_wrapper
from typing import Callable
from typing_extensions import Any, Dict, TypedDict


class WrapperWithAttributes(TypedDict):
    passed_variables: dict[str, Any]


class GetPassedArgs:
    def __init__(self, func) -> None:
        update_wrapper(self, func)

        self.func = func
        self.passed_variables: Dict[str, Any] = {}

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        sig = inspect.signature(self.func)
        bound_args = sig.bind_partial(*args, **kwargs)
        bound_args.apply_defaults()
        self.passed_variables = {
            k: v
            for k, v in bound_args.arguments.items()
            if not isinstance(v, np.ndarray)
            and (v != sig.parameters[k].default)
            or (
                isinstance(v, np.ndarray) and not (v == sig.parameters[k].default).all()
            )
            or k in kwargs
        }
        return self.func(*args, **kwargs)


def get_passed_args(f: Callable) -> Callable:
    return GetPassedArgs(f)
