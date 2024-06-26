from .plts.axes import Axes


def axes(*args, **kwargs):
    __axes = Axes(*args, **kwargs)
    return __axes.get_axes
