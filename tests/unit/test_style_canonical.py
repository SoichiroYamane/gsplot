"""Tests for explicit layout, styling, legend, and theme adapters."""

import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest
from matplotlib.legend import Legend

from gsplot._core import AxisSpec, InsetSpec, LayoutError, PlotError, Theme
from gsplot._figure.inset import inset_axes
from gsplot._plot.basic import line
from gsplot._style.axes import box_aspect, minor_ticks, style_axes, suptitle, title
from gsplot._style.legends import cmap_legend, legend, legend_entries, legends
from gsplot._style.panels import panel_labels
from gsplot._style.paper import PAPER_CYCLE_RGBA, paper
from gsplot._style.themes import fig_facecolor, set_theme


def test_explicit_inset_and_axes_styling() -> None:
    """Inset creation and style operations stay attached to explicit targets."""

    figure, (first, second) = plt.subplots(1, 2)
    child = inset_axes(first, InsetSpec(bounds=(0.1, 0.1, 0.4, 0.4)))
    assert child.figure is figure
    assert child in first.child_axes
    style_axes(
        {"first": first, "second": second},
        AxisSpec(xlabel="time", xlim=(0, 2), xminor=True),
    )
    assert first.get_xlabel() == "time"
    assert first.get_xlim() == (0.0, 2.0)
    minor_ticks(second, False, axis="both")
    box_aspect([first, second], 1)
    assert first.get_box_aspect() == 1
    with pytest.raises(LayoutError):
        style_axes([first, object()], AxisSpec(xlabel="must not apply"))  # type: ignore[list-item]
    assert first.get_xlabel() == "time"
    plt.close(figure)


def test_titles_panel_labels_and_explicit_themes() -> None:
    """Text and theme helpers mutate only the supplied Figure/Axes."""

    figure, axes = plt.subplots(1, 2)
    axes_array = tuple(axes)
    assert title(axes_array[0], "Panel").get_text() == "Panel"
    assert suptitle(figure, "Experiment").get_text() == "Experiment"
    labels = panel_labels(axes_array)
    assert tuple(item.get_text() for item in labels) == ("A", "B")
    before = mpl.rcParams["axes.facecolor"]
    set_theme(figure, Theme.transparent())
    assert figure.patch.get_facecolor()[-1] == 0
    assert mpl.rcParams["axes.facecolor"] == before
    fig_facecolor(figure, "white")
    assert figure.patch.get_facecolor()[:3] == (1.0, 1.0, 1.0)
    with pytest.raises(PlotError):
        set_theme(axes_array[0], Theme(figure_facecolor="black"))
    plt.close(figure)


def test_rendered_panel_label_locations_require_one_figure() -> None:
    """Rendered panel labels use Figure coordinates and reject mixed targets."""

    figure, axes = plt.subplots(1, 2)
    other_figure, other_axis = plt.subplots()
    try:
        inside = panel_labels(tuple(axes), labels=("(a)", "(b)"), loc="in")
        outside = panel_labels(tuple(axes), labels=("A", "B"), loc="out")

        assert all(text.figure is figure for text in inside + outside)
        assert all(text.get_transform() is figure.transFigure for text in inside)
        assert all(text.get_transform() is figure.transFigure for text in outside)
        with pytest.raises(LayoutError, match="loc"):
            panel_labels(tuple(axes), loc="left")
        with pytest.raises(LayoutError, match="one Figure"):
            panel_labels((axes[0], other_axis), loc="in")
    finally:
        plt.close(figure)
        plt.close(other_figure)


def test_legends_are_local_and_require_explicit_replacement() -> None:
    """Legend construction never replaces an existing legend by default."""

    figure, axes = plt.subplots(1, 2)
    line(axes[0], [0, 1], [0, 1], props={"label": "one"})
    line(axes[1], [0, 1], [1, 0], props={"label": "two"})
    entries = legend_entries(axes[0])
    assert entries.labels == ("one",)
    created = legend(axes[0])
    assert isinstance(created, Legend)
    with pytest.raises(LayoutError, match="replace"):
        legend(axes[0])
    replaced = legend(axes[0], replace=True)
    assert isinstance(replaced, Legend)
    collection = legends(figure, replace=True)
    assert len(collection) == 2
    with pytest.raises(LayoutError, match="replace"):
        cmap_legend(axes[0], label="range")
    cmap = cmap_legend(axes[0], label="range", replace=True, stripes=3)
    assert isinstance(cmap, Legend)
    bounded = cmap_legend(axes[1], norm=(0, 1), stripes=3, replace=True)
    assert isinstance(bounded, Legend)
    plt.close(figure)


def test_paper_applies_the_frozen_profile_without_global_state() -> None:
    """Paper styling matches the golden target and leaves rcParams untouched."""

    before = mpl.rcParams.copy()
    figure, axis = plt.subplots()
    original_figure_face = figure.get_facecolor()
    paper(axis)

    assert figure.get_facecolor() == original_figure_face
    assert axis.get_facecolor() == (1.0, 1.0, 1.0, 1.0)
    assert axis.margins() == (0.0, 0.0)
    assert axis.xaxis.labelpad == 6
    assert axis.yaxis.labelpad == 6
    assert all(spine.get_visible() for spine in axis.spines.values())
    assert all(
        spine.get_edgecolor() == (0.0, 0.0, 0.0, 1.0) for spine in axis.spines.values()
    )
    assert all(spine.get_linewidth() == 0.8 for spine in axis.spines.values())
    assert axis.xaxis._major_tick_kw["tickdir"] == "in"
    assert axis.xaxis._major_tick_kw["size"] == 3.5
    assert axis.xaxis._major_tick_kw["width"] == 0.8
    assert axis.xaxis._major_tick_kw["pad"] == 6
    assert axis.xaxis._minor_tick_kw["size"] == 2
    assert axis.xaxis._minor_tick_kw["width"] == 0.6
    assert axis.xaxis.label.get_fontfamily() == ["DejaVu Sans"]
    assert all(
        label.get_fontfamily() == ["DejaVu Sans"]
        for label in (
            *axis.get_xticklabels(which="both"),
            *axis.get_yticklabels(which="both"),
        )
    )
    assert axis.xaxis.label.get_fontsize() == 10

    lines = [
        axis.plot([0.23, 0.77], [index + 1.2, index + 1.7])[0] for index in range(5)
    ]
    assert tuple(line.get_color() for line in lines) == PAPER_CYCLE_RGBA
    assert axis.get_xlim() == (0.2, 0.8)
    assert dict(mpl.rcParams) == dict(before)
    plt.close(figure)


def test_paper_validates_every_axis_before_mutating_any_axis() -> None:
    """Cycle conflicts and invalid targets fail atomically."""

    figure, (first, second) = plt.subplots(1, 2)
    second.plot([0, 1], [0, 1])
    first.set_facecolor("red")
    with pytest.raises(PlotError, match="cycle=True"):
        paper((first, second))
    assert first.get_facecolor() == (1.0, 0.0, 0.0, 1.0)

    paper((first, second), cycle=False)
    assert first.get_facecolor() == (1.0, 1.0, 1.0, 1.0)
    with pytest.raises(PlotError, match="cycle"):
        paper(first, cycle=1)  # type: ignore[arg-type]
    plt.close(figure)
