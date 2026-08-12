"""One explicit NumPy text-to-array adapter."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from os import PathLike
from typing import Any, Literal, cast

import numpy as np
from numpy.typing import DTypeLike, NDArray

from .._core.errors import DataError

Loader = Literal["genfromtxt", "loadtxt"]


def _path(value: str | PathLike[str], *, operation: str) -> str | PathLike[str]:
    """Validate one explicit path-like loader input."""

    if not isinstance(value, (str, PathLike)) or (
        isinstance(value, str) and not value.strip()
    ):
        raise DataError(f"{operation}: path must be a non-empty path-like value")
    return value


def _loader(value: Any, *, operation: str) -> Loader:
    """Validate one supported NumPy text loader name."""

    if not isinstance(value, str) or value not in {"genfromtxt", "loadtxt"}:
        raise DataError(f"{operation}: loader must be 'genfromtxt' or 'loadtxt'")
    return cast(Loader, value)


def _load(
    path: str | PathLike[str],
    *,
    loader: Loader,
    ndmin: int,
    options: Mapping[str, Any],
    operation: str,
) -> NDArray[Any] | list[NDArray[Any]]:
    """Call one selected loader and preserve its native result shape."""

    try:
        loader_function: Any = np.genfromtxt if loader == "genfromtxt" else np.loadtxt
        loaded = loader_function(path, ndmin=ndmin, **dict(options))
    except (OSError, TypeError, ValueError, UnicodeError) as exc:
        raise DataError(f"{operation}: could not read the supplied path") from exc
    return cast(NDArray[Any] | list[NDArray[Any]], loaded)


def read_array(
    path: str | PathLike[str],
    *,
    loader: Literal["genfromtxt", "loadtxt"] = "genfromtxt",
    ndmin: int = 1,
    options: Mapping[str, Any] | None = None,
) -> NDArray[Any] | list[NDArray[Any]]:
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
    numpy.ndarray or list of numpy.ndarray
        Native loader result. Structured dtype with ``unpack=True`` may return
        separate field arrays with different dtypes.

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

    selected_path = _path(path, operation="read_array")
    selected_loader = _loader(loader, operation="read_array")
    if isinstance(ndmin, bool) or not isinstance(ndmin, int) or ndmin < 1:
        raise DataError(
            "read_array: ndmin must be an integer greater than or equal to 1"
        )
    if options is None:
        selected_options: dict[str, Any] = {}
    else:
        if not isinstance(options, Mapping):
            raise DataError("read_array: options must be a mapping")
        if any(not isinstance(key, str) for key in options):
            raise DataError("read_array: options keys must be strings")
        reserved = sorted(set(options) & {"loader", "ndmin", "fname"})
        if reserved:
            joined = ", ".join(repr(key) for key in reserved)
            raise DataError(
                f"read_array: options cannot contain reserved key(s): {joined}"
            )
        selected_options = dict(options)
    return _load(
        selected_path,
        loader=selected_loader,
        ndmin=ndmin,
        options=selected_options,
        operation="read_array",
    )


def _text_option(value: Any, name: str) -> str | None:
    """Validate a concise delimiter or comment marker."""

    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise DataError(f"read: {name} must be non-empty text or None")
    return value


def _usecols(value: Any) -> int | tuple[int, ...] | None:
    """Validate one finite concise column selection."""

    if value is None:
        return None
    if type(value) is int:
        return value
    if isinstance(value, (str, bytes)):
        raise DataError("read: usecols must be an integer or integer sequence")
    if not isinstance(value, Sequence):
        raise DataError("read: usecols must be an integer or integer sequence")
    selected = tuple(value)
    if not selected or any(type(item) is not int for item in selected):
        raise DataError("read: usecols must contain one or more integers")
    return cast(tuple[int, ...], selected)


def read(
    path: str | PathLike[str],
    *,
    loader: Literal["genfromtxt", "loadtxt"] = "genfromtxt",
    delimiter: str | None = ",",
    comments: str | None = "#",
    skip_header: int = 0,
    usecols: int | Sequence[int] | None = None,
    unpack: bool = True,
    ndmin: Literal[0, 1, 2] = 1,
    dtype: DTypeLike = float,
) -> NDArray[Any] | list[NDArray[Any]]:
    """Read comma-delimited columns with finite NumPy text options.

    Parameters
    ----------
    path
        Explicit text file path. The current working directory is unchanged.
    loader
        NumPy loader name: ``"genfromtxt"`` or ``"loadtxt"``.
    delimiter
        Field delimiter, defaulting to ``,`` for CSV. Use ``None`` for
        whitespace-delimited input.
    comments
        Comment marker, defaulting to ``"#"``. Use ``None`` to disable it.
    skip_header
        Non-negative number of initial lines to skip, defaulting to ``0``.
    usecols
        Optional integer column or finite integer column sequence.
    unpack
        Return columns or structured fields separately, defaulting to ``True``.
    ndmin
        Minimum result dimensions: ``0``, ``1`` (default), or ``2``.
    dtype
        NumPy-compatible dtype, defaulting to ``float``.

    Returns
    -------
    numpy.ndarray or list of numpy.ndarray
        Native NumPy loader result. Structured unpacking returns a list of
        per-field arrays and preserves their individual dtypes.

    Raises
    ------
    DataError
        If a control, path, dtype, or file content is invalid.

    Notes
    -----
    ``skip_header`` maps to ``skiprows`` for ``loadtxt``. Use
    :func:`gsplot.read_array` for less common NumPy loader options.

    Examples
    --------
    >>> import gsplot as gs
    >>> columns = gs.read("data.csv", skip_header=1, usecols=(0, 2))
    >>> len(columns) >= 1
    True
    """

    selected_path = _path(path, operation="read")
    selected_loader = _loader(loader, operation="read")
    selected_delimiter = _text_option(delimiter, "delimiter")
    selected_comments = _text_option(comments, "comments")
    if type(skip_header) is not int or skip_header < 0:
        raise DataError("read: skip_header must be a non-negative integer")
    selected_usecols = _usecols(usecols)
    if not isinstance(unpack, bool):
        raise DataError("read: unpack must be a boolean")
    if type(ndmin) is not int or ndmin not in {0, 1, 2}:
        raise DataError("read: ndmin must be 0, 1, or 2")
    try:
        np.dtype(dtype)
    except (TypeError, ValueError) as exc:
        raise DataError("read: dtype must be NumPy-compatible") from exc
    if selected_loader == "loadtxt" and (
        selected_delimiter is not None and len(selected_delimiter) != 1
    ):
        raise DataError("read: loadtxt delimiter must be one character or None")

    options: dict[str, Any] = {
        "delimiter": selected_delimiter,
        "comments": selected_comments,
        "usecols": selected_usecols,
        "unpack": unpack,
        "dtype": dtype,
    }
    options["skip_header" if selected_loader == "genfromtxt" else "skiprows"] = (
        skip_header
    )
    return _load(
        selected_path,
        loader=selected_loader,
        ndmin=ndmin,
        options=options,
        operation="read",
    )


__all__ = ["read", "read_array"]
