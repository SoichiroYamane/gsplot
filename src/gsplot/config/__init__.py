"""Deprecated forwarding package for legacy configuration modules."""

from .._compat.shim import load_legacy, module_dir

_implementation = load_legacy("gsplot._compat.legacy.config", __name__)
__all__ = tuple(getattr(_implementation, "__all__", ()))


def __getattr__(name: str):
    return getattr(_implementation, name)


def __dir__():
    return module_dir(_implementation, globals())
