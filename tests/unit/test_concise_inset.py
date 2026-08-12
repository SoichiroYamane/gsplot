"""Tests for concise inset placement, styling, zoom, and compatibility."""

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.axes import Axes
from mpl_toolkits.axes_grid1.inset_locator import BboxConnector, BboxPatch

import gsplot as gs


def test_inset_applies_paper_labels_and_normalized_layering() -> None:
    """The concise default combines placement and common publication setup."""

    figure, parent = plt.subplots(layout="constrained")
    figure.canvas.draw()
    parent_position = parent.get_position().bounds
    try:
        child = gs.inset(
            parent,
            (0.55, 0.55, 0.4, 0.4),
            label=("time", "signal", (1, 2), (-1, 1)),
            zoom=((1, 2), (4, 3)),
        )
        figure.canvas.draw()

        assert isinstance(child, Axes)
        assert child.figure is figure
        assert child in parent.child_axes
        assert child.get_zorder() == 5
        assert child.get_xlabel() == "time"
        assert child.get_ylabel() == "signal"
        assert child.get_xlim() == (1.0, 2.0)
        assert child.get_ylim() == (-1.0, 1.0)
        assert child.xaxis.labelpad == 0
        assert child.yaxis.labelpad == 0
        assert child.get_facecolor() == (1.0, 1.0, 1.0, 1.0)
        assert np.allclose(parent.get_position().bounds, parent_position)

        indicator = parent.patches[-3:]
        assert isinstance(indicator[0], BboxPatch)
        assert all(isinstance(item, BboxConnector) for item in indicator[1:])
        assert all(item.axes is parent for item in indicator)
        assert all(item.get_zorder() == pytest.approx(4.99) for item in indicator)
        assert all(not item.get_in_layout() for item in indicator)
        assert all(not item.get_clip_on() for item in indicator[1:])
        assert tuple((item.loc2, item.loc1) for item in indicator[1:]) == (
            (1, 2),
            (4, 3),
        )

        before = indicator[0].get_path().vertices.copy()
        child.set_xlim(1.25, 1.75)
        after = indicator[0].get_path().vertices.copy()
        assert not np.array_equal(after, before)
    finally:
        plt.close(figure)


def test_inset_supports_automatic_zoom_advanced_placement_and_explicit_layers() -> None:
    """Automatic indicators and advanced placement share the concise layers."""

    figure, parent = plt.subplots()
    before = set(parent.get_children())
    try:
        child = gs.inset(
            parent,
            gs.InsetSpec(width="25%", height="25%"),
            zoom=True,
            style=None,
            zorder=8,
            zoom_zorder=7,
        )
        created = set(parent.get_children()) - before
        assert child.get_zorder() == 8
        indicators = tuple(item for item in created if item is not child)
        assert indicators
        assert all(item.get_zorder() == 7 for item in indicators)
        assert all(not item.get_in_layout() for item in indicators)
    finally:
        plt.close(figure)


@pytest.mark.parametrize(
    "options",
    (
        {"bounds": [0.5, 0.5, 0.4, 0.4]},
        {"bounds": (-0.1, 0.5, 0.4, 0.4)},
        {"bounds": (0.7, 0.5, 0.4, 0.4)},
        {"bounds": (True, 0.5, 0.4, 0.4)},
        {"bounds": (0.5, 0.5, 0.4, 0.4), "label": ("x",)},
        {"bounds": (0.5, 0.5, 0.4, 0.4), "zoom": ((1, 2), (4, 5))},
        {"bounds": (0.5, 0.5, 0.4, 0.4), "zoom": ((1, 2), (1, 2))},
        {"bounds": (0.5, 0.5, 0.4, 0.4), "style": "screen"},
        {"bounds": (0.5, 0.5, 0.4, 0.4), "style": []},
        {"bounds": (0.5, 0.5, 0.4, 0.4), "zorder": np.inf},
        {"bounds": (0.5, 0.5, 0.4, 0.4), "zoom_zorder": 3},
    ),
)
def test_inset_rejects_invalid_plans_before_creating_a_child(options: dict) -> None:
    """Every concise option is preflighted before Matplotlib is mutated."""

    figure, parent = plt.subplots()
    try:
        before_children = tuple(parent.child_axes)
        before_patches = tuple(parent.patches)
        selected = dict(options)
        bounds = selected.pop("bounds")
        with pytest.raises(gs.LayoutError, match="inset"):
            gs.inset(parent, bounds, **selected)
        assert tuple(parent.child_axes) == before_children
        assert tuple(parent.patches) == before_patches
    finally:
        plt.close(figure)


def test_legacy_root_insets_honor_explicit_zoom_corner_pairs() -> None:
    """Root compatibility adapters retain requested connector pairs and layers."""

    figure, parent = plt.subplots()
    try:
        with pytest.deprecated_call():
            child = gs.axes_inset(
                parent,
                (0.5, 0.5, 0.4, 0.4),
                zoom=((1, 2), (4, 3)),
            )
        indicator = parent.patches[-3:]
        assert child.figure is figure
        assert isinstance(indicator[0], BboxPatch)
        assert all(isinstance(item, BboxConnector) for item in indicator[1:])
        assert all(item.get_zorder() == 1 for item in indicator)

        with pytest.deprecated_call():
            anchored = gs.axes_inset_padding(
                parent,
                "25%",
                "25%",
                zoom=((1, 2), (4, 3)),
            )
        anchored_indicator = parent.patches[-3:]
        assert anchored.figure is figure
        assert all(item.get_zorder() == 1 for item in anchored_indicator)
    finally:
        plt.close(figure)
