"""Publication-aware figure layout with explicit Figure ownership."""

from __future__ import annotations

import inspect
import warnings
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, cast

import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from numpy.typing import NDArray

from .._config.model import Config
from .._core.errors import ConfigError, LayoutError
from .._core.options import MISSING, OptionSpec, bind_options, supplied_options
from .._core.plans import OptionPlan
from .._core.types import (
    LayoutMode,
    MosaicSpec,
    SizeSpec,
    StyleMode,
    Unit,
)
from .._core.validation import ensure_bool, ensure_finite_real, ensure_pair
from .._style.paper import paper
from .backend import use_backend

AxesContainer = Axes | NDArray[Any] | dict[str, Axes]
ShareMode = bool | Literal["none", "all", "row", "col"]

_UNIT_TO_INCH = {"in": 1.0, "cm": 1 / 2.54, "mm": 1 / 25.4, "pt": 1 / 72.0}
_SINGLE_WIDTH_MM = 85.0
_DOUBLE_WIDTH_MM = 170.0
_MIN_NOMINAL_MM = 50.0
_MAX_HEIGHT_MM = 220.0


@dataclass(frozen=True, slots=True)
class _ShapePlan:
    """Validated outer layout dimensions and optional mosaic."""

    rows: int
    columns: int
    mosaic: MosaicSpec | None


def _count(value: Any, name: str) -> int:
    """Validate one positive non-boolean grid count."""

    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise LayoutError(f"{name} must be a positive integer")
    return value


def _mosaic_rows(mosaic: MosaicSpec) -> tuple[tuple[object, ...], ...]:
    """Snapshot a finite rectangular mosaic without creating a Figure."""

    rows: tuple[tuple[object, ...], ...]
    if isinstance(mosaic, str):
        if not mosaic.strip():
            raise LayoutError("mosaic must not be empty")
        if "\n" in mosaic:
            normalized = inspect.cleandoc(mosaic).strip("\n").split("\n")
        else:
            normalized = mosaic.split(";")
        rows = tuple(tuple(row) for row in normalized)
    else:
        if isinstance(mosaic, (str, bytes)) or not isinstance(mosaic, Sequence):
            raise LayoutError("mosaic must be a string or a sequence of rows")
        source_rows = tuple(mosaic)
        if any(
            isinstance(row, (str, bytes)) or not isinstance(row, Sequence)
            for row in source_rows
        ):
            raise LayoutError("mosaic rows must be non-string sequences")
        rows = tuple(tuple(cast(Sequence[object], row)) for row in source_rows)

    if not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows):
        raise LayoutError("mosaic must contain a non-empty rectangular grid")
    for row_index, row in enumerate(rows):
        for column_index, label in enumerate(row):
            if label is None:
                continue
            if not isinstance(label, str) or not label.strip():
                raise LayoutError(
                    f"mosaic label at ({row_index}, {column_index}) "
                    "must be non-empty text or None"
                )

    labels = {label for row in rows for label in row if label not in {None, "."}}
    for label in labels:
        positions = [
            (row_index, column_index)
            for row_index, row in enumerate(rows)
            for column_index, value in enumerate(row)
            if value == label
        ]
        row_values = [position[0] for position in positions]
        column_values = [position[1] for position in positions]
        expected = {
            (row_index, column_index)
            for row_index in range(min(row_values), max(row_values) + 1)
            for column_index in range(min(column_values), max(column_values) + 1)
        }
        if set(positions) != expected:
            raise LayoutError(f"mosaic label {label!r} must form one rectangle")
    return rows


def _validate_mosaic(mosaic: Any) -> MosaicSpec:
    """Validate the mosaic shape retained by the 1.x compatibility adapter."""

    selected = cast(MosaicSpec, mosaic)
    _mosaic_rows(selected)
    return selected


