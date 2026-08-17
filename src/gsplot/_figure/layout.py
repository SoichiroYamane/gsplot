"""Publication-aware figure layout with explicit Figure ownership."""

from __future__ import annotations

import inspect
import warnings
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal, cast, overload

import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from numpy.typing import NDArray

from .._config.model import Config
from .._core.errors import ConfigError, LayoutError
from .._core.options import MISSING, OptionSpec, bind_options, supplied_options
from .._core.plans import OptionPlan
from .._core.types import (
    AxesDict,
    LayoutMode,
    MosaicSpec,
    SizeSpec,
    StyleMode,
    Unit,
)
from .._core.validation import ensure_bool, ensure_finite_real, ensure_pair
from .._style.paper import paper
from .backend import use_backend

AxesContainer = Axes | NDArray[Any] | AxesDict | dict[str, Axes]
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


def _optional_nonnegative_float(value: Any, name: str) -> float | None:
    """Validate an optional non-negative real scalar."""

    if value is None or value is MISSING:
        return None
    val = ensure_finite_real(value, name, error=LayoutError)
    if val < 0:
        raise LayoutError(f"{name} must be non-negative")
    return val


def _resolve_alias(primary: Any, alias: Any, primary_name: str, alias_name: str) -> Any:
    """Resolve an option and its alias while forbidding conflicting definitions."""

    if (
        primary is not MISSING
        and alias is not MISSING
        and primary is not None
        and alias is not None
    ):
        if primary != alias:
            raise LayoutError(
                f"{primary_name} and {alias_name} cannot both be supplied with different values"
            )
    return primary if (primary is not MISSING and primary is not None) else alias


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
    live: Any,
    layout: Any,
    style: Any,
    pad: Any = MISSING,
    xpad: Any = MISSING,
    ypad: Any = MISSING,
    xspace: Any = MISSING,
    yspace: Any = MISSING,
    w_pad: Any = MISSING,
    h_pad: Any = MISSING,
    wspace: Any = MISSING,
    hspace: Any = MISSING,
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

    resolved_xpad = _resolve_alias(xpad, w_pad, "xpad", "w_pad")
    resolved_ypad = _resolve_alias(ypad, h_pad, "ypad", "h_pad")
    resolved_xspace = _resolve_alias(xspace, wspace, "xspace", "wspace")
    resolved_yspace = _resolve_alias(yspace, hspace, "yspace", "hspace")

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
            "live": live,
            "layout": legacy_mode if layout is MISSING else layout,
            "style": style,
            "pad": pad,
            "xpad": resolved_xpad,
            "ypad": resolved_ypad,
            "xspace": resolved_xspace,
            "yspace": resolved_yspace,
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
        _option_spec(
            "live",
            False,
            lambda value, name: ensure_bool(value, name, error=LayoutError),
        ),
        _option_spec("layout", "auto", _layout),
        _option_spec("style", "auto", _style),
        _option_spec("pad", None, _optional_nonnegative_float),
        _option_spec("xpad", None, _optional_nonnegative_float),
        _option_spec("ypad", None, _optional_nonnegative_float),
        _option_spec("xspace", None, _optional_nonnegative_float),
        _option_spec("yspace", None, _optional_nonnegative_float),
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
    layout: LayoutMode,
    clear: bool = False,
) -> None:
    """Reject incompatible Figure reuse before clearing or adding Axes."""

    if layout == "auto" or clear:
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
        created = figure.subplot_mosaic(
            cast(Any, shape.mosaic),
            sharex=cast(bool, _matplotlib_share(options["sharex"], mosaic=True)),
            sharey=cast(bool, _matplotlib_share(options["sharey"], mosaic=True)),
            width_ratios=options["width_ratios"],
            height_ratios=options["height_ratios"],
            subplot_kw=kwargs,
        )
        return AxesDict(created)
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


