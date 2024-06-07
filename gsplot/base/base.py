class AttributeSetter:
    def __init__(self, keys, defaults, params, **kwargs):
        self.keys = keys
        self.defaults = defaults
        self.params = params
        self.kwargs = kwargs

    def set_attributes(self, obj):
        for key, default in zip(self.keys, self.defaults):
            if key in self.kwargs:
                setattr(obj, key, self.kwargs[key])
            elif key in self.params:
                setattr(obj, key, self.params[key])
            elif key in self.keys:
                setattr(obj, key, default)

        # return keywards without default values
        return {
            key: value for key, value in self.kwargs.items() if key not in self.keys
        }
