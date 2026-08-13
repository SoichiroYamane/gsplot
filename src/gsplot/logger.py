"""Deprecated, side-effect-free forwarding shim for historical logging."""

from ._compat.shim import forwarded_attr, load_legacy, module_dir

_implementation = load_legacy("gsplot._compat.legacy.logger", __name__)
__all__ = ("logger",)


def __getattr__(name: str):
    return forwarded_attr(_implementation, name, __all__)


def __dir__():
    return module_dir(_implementation, globals())
