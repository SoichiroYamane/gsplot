import inspect
import numpy as np
from functools import update_wrapper
from typing import Callable
from typing_extensions import Any, Dict, TypedDict


class WrapperWithAttributes(TypedDict):
    """
    A TypedDict for storing attributes related to passed variables.

    Attributes
    ----------
    passed_variables : dict[str, Any]
        A dictionary mapping variable names to their corresponding passed values.
    """

    passed_variables: dict[str, Any]


class GetPassedArgs:
    """
    A decorator class that captures and stores arguments passed to a function,
    excluding those that match the function's default values, unless they are numpy arrays.

    Parameters
    ----------
    func : Callable
        The function to be decorated.

    Attributes
    ----------
    func : Callable
        The function to be called.
    passed_variables : Dict[str, Any]
        A dictionary storing the names and values of passed arguments that differ
        from the function's default values, with special handling for numpy arrays.

    Methods
    -------
    __call__(*args: Any, **kwargs: Any) -> Any
        Calls the decorated function and captures the arguments that were passed.
    """

    def __init__(self, func) -> None:
        """
        Initializes the GetPassedArgs decorator with the provided function.

        Parameters
        ----------
        func : Callable
            The function to be decorated.
        """

        update_wrapper(self, func)

        self.func = func
        self.passed_variables: Dict[str, Any] = {}

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Calls the decorated function and captures the arguments that were passed,
        excluding those that match the function's default values.

        Parameters
        ----------
        *args : Any
            Positional arguments to be passed to the function.
        **kwargs : Any
            Keyword arguments to be passed to the function.

        Returns
        -------
        Any
            The result of the function call.
        """

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
    """
    A decorator function that wraps the provided function with GetPassedArgs.

    Parameters
    ----------
    f : Callable
        The function to be wrapped.

    Returns
    -------
    Callable
        The wrapped function, which captures passed arguments.
    """
    return GetPassedArgs(f)