def _shape_plan(
    shape: tuple[Any, ...],
    *,
    nrows: int | None,
    ncols: int | None,
    mosaic: MosaicSpec | None,
) -> _ShapePlan:
    """Resolve positional and keyword shape forms without ambiguity."""

    if len(shape) > 2:
        raise LayoutError("subplots accepts at most two positional shape values")
    if shape and any(value is not None for value in (nrows, ncols, mosaic)):
        raise LayoutError(
            "positional shape cannot be combined with nrows, ncols, or mosaic"
        )

    selected_mosaic: MosaicSpec | None = None
    if len(shape) == 2:
        rows = _count(shape[0], "shape[0]")
        columns = _count(shape[1], "shape[1]")
    elif (
        len(shape) == 1 and isinstance(shape[0], int) and not isinstance(shape[0], bool)
    ):
        rows = _count(shape[0], "shape[0]")
        columns = 1
    elif len(shape) == 1:
        selected_mosaic = cast(MosaicSpec, shape[0])
        mosaic_rows = _mosaic_rows(selected_mosaic)
        if not isinstance(selected_mosaic, str):
            selected_mosaic = cast(
                MosaicSpec,
                tuple(
                    tuple("." if value is None else value for value in row)
                    for row in mosaic_rows
                ),
            )
        rows, columns = len(mosaic_rows), len(mosaic_rows[0])
    elif mosaic is not None:
        if nrows is not None or ncols is not None:
            raise LayoutError("mosaic cannot be combined with nrows or ncols")
        selected_mosaic = mosaic
        mosaic_rows = _mosaic_rows(selected_mosaic)
        if not isinstance(selected_mosaic, str):
            selected_mosaic = cast(
                MosaicSpec,
                tuple(
                    tuple("." if value is None else value for value in row)
                    for row in mosaic_rows
                ),
            )
        rows, columns = len(mosaic_rows), len(mosaic_rows[0])
    else:
        rows = _count(1 if nrows is None else nrows, "nrows")
        columns = _count(1 if ncols is None else ncols, "ncols")
    return _ShapePlan(rows=rows, columns=columns, mosaic=selected_mosaic)


def _size(value: Any, name: str) -> SizeSpec:
    """Validate one direct canonical size specification."""

    if value is None or (
        isinstance(value, str) and value in {"auto", "single", "double"}
    ):
        return cast(SizeSpec, value)
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise LayoutError(
            f"{name} must be 'auto', 'single', 'double', None, or two dimensions"
        )
    return ensure_pair(value, name, positive=True, error=LayoutError)


def _unit(value: Any, name: str) -> Unit:
    """Validate one physical size unit."""

    if not isinstance(value, str) or value not in _UNIT_TO_INCH:
        raise LayoutError(f"{name} must be one of: in, cm, mm, pt")
    return cast(Unit, value)


def _layout(value: Any, name: str) -> LayoutMode:
    """Validate one finite Figure layout mode."""

    if value not in {"auto", "constrained", "tight", "none"}:
        raise LayoutError(f"{name} must be 'auto', 'constrained', 'tight', or 'none'")
    return cast(LayoutMode, value)


def _style(value: Any, name: str) -> StyleMode:
    """Validate one target-local subplot style mode."""

    if value not in {"auto", "paper", None}:
        raise LayoutError(f"{name} must be 'auto', 'paper', or None")
    return cast(StyleMode, value)


def _share(value: Any, name: str) -> ShareMode:
    """Validate one Matplotlib-compatible sharing mode."""

    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value in {"none", "all", "row", "col"}:
        return cast(ShareMode, value)
    raise LayoutError(f"{name} must be a boolean or 'none', 'all', 'row', or 'col'")


def _ratios(value: Any, name: str, count: int) -> tuple[float, ...] | None:
    """Validate one positive ratio sequence for an exact outer dimension."""

    if value is None:
        return None
    if isinstance(value, np.ndarray):
        if value.ndim != 1:
            raise LayoutError(f"{name} must be one-dimensional")
        value = value.tolist()
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise LayoutError(f"{name} must be a sequence of {count} positive values")
    selected = tuple(
        ensure_finite_real(item, f"{name}[{index}]", error=LayoutError)
        for index, item in enumerate(value)
    )
    if len(selected) != count:
        raise LayoutError(f"{name} must contain exactly {count} values")
    if any(item <= 0 for item in selected):
        raise LayoutError(f"{name} values must be positive")
    return selected


def _subplot_options(value: Any, name: str) -> Mapping[str, Any] | None:
    """Snapshot one finite string-keyed subplot option mapping."""

    if value is None:
        return None
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise LayoutError(f"{name} must be a string-keyed mapping or None")
    return dict(value)


def _legacy_layout(
    *, tight_layout: Any, constrained_layout: Any
) -> LayoutMode | object:
    """Translate finite 1.x layout booleans while retaining omission."""

    supplied = [
        value
        for value in (tight_layout, constrained_layout)
        if value is not MISSING and value is not None
    ]
    if not supplied:
        return MISSING
    tight = (
        False
        if tight_layout is MISSING or tight_layout is None
        else ensure_bool(tight_layout, "tight_layout", error=LayoutError)
    )
    constrained = (
        False
        if constrained_layout is MISSING or constrained_layout is None
        else ensure_bool(constrained_layout, "constrained_layout", error=LayoutError)
    )
    if tight and constrained:
        raise LayoutError("tight_layout and constrained_layout cannot both be true")
    return "tight" if tight else "constrained" if constrained else "none"


