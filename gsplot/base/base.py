from typing import Any, Dict


class AttributeSetter:
    def __init__(self, defaults: Dict[str, Any], params: Dict[str, Any], **kwargs: Any):
        self.defaults: Dict[str, Any] = defaults
        self.params: Dict[str, Any] = params
        self.kwargs: Dict[str, Any] = kwargs

    def set_attributes(self, obj: Any) -> Dict[str, Any]:
        for key, default in self.defaults.items():
            if key in self.kwargs:
                setattr(obj, key, self.kwargs[key])
            elif key in self.params:
                setattr(obj, key, self.params[key])
            else:
                setattr(obj, key, default)

        return {
            key: value
            for key, value in {**self.kwargs, **self.params}.items()
            if key not in self.defaults
        }
