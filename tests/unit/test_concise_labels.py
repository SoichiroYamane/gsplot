"""Tests for concise label, square, and panel-index operations."""

import inspect

import matplotlib.pyplot as plt
import pytest
from matplotlib.ticker import AutoMinorLocator, LogLocator

from gsplot._core import LayoutError, PlotError
from gsplot._style.axes import label, square
from gsplot._style.panels import index


def test_concise_label_and_index_signatures_publish_frozen_defaults() -> None:
    """Runtime introspection exposes user defaults instead of sentinels."""

    label_signature = inspect.signature(label)
    index_signature = inspect.signature(index)

    assert label_signature.parameters["xlabel"].default == ""
    assert label_signature.parameters["ylabel"].default == ""
    assert label_signature.parameters["minor"].default is True
    assert label_signature.parameters["pad"].default == 5
    assert label_signature.parameters["square"].default is False
    assert label_signature.parameters["index"].default is False
    assert index_signature.parameters["loc"].default == "out"
    assert index_signature.parameters["size"].default == "large"


def test_shared_labels_apply_publication_defaults_and_optional_helpers() -> None:
    """One concise call labels, squares, and indexes every explicit target."""

    figure, axes = plt.subplots(1, 2)
    try:
        label(
            axes,
            "time",
            "signal",
            xlim=(0, 2),
            ylim=(3, -1),
            xticks=(0, 1, 2),
            square=True,
            index="in",
        )

        assert all(axis.get_xlabel() == "time" for axis in axes)
        assert all(axis.get_ylabel() == "signal" for axis in axes)
        assert all(axis.get_xlim() == (0.0, 2.0) for axis in axes)
        assert all(axis.get_ylim() == (3.0, -1.0) for axis in axes)
        assert all(axis.xaxis.labelpad == 5 for axis in axes)
        assert all(axis.yaxis.labelpad == 5 for axis in axes)
        assert all(
            isinstance(axis.xaxis.minor.locator, AutoMinorLocator) for axis in axes
        )
        assert all(
            isinstance(axis.yaxis.minor.locator, AutoMinorLocator) for axis in axes
        )
        assert all(axis.get_box_aspect() == 1 for axis in axes)
        texts = tuple(axis.texts[0] for axis in axes)
        assert tuple(text.get_text() for text in texts) == ("(a)", "(b)")
        assert all(text.get_position() == (0, 1) for text in texts)
        assert all(text.get_ha() == "left" for text in texts)
        assert all(text.get_va() == "top" for text in texts)
    finally:
        plt.close(figure)


def test_ordered_and_exact_key_label_records_remain_explicit() -> None:
    """Per-target labels accept only ordered records or exact target keys."""

    figure, (first, second) = plt.subplots(1, 2)
    try:
        target = {"B": second, "A": first}
        label(
            target,
            {
                "B": ("bx", "by", (2, 0), None),
                "A": ("ax", "ay"),
            },
            minor=False,
            xpad=2,
            ypad=3,
        )
        assert second.get_xlabel() == "bx"
        assert second.get_ylabel() == "by"
        assert second.get_xlim() == (2.0, 0.0)
        assert first.get_xlabel() == "ax"
        assert first.get_ylabel() == "ay"
        assert first.xaxis.labelpad == 2
        assert first.yaxis.labelpad == 3

        label((first, second), [("left", "one"), ("right", "two")])
        assert (first.get_xlabel(), second.get_xlabel()) == ("left", "right")
    finally:
        plt.close(figure)


def test_label_preflight_rejects_ambiguous_records_and_invalid_domains() -> None:
    """A later invalid target value cannot partially mutate an earlier Axes."""

    figure, (first, second) = plt.subplots(1, 2)
    try:
        first.set_xlabel("before")
        with pytest.raises(LayoutError, match="record"):
            label((first, second), [("valid", "record"), ("invalid",)])
        assert first.get_xlabel() == "before"

        with pytest.raises(LayoutError, match="cannot be combined"):
            label((first, second), [("a", "b"), ("c", "d")], ylabel="extra")
        assert first.get_xlabel() == "before"

        second.plot([-1, 1], [1, 2])
        with pytest.raises(LayoutError, match="positive data"):
            label((first, second), "after", "value", xscale="log")
        assert first.get_xlabel() == "before"

        with pytest.raises((LayoutError, PlotError)):
            label((first, object()), "after", "value")  # type: ignore[list-item]
        assert first.get_xlabel() == "before"
    finally:
        plt.close(figure)