def _option_spec(
    name: str,
    default: Any,
    validator: Callable[[Any, str], Any],
) -> OptionSpec[Any]:
    """Build a typed option without runtime generic subscription on Python 3.10."""

    return OptionSpec(name, default, validator=validator)


def _resolve_options(
    shape: _ShapePlan,
    *,
    size: Any,
    unit: Any,
    sharex: Any,
    sharey: Any,
    squeeze: Any,
    width_ratios: Any,
    height_ratios: Any,
    subplot_kw: Any,
    clear: Any,
    layout: Any,
    style: Any,
    config: Config | None,
    figsize: Any,
    tight_layout: Any,
    constrained_layout: Any,
) -> OptionPlan:
    """Bind direct, compatibility, Config, and default values once."""

    if config is not None and not isinstance(config, Config):
        raise ConfigError("config must be a gsplot Config")
    legacy_size = MISSING if figsize is MISSING else _size(figsize, "figsize")
    legacy_mode = _legacy_layout(
        tight_layout=tight_layout, constrained_layout=constrained_layout
    )
    if size is not MISSING and legacy_size is not MISSING:
        raise LayoutError("size and deprecated figsize cannot both be supplied")
    if layout is not MISSING and legacy_mode is not MISSING:
        raise LayoutError(
            "layout cannot be combined with tight_layout or constrained_layout"
        )

    direct = supplied_options(
        {
            "size": legacy_size if size is MISSING else size,
            "unit": unit,
            "sharex": sharex,
            "sharey": sharey,
            "squeeze": squeeze,
            "width_ratios": width_ratios,
            "height_ratios": height_ratios,
            "subplot_kw": subplot_kw,
            "clear": clear,
            "layout": legacy_mode if layout is MISSING else layout,
            "style": style,
        }
    )
    configured = None
    if config is not None:
        configured = {
            "size": config.figure.size,
            "unit": config.figure.unit,
            "squeeze": config.figure.squeeze,
            "layout": config.figure.layout,
        }
    specs: tuple[OptionSpec[Any], ...] = (
        _option_spec("size", "auto", _size),
        _option_spec("unit", "in", _unit),
        _option_spec("sharex", False, _share),
        _option_spec("sharey", False, _share),
        _option_spec(
            "squeeze",
            True,
            lambda value, name: ensure_bool(value, name, error=LayoutError),
        ),
        _option_spec(
            "width_ratios",
            None,
            lambda value, name: _ratios(value, name, shape.columns),
        ),
        _option_spec(
            "height_ratios",
            None,
            lambda value, name: _ratios(value, name, shape.rows),
        ),
        _option_spec("subplot_kw", None, _subplot_options),
        _option_spec(
            "clear",
            False,
            lambda value, name: ensure_bool(value, name, error=LayoutError),
        ),
        _option_spec("layout", "auto", _layout),
        _option_spec("style", "auto", _style),
    )
    plan = bind_options("subplots", specs, explicit=direct, configured=configured)
    if (figsize is not MISSING) or any(
        value is not MISSING and value is not None
        for value in (tight_layout, constrained_layout)
    ):
        warnings.warn(
            "figsize, tight_layout, and constrained_layout are deprecated; "
            "use size and layout",
            DeprecationWarning,
            stacklevel=3,
        )
    if not isinstance(plan["size"], tuple) and plan["unit"] != "in":
        raise LayoutError("unit must be 'in' unless size is an explicit tuple")
    if shape.mosaic is not None:
        for name in ("sharex", "sharey"):
            if plan[name] in {"row", "col"}:
                raise LayoutError(
                    f"{name}='row' or 'col' is unavailable for mosaic layouts"
                )
    return plan


def _named_size_mm(
    shape: _ShapePlan,
    size: str,
    width_ratios: tuple[float, ...] | None,
    height_ratios: tuple[float, ...] | None,
) -> tuple[float, float]:
    """Resolve a named publication canvas and enforce readability guards."""

    width = (
        _SINGLE_WIDTH_MM
        if size == "single" or (size == "auto" and shape.columns == 1)
        else _DOUBLE_WIDTH_MM
    )
    pitch = width / shape.columns
    height = pitch * shape.rows
    selected_widths = width_ratios or (1.0,) * shape.columns
    selected_heights = height_ratios or (1.0,) * shape.rows
    nominal_widths = tuple(
        width * value / sum(selected_widths) for value in selected_widths
    )
    nominal_heights = tuple(
        height * value / sum(selected_heights) for value in selected_heights
    )
    if min(*nominal_widths, *nominal_heights) < _MIN_NOMINAL_MM:
        raise LayoutError(
            "named publication size gives a nominal row or column below 50 mm; "
            "use a larger explicit size=(width, height)"
        )
    if height > _MAX_HEIGHT_MM:
        raise LayoutError(
            "named publication size exceeds the 220 mm height limit; "
            "use an explicit size=(width, height)"
        )
    return width, height


