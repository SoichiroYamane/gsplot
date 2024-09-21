import inspect
import numpy as np
from functools import update_wrapper, wraps
from typing import Callable
from typing_extensions import Any, Dict, TypedDict

from typing import Callable, ParamSpec, TypeVar, Generic, Protocol


# class WrapperWithAttributes(TypedDict):
#     """
#     A TypedDict for storing attributes related to passed variables.
#
#     Attributes
#     ----------
#     passed_variables : dict[str, Any]
#         A dictionary mapping variable names to their corresponding passed values.
#     """
#
#     passed_variables: dict[str, Any]


# class GetPassedArgs:
#     def __init__(self, func: Callable) -> None:
#         self.func = func
#         self.passed_variables: dict[str, Any] = {}
#
#         # update_wrapper(self, func)
#         wraps(func)(self)
#
#     def __call__(self, *args: Any, **kwargs: Any) -> Any:
#         print("args", args)
#         print("kwargs", kwargs)
#
#         sig = inspect.signature(self.func)
#         bound_args = sig.bind_partial(*args, **kwargs)
#
#         print("bound_args", bound_args)
#         print("\n")
#         bound_args.apply_defaults()
#         self.passed_variables = {
#             k: v
#             for k, v in bound_args.arguments.items()
#             if not isinstance(v, np.ndarray)
#             and (v != sig.parameters[k].default)
#             or (
#                 isinstance(v, np.ndarray) and not (v == sig.parameters[k].default).all()
#             )
#             or k in kwargs
#         }
#         return self.func(*args, **kwargs)
#


def get_passed_args(f: Callable) -> None:
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
    pass


T = TypeVar("T")
P = ParamSpec("P")


class Command(Generic[P, T]):
    """
    A class that wraps a callable (function) and allows additional keyword arguments
    to be passed when the function is called.

    Attributes:
        function (Callable[P, T]): The function to be wrapped.
        kwargs (dict): Additional keyword arguments to be passed when calling the function.

    Methods:
        __call__(*args: P.args, **kwargs: P.kwargs) -> T:
            Calls the wrapped function with the provided arguments and keyword arguments.
    """

    def __init__(self, function: Callable[P, T], **kwargs) -> None:
        """
        Initializes the Command with a function and optional keyword arguments.

        Args:
            function (Callable[P, T]): The function to wrap.
            **kwargs: Additional keyword arguments to pass when the function is called.
        """
        self.function = function
        self.kwargs = kwargs

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        """
        Calls the wrapped function with the provided arguments and keyword arguments.

        Args:
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.

        Returns:
            T: The return value of the function.
        """
        return self.function(*args, **self.kwargs)


# def to_command(**kwargs):
#     """
#     A decorator that wraps a function in a Command class, passing additional
#     keyword arguments to the Command instance.
#
#     Args:
#         **decorator_kwargs: Keyword arguments to pass to the Command class.
#
#     Returns:
#         Callable: A decorator that wraps the function with Command.
#     """
#
#     def wrapped(func: Callable) -> Command:
#         wraps(func)
#
#         def wrapper(*args, **kwargs):
#             return Command(func, **kwargs)
#
#         return wrapper
#
#     return wrapped


def to_command(**decorator_kwargs):
    """
    A decorator that wraps a function in a Command class, passing additional
    keyword arguments to the Command instance.

    Args:
        **decorator_kwargs: Keyword arguments to pass to the Command class.

    Returns:
        Callable: A decorator that wraps the function with Command.
    """

    def wrapped(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return Command(func, **decorator_kwargs)

        return wrapper

    return wrapped


# In the class that sphinx should be documenting:
@to_command(name="foo", description="bar")
def foo_bar(self, *, name: str, description: str) -> None:
    """
    A method that does something with a name and a description.

    Args:
        name (str): The name to process.
        description (str): The description associated with the name.

    Returns:
        None
    """
    pass
