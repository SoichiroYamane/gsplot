from typing import Any, Dict

import inspect
from ..params.params import Params, LoadParams


class AttributeSetter:
    """
    A class to handle setting attributes and parameters for objects using
    configuration values, defaults, and provided keyword arguments.

    Methods
    -------
    get_default_values(obj: Any) -> Dict[str, Any]
        Retrieves the default values of the parameters from the `__init__` method of the given object.

    get_params_from_config(key: str) -> Dict[str, Any]
        Loads parameters from a configuration based on a provided key.

    update_current_values(obj: Any, locals_dict: Dict[str, Any]) -> None
        Updates the attributes of the given object with values from `locals_dict`.

    get_kwargs(kwargs: Any, defaults: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]
        Filters and merges keyword arguments with defaults and parameters from the configuration.

    set_attributes(obj: Any, locals_dict: Dict[str, Any], key: str) -> Any
        Sets the attributes of the object using defaults, configuration parameters, and provided keyword arguments.
    """

    def get_default_values(self, obj: Any) -> Dict[str, Any]:
        """
        Retrieves the default values of the parameters from the `__init__` method of the given object.

        Parameters
        ----------
        obj : Any
            The object whose `__init__` method's parameter defaults are to be retrieved.

        Returns
        -------
        Dict[str, Any]
            A dictionary mapping parameter names to their default values.
        """
        sig = inspect.signature(obj.__init__)  # type: ignore
        defaults = {
            name: param.default
            for name, param in sig.parameters.items()
            if param.default is not inspect.Parameter.empty
        }  # type: ignore
        return defaults

    def get_params_from_config(self, key: str) -> Dict[str, Any]:
        """
        Loads parameters from a configuration based on a provided key.

        Parameters
        ----------
        key : str
            The key used to retrieve parameters from the configuration.

        Returns
        -------
        Dict[str, Any]
            A dictionary of parameters retrieved from the configuration.
        """
        LoadParams().load_params()
        params: Dict[str, Any] = Params().get_item(key)
        return params

    def update_current_values(self, obj: Any, locals_dict: Dict[str, Any]) -> None:
        """
        Updates the attributes of the given object with values from `locals_dict`.

        Parameters
        ----------
        obj : Any
            The object whose attributes are to be updated.
        locals_dict : Dict[str, Any]
            A dictionary containing local variables used to update the object's attributes.
        """
        obj.__dict__.update(locals_dict)

    def get_kwargs(
        self, kwargs: Any, defaults: Dict[str, Any], params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Filters and merges keyword arguments with defaults and parameters from the configuration.

        Parameters
        ----------
        kwargs : Any
            The keyword arguments passed to the function.
        defaults : Dict[str, Any]
            A dictionary of default values for the parameters.
        params : Dict[str, Any]
            A dictionary of parameters from the configuration.

        Returns
        -------
        Dict[str, Any]
            A dictionary of merged keyword arguments, excluding those present in defaults.
        """
        return {
            key: value
            for key, value in {**kwargs, **params}.items()
            if key not in defaults
        }

    def set_attributes(
        self,
        obj: Any,
        locals_dict: Dict[str, Any],
        key: str,
    ) -> Any:
        """
        Sets the attributes of the object using defaults, configuration parameters, and provided keyword arguments.

        Parameters
        ----------
        obj : Any
            The object whose attributes are to be set.
        locals_dict : Dict[str, Any]
            A dictionary containing local variables, including keyword arguments (`kwargs`), used to update the object's attributes.
        key : str
            The key used to retrieve parameters from the configuration.

        Returns
        -------
        Any
            The updated keyword arguments after merging with defaults and configuration parameters.
        """
        self.update_current_values(obj, locals_dict)
        defaults = self.get_default_values(obj)
        params = self.get_params_from_config(key)
        passed_kwargs = locals_dict["kwargs"]

        for key, default in defaults.items():
            current_value = obj.__dict__[key]
            if current_value != default:
                setattr(obj, key, current_value)
            elif key in params:
                setattr(obj, key, params[key])
            else:
                setattr(obj, key, default)

        kwargs = self.get_kwargs(locals_dict["kwargs"], defaults, params)
        kwargs.update(passed_kwargs)
        return kwargs