def _size_inches(shape: _ShapePlan, options: OptionPlan) -> tuple[float, float] | None:
    """Convert one validated size plan to a Matplotlib inch tuple."""

    size = options["size"]
    if size is None:
        return None
    if isinstance(size, tuple):
        factor = _UNIT_TO_INCH[options["unit"]]
        return size[0] * factor, size[1] * factor
    width, height = _named_size_mm(
        shape,
        size,
        options["width_ratios"],
        options["height_ratios"],
    )
    return width / 25.4, height / 25.4


def _layout_kind(figure: Figure) -> str:
    """Classify an existing Figure layout engine without mutation."""

    engine = figure.get_layout_engine()
    if engine is None:
        return "none"
    from matplotlib.layout_engine import ConstrainedLayoutEngine, TightLayoutEngine

    if isinstance(engine, ConstrainedLayoutEngine):
        return "constrained"
    if isinstance(engine, TightLayoutEngine):
        return "tight"
    return "other"


def _validate_reuse(
    figure: Figure,
    *,
    size: SizeSpec,
    size_inches: tuple[float, float] | None,
    layout: LayoutMode,
) -> None:
    """Reject incompatible Figure reuse before clearing or adding Axes."""

    if (
        size not in {"auto", None}
        and size_inches is not None
        and not np.allclose(figure.get_size_inches(), size_inches, rtol=0, atol=1e-9)
    ):
        raise LayoutError(
            "requested size does not match the reused Figure; omit size to preserve it"
        )
    if layout == "auto":
        return
    current = _layout_kind(figure)
    if current != layout and not (
        current == "none" and layout in {"tight", "constrained"}
    ):
        raise LayoutError(
            f"layout={layout!r} conflicts with the reused Figure's {current!r} layout"
        )


def _matplotlib_share(value: ShareMode, *, mosaic: bool) -> ShareMode:
    """Translate common sharing names for the stricter mosaic API."""

    if not mosaic:
        return value
    return value == "all" if isinstance(value, str) else value


def _create_axes(
    figure: Figure, shape: _ShapePlan, options: OptionPlan
) -> AxesContainer:
    """Create axes only after every operation precondition has passed."""

    kwargs = dict(options["subplot_kw"] or {})
    if shape.mosaic is not None:
        return cast(
            dict[str, Axes],
            figure.subplot_mosaic(
                cast(Any, shape.mosaic),
                sharex=cast(bool, _matplotlib_share(options["sharex"], mosaic=True)),
                sharey=cast(bool, _matplotlib_share(options["sharey"], mosaic=True)),
                width_ratios=options["width_ratios"],
                height_ratios=options["height_ratios"],
                subplot_kw=kwargs,
            ),
        )
    return cast(
        AxesContainer,
        figure.subplots(
            shape.rows,
            shape.columns,
            sharex=options["sharex"],
            sharey=options["sharey"],
            squeeze=options["squeeze"],
            width_ratios=options["width_ratios"],
            height_ratios=options["height_ratios"],
            subplot_kw=kwargs,
        ),
    )


