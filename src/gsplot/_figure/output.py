"""Explicit Figure saving and display primitives."""

from __future__ import annotations

import math
import os
import stat
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Any, cast

from matplotlib import rc_context
from matplotlib.backend_bases import FigureManagerBase
from matplotlib.figure import Figure

from .._core.errors import OptionError, OutputError, PlotError
from .._core.targets import normalize_axes
from .._core.types import AxesTarget

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


@dataclass(frozen=True, slots=True)
class _SavePlan:
    """Immutable preflight result for one concise save operation."""

    figure: Figure
    formats: tuple[str, ...]
    destinations: tuple[Path, ...]
    dpi: float
    crop: bool
    pad: float | None
    show: bool
    close: bool
    create_parent: bool
    overwrite: bool
    transparent: bool
    metadata: tuple[tuple[str, object], ...] | None


def _target_figure(target: Figure | AxesTarget, operation: str) -> Figure:
    """Resolve exactly one Figure without consulting pyplot current state."""

    if isinstance(target, Figure):
        return target
    try:
        return normalize_axes(target, operation=operation).figure
    except PlotError as exc:
        raise OutputError(
            f"{operation}: target must resolve to exactly one Matplotlib Figure"
        ) from exc


def _normalized_output_path(value: str | PathLike[str]) -> Path:
    """Normalize a final path while preserving its last component for lstat."""

    if not isinstance(value, (str, PathLike)):
        raise OutputError("save: path must be a path-like value")
    if isinstance(value, str) and not value.strip():
        raise OutputError("save: path must not be empty")
    try:
        candidate = Path(value).expanduser()
        if candidate.name in {"", ".", ".."}:
            raise OutputError("save: path must name an output file")
        parent = candidate.parent.resolve(strict=False)
    except OutputError:
        raise
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        raise OutputError("save: path could not be normalized") from exc
    return parent / candidate.name


def _format_name(value: object) -> str:
    """Normalize one output format without accepting path fragments."""

    if not isinstance(value, str) or not value:
        raise OutputError("save: formats must contain non-empty strings")
    selected = value.lower().lstrip(".")
    if not selected or "/" in selected or "\\" in selected:
        raise OutputError("save: a format must not contain a path separator")
    return selected


def _concise_formats(
    figure: Figure,
    path: Path,
    formats: str | Sequence[str] | None,
) -> tuple[tuple[str, ...], tuple[Path, ...]]:
    """Resolve canvas-supported formats and collision-free final paths."""

    try:
        supported = {
            str(name).lower() for name in figure.canvas.get_supported_filetypes()
        }
    except Exception as exc:
        raise OutputError("save: canvas output formats could not be inspected") from exc

    suffix = path.suffix.lstrip(".").lower()
    if suffix and suffix not in supported:
        raise OutputError("save: the output suffix is not supported by the canvas")
    selected: tuple[str, ...]
    if formats is None:
        selected = (suffix,) if suffix else ("png", "pdf")
    elif isinstance(formats, str):
        selected = (_format_name(formats),)
    elif isinstance(formats, Sequence) and not isinstance(formats, (bytes, str)):
        selected = tuple(_format_name(item) for item in formats)
    else:
        raise OutputError("save: formats must be a string or non-empty sequence")
    if not selected:
        raise OutputError("save: formats must not be empty")
    if len(set(selected)) != len(selected):
        raise OutputError("save: formats must be unique after normalization")
    if any(item not in supported for item in selected):
        raise OutputError("save: a requested format is not supported by the canvas")
    if suffix and (len(selected) != 1 or selected[0] != suffix):
        raise OutputError("save: a suffixed path requires exactly its matching format")

    destinations = (
        (path.with_suffix(f".{selected[0]}"),)
        if suffix
        else tuple(path.with_suffix(f".{item}") for item in selected)
    )
    if len(set(destinations)) != len(destinations):
        raise OutputError("save: requested formats resolve to duplicate paths")
    return selected, destinations


def _finite_positive(value: object, name: str) -> float:
    """Validate one positive finite output scalar."""

    if isinstance(value, bool):
        raise OutputError(f"save: {name} must be a positive finite number")
    try:
        selected = float(cast(Any, value))
    except (TypeError, ValueError) as exc:
        raise OutputError(f"save: {name} must be a positive finite number") from exc
    if not math.isfinite(selected) or selected <= 0:
        raise OutputError(f"save: {name} must be a positive finite number")
    return selected


