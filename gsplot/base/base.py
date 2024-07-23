from typing import Any, Dict

import inspect
from ..params.params import Params, LoadParams


# class AttributeSetter:
#     def __init__(
#         self, defaults: Dict[str, Any], params: Dict[str, Any], **kwargs: Any
#     ) -> None:
#         self.defaults: Dict[str, Any] = defaults
#         self.params: Dict[str, Any] = params
#         self.kwargs: Dict[str, Any] = kwargs
#
#     def set_attributes(self, obj: Any) -> Dict[str, Any]:
#         for key, default in self.defaults.items():
#             if key in self.kwargs:
#                 setattr(obj, key, self.kwargs[key])
#             elif key in self.params:
#                 setattr(obj, key, self.params[key])
#             else:
#                 setattr(obj, key, default)
#
#         return {
#             key: value
#             for key, value in {**self.kwargs, **self.params}.items()
#             if key not in self.defaults
#         }


class AttributeSetter:
    def get_default_values(self, obj: Any) -> Dict[str, Any]:
        sig = inspect.signature(obj.__init__)  # type: ignore
        defaults = {
            name: param.default
            for name, param in sig.parameters.items()
            if param.default is not inspect.Parameter.empty
        }  # type: ignore
        return defaults

    def get_params_from_config(self, key: str) -> Dict[str, Any]:
        LoadParams().load_params()
        params: Dict[str, Any] = Params().get_item(key)
        return params

    def update_current_values(self, obj: Any, locals_dict: Dict[str, Any]) -> None:
        obj.__dict__.update(locals_dict)

    def get_kwargs(
        self, kwargs: Any, defaults: Dict[str, Any], params: Dict[str, Any]
    ) -> Dict[str, Any]:
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

        self.update_current_values(obj, locals_dict)
        defaults = self.get_default_values(obj)
        params = self.get_params_from_config(key)

        for key, default in defaults.items():
            current_value = obj.__dict__[key]
            if current_value != default:
                setattr(obj, key, current_value)
            elif key in params:
                setattr(obj, key, params[key])
            else:
                setattr(obj, key, default)

        kwargs = self.get_kwargs(locals_dict["kwargs"], defaults, params)
        return kwargs