def test_label_uses_scale_aware_minor_tick_locators() -> None:
    """Log scales receive native log minor locators instead of linear locators."""

    figure, axis = plt.subplots()
    try:
        axis.plot([1, 10], [0.1, 0.9])
        label(axis, "x", "y", xscale="log", yscale="logit")
        assert isinstance(axis.xaxis.minor.locator, LogLocator)
        assert not isinstance(axis.yaxis.minor.locator, AutoMinorLocator)
    finally:
        plt.close(figure)


def test_square_and_index_validate_all_inputs_before_mutation() -> None:
    """Standalone helpers reject invalid values without partial artists."""

    figure, axes = plt.subplots(1, 2)
    try:
        with pytest.raises(LayoutError, match="positive"):
            square(axes, 0)
        assert all(axis.get_box_aspect() is None for axis in axes)

        with pytest.raises(PlotError, match="exactly"):
            index({"A": axes[0], "B": axes[1]}, {"A": "one"})
        assert all(not axis.texts for axis in axes)

        with pytest.raises(LayoutError, match="ordered sequence"):
            index(axes, "ab")
        with pytest.raises(LayoutError, match="conflicts"):
            index(axes, size=12, props={"fontsize": 10})
        for invalid_size in (True, 0, -1, float("nan"), float("inf"), None):
            with pytest.raises(LayoutError, match="size|fontsize"):
                index(axes, size=invalid_size)  # type: ignore[arg-type]
        assert all(not axis.texts for axis in axes)

        texts = index(axes, labels=("left", "right"), props={"fontsize": 9})
        assert tuple(text.get_text() for text in texts) == ("left", "right")
        assert all(text.get_fontsize() == 9 for text in texts)
        assert all(text.get_position() == (0, 6) for text in texts)
        assert all(text.get_ha() == "left" for text in texts)
        assert all(text.get_va() == "bottom" for text in texts)

        custom = index(
            axes[0],
            labels=("custom",),
            props={"horizontalalignment": "right", "verticalalignment": "center"},
        )
        assert custom.get_ha() == "right"
        assert custom.get_va() == "center"
    finally:
        plt.close(figure)


@pytest.mark.parametrize("dpi", (72, 144))
def test_index_default_origins_and_clearance_are_dpi_aware(dpi: int) -> None:
    """Outside follows the y-label left edge with a six-point top gap."""

    figure, (inside_axis, outside_axis) = plt.subplots(1, 2, dpi=dpi)
    try:
        outside_axis.set_ylabel("Signal (a.u.)")
        inside = index(inside_axis, loc="in")
        outside = index(outside_axis, loc="out")
        figure.canvas.draw()
        renderer = figure.canvas.get_renderer()
        inside_gap = 4 * dpi / 72
        outside_gap = 6 * dpi / 72

        inside_box = inside.get_window_extent(renderer)
        inside_axes_box = inside_axis.get_window_extent(renderer)
        assert inside_box.x0 - inside_axes_box.x0 == pytest.approx(inside_gap)
        assert inside_axes_box.y1 - inside_box.y1 == pytest.approx(inside_gap)

        outside_box = outside.get_window_extent(renderer)
        outside_axes_box = outside_axis.get_window_extent(renderer)
        ylabel_box = outside_axis.yaxis.label.get_window_extent(renderer)
        assert outside_box.x0 == pytest.approx(ylabel_box.x0)
        assert outside_box.y0 - outside_axes_box.y1 == pytest.approx(outside_gap)

        previous_x = outside_box.x0
        outside_axis.yaxis.labelpad += 10
        figure.canvas.draw()
        moved_box = outside.get_window_extent(renderer)
        moved_ylabel_box = outside_axis.yaxis.label.get_window_extent(renderer)
        assert moved_box.x0 == pytest.approx(moved_ylabel_box.x0)
        assert moved_box.x0 < previous_x
    finally:
        plt.close(figure)


def test_generated_index_labels_continue_bijectively_after_z() -> None:
    """Generated lowercase panel names continue as aa and ab."""

    figure, axes = plt.subplots(4, 7)
    try:
        texts = index(axes)
        assert texts[25].get_text() == "(z)"
        assert texts[26].get_text() == "(aa)"
        assert texts[27].get_text() == "(ab)"
    finally:
        plt.close(figure)