def subplots(
    *shape: int | MosaicSpec,
    nrows: int | None = None,
    ncols: int | None = None,
    mosaic: MosaicSpec | None = None,
    size: SizeSpec = cast(SizeSpec, MISSING),
    unit: Unit = cast(Unit, MISSING),
    sharex: ShareMode = cast(ShareMode, MISSING),
    sharey: ShareMode = cast(ShareMode, MISSING),
    squeeze: bool = cast(bool, MISSING),
    width_ratios: Sequence[float] | None = cast(Any, MISSING),
    height_ratios: Sequence[float] | None = cast(Any, MISSING),
    subplot_kw: Mapping[str, Any] | None = cast(Any, MISSING),
    fig: Figure | None = None,
    clear: bool = cast(bool, MISSING),
    layout: LayoutMode = cast(LayoutMode, MISSING),
    style: StyleMode = cast(StyleMode, MISSING),
    config: Config | None = None,
    figsize: tuple[float, float] | None = cast(Any, MISSING),
    tight_layout: bool | None = cast(Any, MISSING),
    constrained_layout: bool | None = cast(Any, MISSING),
) -> tuple[Figure, AxesContainer]:
    """Create or reuse a native Figure with concise publication defaults.

    Parameters
    ----------
    *shape
        Zero values for keyword shape, one positive row count or mosaic, or
        two positive grid dimensions.
    nrows, ncols, mosaic
        Explicit keyword alternatives to positional shape.
    size, unit
        ``"auto"``, ``"single"``, ``"double"``, explicit dimensions, or
        ``None`` and the physical unit for explicit dimensions.
    sharex, sharey, squeeze
        Native Matplotlib sharing and return-container controls.
    width_ratios, height_ratios
        Positive ratios matching the outer layout dimensions.
    subplot_kw
        Finite options copied into each Matplotlib subplot constructor.
    fig, clear
        Optional existing Figure and whether to clear it after validation.
    layout
        ``"auto"``, ``"constrained"``, ``"tight"``, or ``"none"``.
    style
        ``"auto"`` or ``"paper"`` for target-local publication styling, or
        ``None`` to retain Matplotlib styling.
    config
        Explicit immutable configuration for omitted size, unit, squeeze, and
        layout values.
    figsize, tight_layout, constrained_layout
        Deprecated 1.x spellings retained for source compatibility.

    Returns
    -------
    tuple
        The native Figure and Matplotlib Axes, array, or mosaic dictionary.

    Raises
    ------
    LayoutError, ConfigError
        If shape, sizing, layout, style, compatibility, or reuse is invalid.

    Notes
    -----
    New automatic Figures use an 85 mm single-column or 170 mm multi-column
    canvas, constrained layout, and target-local paper styling. Reused Figures
    retain size, layout, and existing Axes styling unless compatible explicit
    values request otherwise.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, axes = gs.subplots("AB")
    >>> tuple(axes)
    ('A', 'B')
    >>> figure.clear()
    """

    shape_plan = _shape_plan(shape, nrows=nrows, ncols=ncols, mosaic=mosaic)
    options = _resolve_options(
        shape_plan,
        size=size,
        unit=unit,
        sharex=sharex,
        sharey=sharey,
        squeeze=squeeze,
        width_ratios=width_ratios,
        height_ratios=height_ratios,
        subplot_kw=subplot_kw,
        clear=clear,
        layout=layout,
        style=style,
        config=config,
        figsize=figsize,
        tight_layout=tight_layout,
        constrained_layout=constrained_layout,
    )
    if fig is not None and not isinstance(fig, Figure):
        raise LayoutError("fig must be a Matplotlib Figure or None")
    preserve_reused_size = fig is not None and (
        options["size"] == "auto" or options["size"] is None
    )
    size_inches = None if preserve_reused_size else _size_inches(shape_plan, options)
    if fig is not None:
        _validate_reuse(
            fig,
            size=options["size"],
            size_inches=size_inches,
            layout=options["layout"],
        )

    new_figure = fig is None
    if new_figure:
        import matplotlib.pyplot as plt

        selected_layout = (
            "constrained" if options["layout"] == "auto" else options["layout"]
        )
        target = plt.figure(figsize=size_inches, layout=selected_layout)
    else:
        target = cast(Figure, fig)
        if options["clear"]:
            target.clear()

    axes = _create_axes(target, shape_plan, options)
    if not new_figure and options["layout"] in {"tight", "constrained"}:
        target.set_layout_engine(options["layout"])
    selected_style = (
        "paper" if new_figure and options["style"] == "auto" else options["style"]
    )
    if selected_style == "paper":
        paper(cast(Any, axes))
        if new_figure:
            target.set_facecolor("white")
    return target, axes


def _public_subplots_signature(
    *shape: int | MosaicSpec,
    nrows: int | None = None,
    ncols: int | None = None,
    mosaic: MosaicSpec | None = None,
    size: SizeSpec = "auto",
    unit: Unit = "in",
    sharex: ShareMode = False,
    sharey: ShareMode = False,
    squeeze: bool = True,
    width_ratios: Sequence[float] | None = None,
    height_ratios: Sequence[float] | None = None,
    subplot_kw: Mapping[str, Any] | None = None,
    fig: Figure | None = None,
    clear: bool = False,
    layout: LayoutMode = "auto",
    style: StyleMode = "auto",
    config: Config | None = None,
    figsize: tuple[float, float] | None = None,
    tight_layout: bool | None = None,
    constrained_layout: bool | None = None,
) -> tuple[Figure, AxesContainer]:
    """Define the resolved user-facing signature for introspection."""

    raise NotImplementedError


cast(Any, subplots).__signature__ = inspect.signature(_public_subplots_signature)

__all__ = ["subplots", "use_backend"]
