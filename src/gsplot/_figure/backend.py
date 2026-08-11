"""Explicit Matplotlib backend selection."""

from __future__ import annotations

import sys

from .._core.errors import LayoutError
from .._core.validation import ensure_nonempty_text


def use_backend(name: str) -> None:
    """Select a Matplotlib backend before pyplot or a figure is initialized.

    Parameters
    ----------
    name
        Backend name accepted by Matplotlib.

    Raises
    ------
    LayoutError
        If pyplot has already been imported, the name is invalid, or Matplotlib
        rejects the backend.
    """

    backend = ensure_nonempty_text(name, "backend", error=LayoutError)
    if "matplotlib.pyplot" in sys.modules:
        raise LayoutError("use_backend must be called before pyplot is imported")
    pylab_helpers = sys.modules.get("matplotlib._pylab_helpers")
    if pylab_helpers is not None:
        managers = getattr(pylab_helpers, "Gcf", None)
        if managers is not None and managers.get_all_fig_managers():
            raise LayoutError(
                "use_backend must be called before a managed Matplotlib Figure exists"
            )

    try:
        import matplotlib

        matplotlib.use(backend)
    except Exception as exc:
        raise LayoutError(f"could not select Matplotlib backend {backend!r}") from exc


__all__ = ["use_backend"]