@overload
def subplots(
    shape: str | Sequence[Sequence[str | None]],
    /,
    *,
    nrows: None = None,
    ncols: None = None,
    mosaic: None = None,
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
    live: bool = False,
    layout: LayoutMode = "auto",
    style: StyleMode = "auto",
    pad: float | None = None,
    xpad: float | None = None,
    ypad: float | None = None,
    xspace: float | None = None,
    yspace: float | None = None,
    w_pad: float | None = None,
    h_pad: float | None = None,
    wspace: float | None = None,
    hspace: float | None = None,
    config: Config | None = None,
    figsize: tuple[float, float] | None = None,
    tight_layout: bool | None = None,
    constrained_layout: bool | None = None,
) -> tuple[Figure, AxesDict]: ...


@overload
def subplots(
    *,
    mosaic: MosaicSpec,
    nrows: None = None,
    ncols: None = None,
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
    live: bool = False,
    layout: LayoutMode = "auto",
    style: StyleMode = "auto",
    pad: float | None = None,
    xpad: float | None = None,
    ypad: float | None = None,
    xspace: float | None = None,
    yspace: float | None = None,
    w_pad: float | None = None,
    h_pad: float | None = None,
    wspace: float | None = None,
    hspace: float | None = None,
    config: Config | None = None,
    figsize: tuple[float, float] | None = None,
    tight_layout: bool | None = None,
    constrained_layout: bool | None = None,
) -> tuple[Figure, AxesDict]: ...


