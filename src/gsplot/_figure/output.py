"""Explicit Figure saving and display primitives."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from os import PathLike
from pathlib import Path
from typing import Any

from matplotlib.figure import Figure

from .._core.errors import OutputError

_FORMATS = frozenset({"png", "pdf", "svg"})
_SAVEFIG_PROPS = frozenset(
    {
        "bbox_extra_artists",
        "bbox_inches",
        "edgecolor",
        "facecolor",
        "orientation",
        "papertype",
        "pad_inches",
        "pil_kwargs",
        "transparent",
    }
)
_CONTROLLED_PROPS = frozenset(
    {"path", "format", "formats", "dpi", "close", "create_parent", "overwrite", "show"}
)


def _validate_bool(value: Any, name: str) -> bool:
    """Validate a strict boolean control."""

    if not isinstance(value, bool):
        raise OutputError(f"{name} must be a boolean")
    return value


def _resolved_path(value: str | PathLike[str], name: str) -> Path:
    """Resolve one caller-owned path without consulting script state."""

    if not isinstance(value, (str, PathLike)):
        raise OutputError(f"{name} must be a path-like value")
    if isinstance(value, str) and not value.strip():
        raise OutputError(f"{name} must not be empty")
    try:
        return Path(value).expanduser().resolve()
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise OutputError(f"could not resolve {name}") from exc


def _formats(
    path: Path,
    formats: str | Sequence[str] | None,
) -> tuple[tuple[str, ...], tuple[Path, ...]]:
    """Validate format/suffix compatibility and derive output paths."""

    suffix = path.suffix.lower().lstrip(".")
    selected: tuple[str, ...]
    if formats is None:
        selected = (suffix,) if suffix else ("png",)
    elif isinstance(formats, str):
        selected = (formats.lower().lstrip("."),)
    elif isinstance(formats, Sequence) and not isinstance(formats, (bytes, str)):
        selected = tuple(formats)
    else:
        raise OutputError("formats must be a format string or non-empty sequence")
    if not selected or any(not isinstance(item, str) or not item for item in selected):
        raise OutputError("formats must be a non-empty sequence of strings")
    selected = tuple(item.lower().lstrip(".") for item in selected)
    if len(set(selected)) != len(selected):
        raise OutputError("formats must not contain duplicates")
    unsupported = sorted(set(selected) - _FORMATS)
    if unsupported:
        raise OutputError(f"unsupported output format(s): {', '.join(unsupported)}")
    if suffix and (len(selected) != 1 or selected[0] != suffix):
        raise OutputError("a suffixed path requires exactly its matching format")
    if suffix:
        destinations: tuple[Path, ...] = (path.with_suffix(f".{selected[0]}"),)
    else:
        destinations = tuple(path.with_suffix(f".{item}") for item in selected)
    return selected, destinations


def _save_props(props: Mapping[str, Any] | None) -> dict[str, Any]:
    """Validate a closed Matplotlib savefig property mapping."""

    if props is None:
        return {}
    if not isinstance(props, Mapping):
        raise OutputError("props must be a mapping")
    if any(not isinstance(key, str) for key in props):
        raise OutputError("props keys must be strings")
    duplicate = sorted(set(props) & _CONTROLLED_PROPS)
    if duplicate:
        joined = ", ".join(repr(key) for key in duplicate)
        raise TypeError(f"props cannot contain gsplot-controlled key(s): {joined}")
    unknown = sorted(set(props) - _SAVEFIG_PROPS)
    if unknown:
        joined = ", ".join(repr(key) for key in unknown)
        raise OutputError(f"savefig props contains unknown key(s): {joined}")
    return dict(props)


def show(fig: Figure) -> None:
    """Display only an explicitly supplied managed Figure.

    A manager-backed non-interactive Figure is a documented no-display
    success.  A Figure without a manager raises ``OutputError`` instead of
    invoking pyplot and exposing unrelated Figures.
    """

    if not isinstance(fig, Figure):
        raise OutputError("fig must be a Matplotlib Figure")
    if getattr(fig.canvas, "manager", None) is None:
        raise OutputError("display requires a managed Figure; use show=False")
    try:
        fig.show(warn=False)
    except Exception as exc:
        raise OutputError("could not display the supplied Figure") from exc


def savefig(
    fig: Figure,
    path: str | PathLike[str],
    *,
    formats: str | Sequence[str] | None = None,
    dpi: float | None = None,
    close: bool = False,
    create_parent: bool = False,
    overwrite: bool = False,
    show: bool = True,
    props: Mapping[str, Any] | None = None,
) -> tuple[Path, ...]:
    """Save an explicit Figure and optionally display it after all writes."""

    if not isinstance(fig, Figure):
        raise OutputError("fig must be a Matplotlib Figure")
    close_value = _validate_bool(close, "close")
    create_parent_value = _validate_bool(create_parent, "create_parent")
    overwrite_value = _validate_bool(overwrite, "overwrite")
    show_value = _validate_bool(show, "show")
    if close_value and show_value:
        raise OutputError("close=True and show=True are mutually exclusive")
    if dpi is not None:
        if isinstance(dpi, bool):
            raise OutputError("dpi must be a positive finite number")
        try:
            dpi_value = float(dpi)
        except (TypeError, ValueError) as exc:
            raise OutputError("dpi must be a positive finite number") from exc
        if not math.isfinite(dpi_value) or dpi_value <= 0:
            raise OutputError("dpi must be a positive finite number")
        dpi = dpi_value
    selected_props = _save_props(props)
    destination = _resolved_path(path, "path")
    selected_formats, destinations = _formats(destination, formats)
    parents = {item.parent for item in destinations}
    for parent in parents:
        if parent.exists() and not parent.is_dir():
            raise OutputError(f"output parent is not a directory: {parent}")
        if not parent.exists() and not create_parent_value:
            raise OutputError(f"output parent does not exist: {parent}")
    if not overwrite_value:
        existing = [item for item in destinations if item.exists()]
        if existing:
            raise OutputError(f"output already exists: {existing[0]}")
    if create_parent_value:
        try:
            for parent in parents:
                parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise OutputError("could not create an output parent directory") from exc
    written: list[Path] = []
    for destination_path, selected_format in zip(destinations, selected_formats):
        try:
            fig.savefig(
                destination_path,
                format=selected_format,
                dpi=dpi,
                **selected_props,
            )
        except Exception as exc:
            written_text = ", ".join(str(item) for item in written) or "none"
            raise OutputError(
                f"could not save {destination_path} as {selected_format}; "
                f"written paths: {written_text}"
            ) from exc
        written.append(destination_path)
    result = tuple(written)
    if show_value:
        try:
            display = globals()["show"]
            display(fig)
        except OutputError as exc:
            written_text = ", ".join(str(item) for item in result)
            raise OutputError(
                f"saved paths but could not display the Figure: {written_text}"
            ) from exc
    if close_value:
        try:
            from matplotlib import pyplot as plt

            plt.close(fig)
        except Exception as exc:
            raise OutputError("saved the Figure but could not close it") from exc
    return result


__all__ = ["savefig", "show"]
