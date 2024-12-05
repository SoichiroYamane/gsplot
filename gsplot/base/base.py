import inspect
from functools import wraps
from typing import Any, Callable

from ..config.config import Config

__all__: list[str] = []


class GetPassedParams:
    """
    A utility class to capture and process the arguments passed to a function.

    This class binds the provided arguments and keyword arguments to the
    signature of the target function, identifies explicitly passed arguments,
    and separates them from default values.

    Parameters
    --------------------
    func : Callable
        The target function whose parameters are to be captured and processed.
    *args : tuple
        Positional arguments passed to the target function.
    **kwargs : dict
        Keyword arguments passed to the target function.

    Attributes
    --------------------
    func : Callable
        The target function whose parameters are being analyzed.
    passed_params : dict of str, Any
        A dictionary containing explicitly passed arguments and keyword arguments.
    args : Any
        Positional arguments passed to the target function.
    kwargs : Any
        Keyword arguments passed to the target function.
    sig : inspect.Signature
        The signature of the target function.

    Methods
    --------------------
    count_default_params(bound_arguments)
        Counts the number of arguments that have default values.
    create_passed_args(bound_arguments)
        Creates a dictionary of explicitly passed positional arguments.
    crete_passed_kwargs(bound_arguments)
        Creates a dictionary of explicitly passed keyword arguments.
    get_passed_params()
        Binds the arguments to the function's signature and retrieves explicitly passed parameters.

    Examples
    --------------------
    >>> def example_function(a, b=2, *args, **kwargs):
    ...     pass
    >>> obj = GetPassedParams(example_function, 1, 3, c=4)
    >>> params = obj.get_passed_params()
    >>> print(params)
    {'a': 1, 'args': [3], 'kwargs': {'c': 4}}
    """

    def __init__(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        self.func: Callable = func
        self.passed_params: dict[str, Any] = {}
        self.args: Any = args
        self.kwargs: Any = kwargs

    def count_default_params(self, bound_arguments: dict[str, Any]) -> int:
        """
        Counts the number of arguments with default values in the bound arguments.

        Parameters
        --------------------
        bound_arguments : dict of str, Any
            The arguments bound to the function's signature.

        Returns
        --------------------
        int
            The count of arguments with default values.
        """
        filtered_bound_arguments = {
            k: v for k, v in bound_arguments.items() if k not in ["args", "kwargs"]
        }
        return len(filtered_bound_arguments)

    def create_passed_args(self, bound_arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Creates a dictionary of explicitly passed positional arguments.

        Parameters
        --------------------
        bound_arguments : dict of str, Any
            The arguments bound to the function's signature.

        Returns
        --------------------
        dict of str, Any
            A dictionary containing the explicitly passed positional arguments.
        """
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
        """
        Creates a dictionary of explicitly passed keyword arguments.

        Parameters
        --------------------
        bound_arguments : dict of str, Any
            The arguments bound to the function's signature.

        Returns
        --------------------
        dict of str, Any
            A dictionary containing the explicitly passed keyword arguments.
        """
        passed_kwargs = {k: v for k, v in bound_arguments.items() if k in self.kwargs}

        passed_kwargs["kwargs"] = bound_arguments.get("kwargs", {})
        return passed_kwargs

    def get_passed_params(self) -> dict[str, Any]:
        """
        Retrieves the explicitly passed parameters after binding them to the function's signature.

        Returns
        --------------------
        dict of str, Any
            A dictionary containing the explicitly passed arguments and keyword arguments.

        Examples
        --------------------
        >>> def example_function(a, b=2, *args, **kwargs):
        ...     pass
        >>> obj = GetPassedParams(example_function, 1, 3, c=4)
        >>> params = obj.get_passed_params()
        >>> print(params)
        {'a': 1, 'args': [3], 'kwargs': {'c': 4}}
        """
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


class CreateClassParams:
    """
    A utility class to construct parameters for a class by combining default parameters,
    configuration entries, and explicitly passed parameters.

    Parameters
    --------------------
    passed_params : dict of str, Any
        The explicitly passed parameters.

    Attributes
    --------------------
    passed_params : dict of str, Any
        The explicitly passed parameters.
    wrapped_func_frame : frame
        The frame of the wrapped function.
    wrapped_func_name : str
        The name of the wrapped function.
    wrapped_func : Callable
        The wrapped function itself.
    default_params : dict of str, Any
        Default parameters extracted from the wrapped function's signature.
    config_entry_params : dict of str, Any
        Parameters from the configuration entry for the wrapped function.

    Methods
    --------------------
    get_wrapped_func_frame()
        Retrieves the frame of the wrapped function.
    get_wrapped_func_name()
        Retrieves the name of the wrapped function.
    get_wrapped_func()
        Retrieves the wrapped function.
    get_default_params()
        Extracts default parameters from the wrapped function's signature.
    get_config_entry_params()
        Retrieves parameters from the configuration entry corresponding to the wrapped function.
    get_class_params()
        Constructs the final parameters for the class by merging default, configuration, and passed parameters.

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

    def __init__(self, passed_params: dict[str, Any]) -> None:
        self.passed_params: dict[str, Any] = passed_params

        self.wrapped_func_frame = self.get_wrapped_func_frame()
        self.wrapped_func_name: str = self.get_wrapped_func_name()
        self.wrapped_func: Callable = self.get_wrapped_func()

        self.default_params: dict[str, Any] = self.get_default_params()
        self.config_entry_params: dict[str, Any] = self.get_config_entry_params()

    def get_wrapped_func_frame(self):
        """
        Retrieves the frame of the wrapped function.

        Returns
        --------------------
        frame
            The frame of the wrapped function.

        Raises
        --------------------
        Exception
            If the current frame or its ancestors cannot be retrieved.
        """
        current_frame = inspect.currentframe()

        if (
            not current_frame
            or not current_frame.f_back
            or not current_frame.f_back.f_back
        ):
            raise Exception("Cannot get current frame")

        wrapped_func_frame = current_frame.f_back.f_back
        return wrapped_func_frame

    def get_wrapped_func_name(self) -> Any:
        """
        Retrieves the name of the wrapped function.

        Returns
        --------------------
        str
            The name of the wrapped function.
        """
        wrapped_func_name = self.wrapped_func_frame.f_code.co_name
        return wrapped_func_name

    def get_wrapped_func(self) -> Any:
        """
        Retrieves the wrapped function.

        Returns
        --------------------
        Callable
            The wrapped function.
        """
        wrapped_func = self.wrapped_func_frame.f_globals[self.wrapped_func_name]
        return wrapped_func

    def get_default_params(self) -> dict[str, Any]:
        """
        Extracts default parameters from the wrapped function's signature.

        Returns
        --------------------
        dict of str, Any
            A dictionary of default parameters.
        """
        sig = inspect.signature(self.wrapped_func)
        default_params = {
            name: param.default
            for name, param in sig.parameters.items()
            if param.default is not inspect.Parameter.empty
        }
        return default_params

    def get_config_entry_params(self) -> dict[str, Any]:
        """
        Retrieves parameters from the configuration entry for the wrapped function.

        Returns
        --------------------
        dict of str, Any
            A dictionary of configuration entry parameters, with non-default
            parameters grouped under a "kwargs" key.
        """
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
        """
        Constructs the final parameters for the class by merging default parameters,
        configuration entry parameters, and explicitly passed parameters.

        Returns
        --------------------
        dict of str, Any
            A dictionary of the final class parameters.
        """
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


def bind_passed_params() -> Callable:
    """
    A decorator to bind and store the parameters passed to a function call.

    This decorator captures the parameters passed to the decorated function
    (including positional arguments, keyword arguments, and their default values)
    and attaches them to the decorated function as an attribute named `passed_params`.

    Returns
    --------------------
    Callable
        A decorator that wraps a function to capture its passed parameters.

    Examples
    --------------------
    >>> @bind_passed_params()
    >>> def example_func(p1, p2, p3):
    >>>     passed_params: dict[str, Any] = ParamsGetter(
    >>>      "passed_params"
    >>>     ).get_params_from_wrapper()
    """

    def wrapped(func: Callable) -> Callable:
        """
        Wraps the target function to capture passed parameters.

        Parameters
        --------------------
        func : Callable
            The function to be wrapped.

        Returns
        --------------------
        Callable
            The wrapped function with an attached `passed_params` attribute.
        """

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            """
            Captures passed parameters and executes the original function.

            Parameters
            --------------------
            *args : tuple
                Positional arguments passed to the function.
            **kwargs : dict
                Keyword arguments passed to the function.

            Returns
            --------------------
            Any
                The result of the original function call.
            """

            # get passed parameters from the function call wrapped by the decorator
            passed_params = GetPassedParams(func, *args, **kwargs).get_passed_params()
            setattr(wrapper, "passed_params", passed_params)
            return func(*args, **kwargs)

        return wrapper

    return wrapped


class ParamsGetter:
    """
    A utility class to retrieve bound parameters from a wrapped function.

    This class accesses a specified attribute of a wrapped function and verifies
    the parameters, ensuring they are not `None`.

    Parameters
    --------------------
    var : str
        The name of the attribute containing the parameters to retrieve.

    Attributes
    --------------------
    var : str
        The name of the target attribute in the wrapped function.

    Methods
    --------------------
    get_wrapped_frame()
        Retrieves the frame of the wrapped function.
    verify(params)
        Verifies that the provided parameters are not `None`.
    get_bound_params()
        Retrieves and verifies the bound parameters from the wrapped function.

    Examples
    --------------------
    >>> @bind_passed_params()
    >>> def example_func(p1, p2, p3):
    >>>     passed_params: dict[str, Any] = ParamsGetter(
    >>>      "passed_params"
    >>>     ).get_bound_params()
    """

    def __init__(self, var: str) -> None:
        self.var: str = var

    def get_wrapped_frame(self):
        """
        Retrieves the frame of the wrapped function.

        Returns
        --------------------
        frame
            The frame of the wrapped function.

        Raises
        --------------------
        Exception
            If the current frame or its ancestors cannot be retrieved.
        """
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
        """
        Verifies that the provided parameters are not `None`.

        Parameters
        --------------------
        params : dict[str, Any] or None
            The parameters to verify.

        Returns
        --------------------
        dict[str, Any]
            The verified parameters.

        Raises
        --------------------
        ValueError
            If the provided parameters are `None`.
        """
        if params is None:
            raise ValueError("Params is None")
        return params

    def get_bound_params(self) -> dict[str, Any]:
        """
        Retrieves and verifies the bound parameters from the wrapped function.

        Returns
        --------------------
        dict[str, Any]
            The bound parameters retrieved from the wrapped function.

        Raises
        --------------------
        ValueError
            If the parameters are `None`.
        Exception
            If the wrapped function frame cannot be retrieved.
        """
        wrapped_frame = self.get_wrapped_frame()
        wrapped_func_name = wrapped_frame.f_code.co_name
        func = wrapped_frame.f_globals[wrapped_func_name]

        params: dict[str, Any] | None = getattr(func, self.var, None)
        params = self.verify(params)
        return params
