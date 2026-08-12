"""One explicit NumPy text-to-array adapter."""

from __future__ import annotations

from collections.abc import Mapping
from os import PathLike
from pathlib import Path
from typing import Any, Literal, cast

import numpy as np
from numpy.typing import NDArray

from .._core.errors import DataError

Loader = Literal["genfromtxt", "loadtxt"]


def read_array(
    path: str | PathLike[str],
    *,
    loader: Loader = "genfromtxt",
    ndmin: int = 1,
    options: Mapping[str, Any] | None = None,
) -> NDArray[Any]:
    """Read a text array without changing the process working directory.

    ``options`` is passed to the selected NumPy loader after the two gsplot
    controls are validated.  In particular, ``unpack`` and structured-array
    options retain NumPy's documented behavior.

    Parameters
    ----------
    path
        Text file to read.  The current working directory is not changed.
    loader
        NumPy loader name: ``"genfromtxt"`` or ``"loadtxt"``.
    ndmin
        Minimum number of dimensions passed to NumPy.
    options
        Finite mapping of options for the selected NumPy loader.

    Returns
    -------
    numpy.ndarray
        The loader result converted to an independent ndarray view/value.

    Raises
    ------
    DataError
        If the path, loader controls, options, or file contents are invalid.

    Examples
    --------
    >>> import gsplot as gs
    >>> array = gs.read_array("data.txt", loader="genfromtxt")
    >>> array.ndim >= 1
    True
    """

    if not isinstance(path, (str, PathLike)) or (
        isinstance(path, str) and not path.strip()
    ):
        raise DataError("path must be a non-empty path-like value")
    if loader not in {"genfromtxt", "loadtxt"}:
        raise DataError("loader must be 'genfromtxt' or 'loadtxt'")
    if isinstance(ndmin, bool) or not isinstance(ndmin, int) or ndmin < 1:
        raise DataError("ndmin must be an integer greater than or equal to 1")
    if options is None:
        selected_options: dict[str, Any] = {}
    else:
        if not isinstance(options, Mapping):
            raise DataError("options must be a mapping")
        if any(not isinstance(key, str) for key in options):
            raise DataError("options keys must be strings")
        reserved = sorted(set(options) & {"loader", "ndmin", "fname"})
        if reserved:
            joined = ", ".join(repr(key) for key in reserved)
            raise DataError(f"options cannot contain reserved key(s): {joined}")
        selected_options = dict(options)
    try:
        loader_function: Any = np.genfromtxt if loader == "genfromtxt" else np.loadtxt
        loaded = loader_function(path, ndmin=ndmin, **selected_options)
    except (OSError, TypeError, ValueError) as exc:
        raise DataError(f"could not read array from {Path(path)}") from exc
    return cast(NDArray[Any], np.asarray(loaded))


__all__ = ["read_array"]
