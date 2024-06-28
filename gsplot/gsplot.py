from .figure.axes import AxesHandler


def axes(*args, **kwargs):
    __axes = AxesHandler(*args, **kwargs)
    return __axes.get_axes
