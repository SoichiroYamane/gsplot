"""Tests for canonical target, finite-option, and immutable-plan foundations."""

from __future__ import annotations

import gc
import weakref
from dataclasses import FrozenInstanceError

import numpy as np
import pytest
from matplotlib.figure import Figure

from gsplot._core import MISSING as CORE_MISSING
from gsplot._core import AxesTarget, PerTarget
from gsplot._core.errors import OptionError, PlotError
from gsplot._core.options import (
    MISSING,
    OptionSpec,
    bind_options,
    supplied_options,
)
from gsplot._core.plans import OperationPlan, TargetPlan
from gsplot._core.targets import normalize_axes, resolve_target_mapping
from gsplot._core.validation import MISSING as VALIDATION_MISSING


def _figure_axes(count: int = 2):
    """Return an unregistered Figure and a stable tuple of owned Axes."""

    figure = Figure()
    axes = figure.subplots(1, count, squeeze=False)
    return figure, tuple(axes.ravel(order="C"))


def test_target_normalization_preserves_every_supported_order() -> None:
    """Single, sequence, array, and mapping targets have deterministic keys."""

    figure, axes = _figure_axes(4)
    single = normalize_axes(axes[2], operation="paper")
    assert single.figure is figure
    assert single.axes == (axes[2],)
    assert single.keys == (axes[2],)
    assert single.kind == "single"
    assert single.single

    sequence = normalize_axes([axes[3], axes[1], axes[0]], operation="paper")
    assert sequence.axes == (axes[3], axes[1], axes[0])
    assert sequence.keys == sequence.axes
    assert sequence.kind == "sequence"

    array = normalize_axes(
        np.asarray([[axes[2], axes[0]], [axes[3], axes[1]]], dtype=object),
        operation="paper",
    )
    assert array.axes == (axes[2], axes[0], axes[3], axes[1])
    assert array.keys == array.axes
    assert array.kind == "array"

    mapping = normalize_axes({"right": axes[3], "left": axes[0]}, operation="paper")
    assert mapping.axes == (axes[3], axes[0])
    assert mapping.keys == ("right", "left")
    assert mapping.kind == "mapping"

    target_hint: AxesTarget = mapping.axes
    values_hint: PerTarget = {axis: index for index, axis in enumerate(axes)}
    assert target_hint == mapping.axes
    assert tuple(values_hint) == axes


def test_target_normalization_uses_the_unique_root_figure() -> None:
    """Sibling SubFigure Axes share their parent root without root=True calls."""

    figure = Figure()
    left, right = figure.subfigures(1, 2)
    axes = (left.subplots(), right.subplots())
    plan = normalize_axes(axes, operation="label")
    assert plan.figure is figure
    assert plan.axes == axes


@pytest.mark.parametrize(
    "factory",
    [
        lambda axes: [],
        lambda axes: np.empty((0, 2), dtype=object),
        lambda axes: "axes",
        lambda axes: {axes[0], axes[1]},
        lambda axes: (axis for axis in axes),
        lambda axes: [axes[0], object()],
        lambda axes: [axes[0], axes[0]],
    ],
)
def test_target_normalization_rejects_ambiguous_or_invalid_inputs(factory) -> None:
    """Invalid target shapes fail before an operation can mutate an Axes."""

    _, axes = _figure_axes()
    before = tuple(len(axis.lines) for axis in axes)
    with pytest.raises(PlotError, match="paper: target"):
        normalize_axes(factory(axes), operation="paper")
    assert tuple(len(axis.lines) for axis in axes) == before

    scalar = np.empty((), dtype=object)
    scalar[()] = axes[0]
    with pytest.raises(PlotError, match="target array"):
        normalize_axes(scalar, operation="paper")


def test_target_normalization_rejects_mixed_figures_and_is_immutable() -> None:
    """One plan cannot cross Figure ownership or be changed after preflight."""

    _, first = _figure_axes(1)
    _, second = _figure_axes(1)
    with pytest.raises(PlotError, match="one Figure"):
        normalize_axes([first[0], second[0]], operation="legend")

    plan = normalize_axes(first[0], operation="legend")
    with pytest.raises(FrozenInstanceError):
        plan.kind = "mapping"  # type: ignore[misc]
    with pytest.raises(PlotError, match="root Figure"):
        TargetPlan(
            operation="legend",
            figure=second[0].figure,
            axes=first,
            keys=first,
            kind="sequence",
        )