def _metadata_items(
    metadata: Mapping[str, object] | None,
) -> tuple[tuple[str, object], ...] | None:
    """Snapshot string-keyed output metadata for an immutable plan."""

    if metadata is None:
        return None
    if not isinstance(metadata, Mapping) or any(
        not isinstance(key, str) for key in metadata
    ):
        raise OutputError("save: metadata must be a string-keyed mapping or None")
    return tuple(metadata.items())


def _existing_destination(path: Path, *, overwrite: bool) -> None:
    """Reject symlinks, non-regular targets, and forbidden replacement."""

    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return
    except OSError as exc:
        raise OutputError("save: an output target could not be inspected") from exc
    if stat.S_ISLNK(mode):
        raise OutputError("save: an output target must not be a symlink")
    if not stat.S_ISREG(mode):
        raise OutputError("save: an existing output target must be a regular file")
    if not overwrite:
        raise OutputError("save: an output target already exists")


def _save_plan(
    target: Figure | AxesTarget,
    path: str | PathLike[str],
    *,
    formats: str | Sequence[str] | None,
    dpi: float,
    crop: bool,
    pad: float | None,
    show: bool,
    close: bool,
    create_parent: bool,
    overwrite: bool,
    transparent: bool,
    metadata: Mapping[str, object] | None,
) -> _SavePlan:
    """Validate a complete concise save request before filesystem mutation."""

    figure = _target_figure(target, "save")
    controls = {
        "crop": crop,
        "show": show,
        "close": close,
        "create_parent": create_parent,
        "overwrite": overwrite,
        "transparent": transparent,
    }
    for name, value in controls.items():
        if not isinstance(value, bool):
            raise OutputError(f"save: {name} must be a boolean")
    if close and show:
        raise OutputError("save: close=True and show=True are mutually exclusive")
    dpi_value = _finite_positive(dpi, "dpi")
    pad_value: float | None
    if pad is not None:
        if not crop:
            raise OutputError("save: pad requires crop=True")
        if isinstance(pad, bool):
            raise OutputError("save: pad must be finite and non-negative")
        try:
            pad_value = float(pad)
        except (TypeError, ValueError) as exc:
            raise OutputError("save: pad must be finite and non-negative") from exc
        if not math.isfinite(pad_value) or pad_value < 0:
            raise OutputError("save: pad must be finite and non-negative")
    else:
        pad_value = 0.1 if crop else None

    destination = _normalized_output_path(path)
    selected_formats, destinations = _concise_formats(figure, destination, formats)
    parent = destination.parent
    if parent.exists():
        if not parent.is_dir():
            raise OutputError("save: output parent must be a directory")
        for item in destinations:
            _existing_destination(item, overwrite=overwrite)
    elif not create_parent:
        raise OutputError("save: output parent does not exist")

    return _SavePlan(
        figure=figure,
        formats=selected_formats,
        destinations=destinations,
        dpi=dpi_value,
        crop=crop,
        pad=pad_value,
        show=show,
        close=close,
        create_parent=create_parent,
        overwrite=overwrite,
        transparent=transparent,
        metadata=_metadata_items(metadata),
    )


def _prepare_output_parent(plan: _SavePlan) -> None:
    """Create an authorized parent and recheck every final destination."""

    parent = plan.destinations[0].parent
    if plan.create_parent:
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise OutputError("save: output parent could not be created") from exc
    if not parent.is_dir():
        raise OutputError("save: output parent must be a directory")
    for destination in plan.destinations:
        _existing_destination(destination, overwrite=plan.overwrite)


def _temporary_sibling(destination: Path) -> Path:
    """Create one unique regular temporary file beside a final destination."""

    name: str | None = None
    try:
        descriptor, name = tempfile.mkstemp(
            prefix=f".{destination.stem}-",
            suffix=f".tmp{destination.suffix}",
            dir=destination.parent,
        )
        os.close(descriptor)
    except OSError as exc:
        if name is not None:
            try:
                Path(name).unlink(missing_ok=True)
            except OSError:
                pass
        raise OutputError("save: a temporary output could not be created") from exc
    if name is None:  # pragma: no cover - mkstemp either returns or raises
        raise OutputError("save: a temporary output could not be created")
    return Path(name)