@overload
def subplots(
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
    live: bool = False,
    layout: LayoutMode = "auto",
    style: StyleMode = "auto",
    pad: float | None = None,
    xpad: float | None = None,
    ypad: float | None = None,
    xspace: float | None = None,
    yspace: float | None = None,
    w_pad: float | None = None,
    h_pad: float | None = None,
    wspace: float | None = None,
    hspace: float | None = None,
    config: Config | None = None,
    figsize: tuple[float, float] | None = None,
    tight_layout: bool | None = None,
    constrained_layout: bool | None = None,
) -> tuple[Figure, AxesContainer]: ...


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
    live: bool = cast(bool, MISSING),
    layout: LayoutMode = cast(LayoutMode, MISSING),
    style: StyleMode = cast(StyleMode, MISSING),
    pad: float | None = cast(Any, MISSING),
    xpad: float | None = cast(Any, MISSING),
    ypad: float | None = cast(Any, MISSING),
    xspace: float | None = cast(Any, MISSING),
    yspace: float | None = cast(Any, MISSING),
    w_pad: float | None = cast(Any, MISSING),
    h_pad: float | None = cast(Any, MISSING),
    wspace: float | None = cast(Any, MISSING),
    hspace: float | None = cast(Any, MISSING),
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
    live
        Whether to run in interactive live mode. When true, reuses the active
        Figure (or creates one), automatically clears previous axes, and
        requests an idle canvas draw.
    layout
        ``"auto"``, ``"constrained"``, ``"tight"``, or ``"none"``.
    style
        ``"auto"`` or ``"paper"`` for target-local publication styling, or
        ``None`` to retain Matplotlib styling.
    pad
        Optional non-negative figure padding scalar.
    xpad, ypad
        Optional non-negative horizontal and vertical subplot padding scalars
        (aliases for ``w_pad`` and ``h_pad``).
    xspace, yspace
        Optional non-negative horizontal and vertical spacing fractions
        (aliases for ``wspace`` and ``hspace``).
    w_pad, h_pad, wspace, hspace
        Matplotlib layout-engine padding and spacing alternatives.
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
        live=live,
        layout=layout,
        style=style,
        pad=pad,
        xpad=xpad,
        ypad=ypad,
        xspace=xspace,
        yspace=yspace,
        w_pad=w_pad,
        h_pad=h_pad,
        wspace=wspace,
        hspace=hspace,
        config=config,
        figsize=figsize,
        tight_layout=tight_layout,
        constrained_layout=constrained_layout,
    )
    is_live = options["live"]
    selected_clear = True if is_live else options["clear"]

    resolved_fig = fig
    if resolved_fig is None and is_live:
        import matplotlib.pyplot as plt

        fignums = plt.get_fignums()
        if fignums:
            resolved_fig = plt.figure(fignums[-1])

    if resolved_fig is not None and not isinstance(resolved_fig, Figure):
        raise LayoutError("fig must be a Matplotlib Figure or None")
    preserve_reused_size = resolved_fig is not None and (
        options["size"] == "auto" or options["size"] is None
    )
    size_inches = None if preserve_reused_size else _size_inches(shape_plan, options)
    if resolved_fig is not None:
        _validate_reuse(
            resolved_fig,
            layout=options["layout"],
            clear=selected_clear,
        )

    new_figure = resolved_fig is None
    selected_layout = (
        "constrained" if options["layout"] == "auto" else options["layout"]
    )
    if new_figure:
        import matplotlib.pyplot as plt

        target = plt.figure(
            figsize=size_inches,
            layout=None if selected_layout == "none" else selected_layout,
        )
    else:
        target = cast(Figure, resolved_fig)
        if size_inches is not None:
            target.set_size_inches(size_inches, forward=True)
        if selected_clear:
            target.clear()
            target.set_layout_engine(
                cast(Any, None if selected_layout == "none" else selected_layout)
            )
        elif options["layout"] in {"tight", "constrained"}:
            target.set_layout_engine(cast(Any, options["layout"]))

    axes = _create_axes(target, shape_plan, options)

    from matplotlib.layout_engine import ConstrainedLayoutEngine, TightLayoutEngine

    engine = target.get_layout_engine()
    if isinstance(engine, ConstrainedLayoutEngine):
        engine_kwargs: dict[str, Any] = {}
        if options["xpad"] is not None:
            engine_kwargs["w_pad"] = options["xpad"]
        elif options["pad"] is not None:
            engine_kwargs["w_pad"] = options["pad"]

        if options["ypad"] is not None:
            engine_kwargs["h_pad"] = options["ypad"]
        elif options["pad"] is not None:
            engine_kwargs["h_pad"] = options["pad"]

        if options["xspace"] is not None:
            engine_kwargs["wspace"] = options["xspace"]
        if options["yspace"] is not None:
            engine_kwargs["hspace"] = options["yspace"]
        if engine_kwargs:
            engine.set(**engine_kwargs)
    elif isinstance(engine, TightLayoutEngine):
        tight_kwargs: dict[str, Any] = {}
        if options["pad"] is not None:
            tight_kwargs["pad"] = options["pad"]
        if options["xpad"] is not None:
            tight_kwargs["w_pad"] = options["xpad"]
        if options["ypad"] is not None:
            tight_kwargs["h_pad"] = options["ypad"]
        if tight_kwargs:
            engine.set(**tight_kwargs)

    apply_paper = (
        (new_figure or selected_clear) and options["style"] == "auto"
    ) or options["style"] == "paper"
    if apply_paper:
        paper(cast(Any, axes))
        target.set_facecolor("white")
    if is_live:
        import matplotlib.pyplot as plt

        if not plt.isinteractive():
            plt.ion()
        try:
            manager = getattr(target.canvas, "manager", None)
            if manager is not None:
                manager.show()
            target.canvas.draw_idle()
        except Exception:
            pass
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
    live: bool = False,
    layout: LayoutMode = "auto",
    style: StyleMode = "auto",
    pad: float | None = None,
    xpad: float | None = None,
    ypad: float | None = None,
    xspace: float | None = None,
    yspace: float | None = None,
    w_pad: float | None = None,
    h_pad: float | None = None,
    wspace: float | None = None,
    hspace: float | None = None,
    config: Config | None = None,
    figsize: tuple[float, float] | None = None,
    tight_layout: bool | None = None,
    constrained_layout: bool | None = None,
) -> tuple[Figure, AxesContainer]:
    """Define the resolved user-facing signature for introspection."""

    raise NotImplementedError


cast(Any, subplots).__signature__ = inspect.signature(_public_subplots_signature)

__all__ = ["subplots", "use_backend"]