def test_exact_target_mapping_uses_original_or_axes_keys() -> None:
    """Per-target mappings resolve only when their key set is exact."""

    _, axes = _figure_axes()
    sequence = normalize_axes(axes, operation="line")
    assert resolve_target_mapping(
        sequence, {axes[1]: "b", axes[0]: "a"}, name="label"
    ) == ("a", "b")

    mapping = normalize_axes({"b": axes[1], "a": axes[0]}, operation="line")
    assert resolve_target_mapping(mapping, {"a": 10, "b": 20}, name="series") == (
        20,
        10,
    )
    with pytest.raises(PlotError, match="exactly"):
        resolve_target_mapping(mapping, {"a": 10}, name="series")
    with pytest.raises(PlotError, match="exactly"):
        resolve_target_mapping(mapping, {"a": 10, "other": 20}, name="series")
    with pytest.raises(PlotError, match="mapping"):
        resolve_target_mapping(mapping, [10, 20], name="series")  # type: ignore[arg-type]


def test_target_plans_are_not_retained_by_canonical_modules() -> None:
    """Releasing a plan permits its caller-owned Figure and Axes to collect."""

    figure, axes = _figure_axes(1)
    axis = axes[0]
    figure_ref = weakref.ref(figure)
    axis_ref = weakref.ref(axis)
    plan = normalize_axes(axis, operation="paper")

    del plan, axes, axis, figure
    gc.collect()
    assert figure_ref() is None
    assert axis_ref() is None


def _positive(value, name: str) -> float:
    """Validate a positive test option."""

    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise OptionError(f"line: {name} must be positive")
    return float(value)


def test_finite_option_binding_records_precedence_and_spelling() -> None:
    """Explicit, derived, Config, and default sources remain distinguishable."""

    assert MISSING is CORE_MISSING is VALIDATION_MISSING
    specs = (
        OptionSpec("linewidth", 1.0, aliases=("lw",), validator=_positive),
        OptionSpec("color", "black", aliases=("c",)),
        OptionSpec("marker", "o"),
        OptionSpec("alpha", 1.0),
    )
    plan = bind_options(
        "line",
        specs,
        explicit={"lw": 2, "alpha": MISSING},
        props={"c": "red"},
        derived={"marker": "s", "alpha": 0.8},
        configured={"color": "blue", "alpha": 0.5},
    )

    assert dict(plan) == {
        "linewidth": 2.0,
        "color": "red",
        "marker": "s",
        "alpha": 0.8,
    }
    assert plan.entry("linewidth").supplied_as == "lw"
    assert plan.entry("color").supplied_as == "props.c"
    assert plan.source("linewidth") == "explicit"
    assert plan.source("color") == "explicit"
    assert plan.source("marker") == "derived"
    assert plan.source("alpha") == "derived"
    assert plan.was_supplied("color")
    assert not plan.was_supplied("marker")

    configured = bind_options("line", specs, configured={"alpha": 0.4})
    assert configured.source("alpha") == "config"
    assert configured.source("marker") == "default"


def test_finite_option_binding_rejects_duplicates_and_unknown_fields() -> None:
    """Every option spelling and props conflict fails during preflight."""

    specs = (OptionSpec("linewidth", 1.0, aliases=("lw",)),)
    with pytest.raises(OptionError, match="more than once"):
        bind_options("line", specs, explicit={"linewidth": 1, "lw": 2})
    with pytest.raises(OptionError, match="directly and in props"):
        bind_options("line", specs, explicit={"lw": 1}, props={"linewidth": 2})
    with pytest.raises(OptionError, match="unsupported"):
        bind_options("line", specs, explicit={"unknown": 1})
    with pytest.raises(OptionError, match="canonical"):
        bind_options("line", specs, configured={"lw": 1})
    with pytest.raises(ValueError, match="duplicate option spelling"):
        bind_options(
            "line",
            (OptionSpec("linewidth", 1, aliases=("lw",)), OptionSpec("lw", 1)),
        )


def test_option_inputs_are_detached_and_operation_plan_is_consistent() -> None:
    """Mutable containers cannot alter a bound plan after validation."""

    source = {"levels": [1, 2], "omitted": MISSING}
    supplied = supplied_options(source)
    source["levels"].append(3)
    assert supplied == {"levels": (1, 2)}

    array = np.asarray([1, 2])
    default = {"labels": ["a", "b"], "levels": array}
    spec = OptionSpec("metadata", default)
    options = bind_options("paper", (spec,))
    default["labels"].append("c")
    array[0] = 99
    assert options["metadata"] == {"labels": ("a", "b"), "levels": (1, 2)}
    with pytest.raises(TypeError):
        options["metadata"]["other"] = ()
    with pytest.raises(FrozenInstanceError):
        options.entries = ()  # type: ignore[misc]

    _, axes = _figure_axes(1)
    target = normalize_axes(axes[0], operation="paper")
    operation = OperationPlan(operation="paper", target=target, options=options)
    assert operation.target is target
    with pytest.raises(ValueError, match="different operation"):
        OperationPlan(operation="line", target=target, options=options)
