"""Deprecated forwarding shim for ``gsplot.config.config``."""

from .._compat.shim import forwarded_attr, load_legacy, module_dir

_implementation = load_legacy("gsplot._compat.legacy.config.config", __name__)
__all__ = tuple(getattr(_implementation, "__all__", ()))


def __getattr__(name: str):
    return forwarded_attr(_implementation, name, __all__)


def __dir__():
    return module_dir(_implementation, globals())