def _cleanup_temporaries(paths: Sequence[Path]) -> None:
    """Best-effort removal for private temporary outputs."""

    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def _render_outputs(plan: _SavePlan) -> tuple[Path, ...]:
    """Render every format to temporary siblings before any final replacement."""

    rendered: list[Path] = []
    save_options: dict[str, Any] = {
        "dpi": plan.dpi,
        "transparent": plan.transparent,
    }
    if plan.crop:
        save_options.update(bbox_inches="tight", pad_inches=plan.pad)
    if plan.metadata is not None:
        save_options["metadata"] = dict(plan.metadata)
    type42 = any(item in {"pdf", "ps"} for item in plan.formats)
    context = {"pdf.fonttype": 42, "ps.fonttype": 42} if type42 else {}
    try:
        with rc_context(context):
            for destination, selected_format in zip(plan.destinations, plan.formats):
                temporary = _temporary_sibling(destination)
                rendered.append(temporary)
                plan.figure.savefig(
                    temporary,
                    format=selected_format,
                    **save_options,
                )
    except Exception as exc:
        _cleanup_temporaries(rendered)
        if isinstance(exc, OutputError):
            raise
        raise OutputError("save: one or more outputs could not be rendered") from exc
    return tuple(rendered)


def _commit_outputs(plan: _SavePlan, rendered: Sequence[Path]) -> tuple[Path, ...]:
    """Replace final paths in format order and report any partial commit."""

    committed: list[Path] = []
    try:
        for temporary, destination in zip(rendered, plan.destinations):
            _existing_destination(destination, overwrite=plan.overwrite)
            os.replace(temporary, destination)
            committed.append(destination)
    except Exception as exc:
        _cleanup_temporaries(rendered)
        raise OutputError(
            "save: rendered outputs could not all be committed",
            committed_paths=committed,
        ) from exc
    return tuple(committed)


def save(
    target: Figure | AxesTarget,
    path: str | PathLike[str],
    *,
    formats: str | Sequence[str] | None = None,
    dpi: float = 600,
    crop: bool = True,
    pad: float | None = None,
    show: bool = True,
    close: bool = False,
    create_parent: bool = False,
    overwrite: bool = True,
    transparent: bool = False,
    metadata: Mapping[str, object] | None = None,
) -> tuple[Path, ...]:
    """Save one explicit Figure through a concise transactional workflow.

    Parameters
    ----------
    target
        A Figure or finite Axes target resolving to exactly one root Figure.
    path
        A supported suffix-bearing path or a suffix-free output base.
    formats
        Ordered output formats. A suffix-free path defaults to PNG and PDF.
    dpi
        Positive output resolution, defaulting to 600 dots per inch.
    crop, pad
        Whether to use a tight crop and its non-negative padding in inches.
        ``pad=None`` resolves to 0.1 inch when cropping.
    show, close
        Display after successful commits or close exactly the saved Figure.
        Both controls cannot be true together.
    create_parent
        Create a missing parent directory when true.
    overwrite
        Replace existing regular files when true. Symlinks are always rejected.
    transparent
        Forward transparent output to Matplotlib.
    metadata
        Optional string-keyed metadata forwarded to each selected format.

    Returns
    -------
    tuple[pathlib.Path, ...]
        Absolute final paths in requested format order.

    Raises
    ------
    OutputError
        If target, controls, rendering, commit, display, or closing fails.

    Notes
    -----
    Every format is rendered to a unique sibling first. Final paths are
    replaced only after all renders succeed. PDF and PostScript rendering uses
    Type 42 fonts in a bounded Matplotlib configuration context. Tight crop
    changes the exported media box; pass ``crop=False`` to preserve the exact
    Figure design canvas.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, axis = gs.subplots()
    >>> paths = gs.save(figure, "figure", show=False)
    >>> tuple(path.suffix for path in paths)
    ('.png', '.pdf')
    >>> figure.clear()
    """

    plan = _save_plan(
        target,
        path,
        formats=formats,
        dpi=dpi,
        crop=crop,
        pad=pad,
        show=show,
        close=close,
        create_parent=create_parent,
        overwrite=overwrite,
        transparent=transparent,
        metadata=metadata,
    )
    _prepare_output_parent(plan)
    committed = _commit_outputs(plan, _render_outputs(plan))
    if plan.show:
        try:
            display = globals()["show"]
            display(plan.figure)
        except Exception as exc:
            raise OutputError(
                "save: outputs were committed but the Figure could not be displayed",
                committed_paths=committed,
            ) from exc
    if plan.close:
        try:
            from matplotlib import pyplot as plt

            plt.close(plan.figure)
        except Exception as exc:
            raise OutputError(
                "save: outputs were committed but the Figure could not be closed",
                committed_paths=committed,
            ) from exc
    return committed


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
        raise OptionError(f"savefig props contains unknown key(s): {joined}")
    return dict(props)


