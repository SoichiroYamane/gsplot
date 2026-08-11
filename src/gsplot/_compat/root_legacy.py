"""Small root-level adapters for legacy operations with no safe translation."""

from __future__ import annotations

import warnings
from typing import NoReturn

from .._core.errors import MetadataError


def save_metadata(*args: object, **kwargs: object) -> NoReturn:
    """Reject implicit metadata collection and direct callers to ``write_meta``."""

    del args, kwargs
    warnings.warn(
        "gsplot.save_metadata is deprecated; create a MetadataSnapshot and call "
        "gsplot.write_meta(snapshot, destination) explicitly",
        DeprecationWarning,
        stacklevel=2,
    )
    raise MetadataError(
        "implicit metadata collection is removed; use "
        "write_meta(MetadataSnapshot(...), destination)"
    )


__all__ = ["save_metadata"]