def _is_interactive_figure(figure: Figure) -> bool:
    """Return whether a canvas has a GUI/web manager implementation."""

    canvas = figure.canvas
    framework = getattr(canvas, "required_interactive_framework", None)
    manager_class = getattr(canvas, "manager_class", FigureManagerBase)
    return framework is not None or manager_class is not FigureManagerBase


def show(target: Figure | AxesTarget) -> None:
    """Display only the unique Figure owned by an explicit target.

    A non-interactive canvas is a documented no-op. An interactive canvas is
    displayed once through its Figure manager without invoking global pyplot
    display or starting a process-global event loop.

    Parameters
    ----------
    target
        A Figure or finite Axes target resolving to exactly one root Figure.

    Returns
    -------
    None
        The Figure is displayed through its own manager when interactive.

    Raises
    ------
    OutputError
        If the target is ambiguous, an interactive Figure has no usable
        manager, or display fails.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, _ = gs.subplots()
    >>> gs.show(figure)  # no-op on non-interactive backends
    >>> figure.clear()
    """

    figure = _target_figure(target, "show")
    if not _is_interactive_figure(figure):
        return None
    if getattr(figure.canvas, "manager", None) is None:
        raise OutputError("show: interactive display requires a managed Figure")
    try:
        figure.show(warn=False)
    except Exception as exc:
        raise OutputError("show: the supplied Figure could not be displayed") from exc


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
    """Save an explicit Figure and optionally display it after all writes.

    Parameters
    ----------
    fig
        The Figure whose native ``savefig`` method is used.
    path
        A suffix-bearing output path or a suffix-free path combined with
        ``formats``.
    formats
        One or more supported formats: ``png``, ``pdf``, or ``svg``.
    dpi
        Optional positive output resolution.
    close, create_parent, overwrite, show
        Explicit lifecycle and filesystem controls.  ``show`` defaults to
        ``True`` and runs only after every requested write succeeds.
    props
        A finite mapping of Matplotlib save properties; gsplot controls may
        not be supplied through this mapping.

    Returns
    -------
    tuple[pathlib.Path, ...]
        Absolute paths written in the requested order.

    Raises
    ------
    OutputError
        If validation, saving, display, or optional closing fails.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, _ = gs.subplots()
    >>> paths = gs.savefig(figure, "figure.png", show=False, overwrite=True)
    >>> paths[0].suffix
    '.png'
    >>> figure.clear()
    """

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
            raise OutputError("output parent is not a directory")
        if not parent.exists() and not create_parent_value:
            raise OutputError("output parent does not exist")
    if not overwrite_value:
        existing = [item for item in destinations if item.exists()]
        if existing:
            raise OutputError("output already exists")
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
            raise OutputError(
                f"could not save output in {selected_format} format",
                committed_paths=written,
            ) from exc
        written.append(destination_path)
    result = tuple(written)
    if show_value:
        try:
            display = globals()["show"]
            display(fig)
        except OutputError as exc:
            raise OutputError(
                "saved outputs but could not display the Figure",
                committed_paths=result,
            ) from exc
    if close_value:
        try:
            from matplotlib import pyplot as plt

            plt.close(fig)
        except Exception as exc:
            raise OutputError("saved the Figure but could not close it") from exc
    return result


__all__ = ["save", "savefig", "show"]
