"""Behavioral tests for the concise multi-target line and scatter API."""

import inspect
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.colors import to_rgba
from matplotlib.markers import MarkerStyle

import gsplot as gs
from gsplot._plot.series import SERIES_COLORS, SERIES_LINESTYLES, SERIES_MARKERS


def test_public_signatures_show_concise_defaults_without_private_sentinels() -> None:
    """Introspection presents the reviewed short API while runtime stays finite."""

    line_signature = inspect.signature(gs.line)
    scatter_signature = inspect.signature(gs.scatter)
    assert tuple(line_signature.parameters)[3:] == (
        "series",
        "label",
        "c",
        "marker",
        "ms",
        "mew",
        "mec",
        "mfc",
        "alpha_mfc",
        "ls",
        "lw",
        "alpha",
        "config",
        "props",
    )
    assert line_signature.parameters["marker"].default == "o"
    assert line_signature.parameters["ms"].default == 7
    assert line_signature.parameters["ls"].default == "--"
    assert tuple(scatter_signature.parameters)[3:] == (
        "series",
        "label",
        "c",
        "marker",
        "s",
        "alpha",
        "config",
        "props",
    )
    assert "omitted" not in str(line_signature)


def test_historical_defaults_use_each_target_axes_cycle() -> None:
    """Fixed visual defaults coexist with native line and patch color cycles."""

    figure, axis = gs.subplots(style=None)
    axis.set_prop_cycle(color=["red", "blue"])
    try:
        first = gs.line(axis, [0, 1], [0, 1])[0]
        second = gs.line(axis, [0, 1], [1, 2])[0]
        points = gs.scatter(axis, [0, 1], [0, 1])
        assert first.get_color() == "red"
        assert second.get_color() == "blue"
        assert first.get_marker() == "o"
        assert first.get_markersize() == 7
        assert first.get_markeredgewidth() == 1.5
        assert first.get_linestyle() == "--"
        assert first.get_linewidth() == 1
        assert first.get_alpha() == 1
        assert first.get_markeredgecolor() == "red"
        assert to_rgba(first.get_markerfacecolor())[3] == pytest.approx(0.2)
        assert np.allclose(points.get_facecolors()[0], to_rgba("red"))
        assert points.get_sizes().tolist() == [1]
        assert points.get_alpha() == 1
    finally:
        plt.close(figure)


def test_series_is_deterministic_and_does_not_advance_axes_cycles() -> None:
    """Series identities are pure and explicit options override their fields."""

    figure, axes = gs.subplots(1, 2, style=None)
    for axis in axes:
        axis.set_prop_cycle(color=["magenta", "cyan"])
    try:
        for index in range(10):
            artist = gs.line(axes[0], [0, 1], [index, index + 1], series=index)[0]
            assert np.allclose(to_rgba(artist.get_color()), SERIES_COLORS[index])
            probe = plt.Line2D([], [], linestyle=SERIES_LINESTYLES[index])
            assert artist.get_linestyle() == probe.get_linestyle()
            points = gs.scatter(axes[1], [index], [index], series=index)
            assert np.allclose(points.get_facecolors()[0], SERIES_COLORS[index])
            expected_marker = MarkerStyle(SERIES_MARKERS[index])
            expected_path = expected_marker.get_path().transformed(
                expected_marker.get_transform()
            )
            assert np.allclose(points.get_paths()[0].vertices, expected_path.vertices)

        assert gs.line(axes[0], [0, 1], [0, 1])[0].get_color() == "magenta"
        assert np.allclose(
            gs.scatter(axes[1], [0], [0]).get_facecolors()[0],
            to_rgba("magenta"),
        )
        overridden = gs.line(axes[0], [0, 1], [0, 1], series=4, c="black", ls=":")[0]
        assert overridden.get_color() == "black"
        assert overridden.get_linestyle() == ":"
        marked = gs.scatter(axes[1], [0], [0], series=4, marker="s")
        expected_marker = MarkerStyle("s")
        expected_path = expected_marker.get_path().transformed(
            expected_marker.get_transform()
        )
        assert np.allclose(marked.get_paths()[0].vertices, expected_path.vertices)
    finally:
        plt.close(figure)


def test_multi_target_broadcast_and_exact_mappings_preserve_target_order() -> None:
    """Data and styles resolve completely before returning native target results."""

    figure, axes = gs.subplots(1, 2, style=None)
    targets = {"left": axes[0], "right": axes[1]}
    x = {"left": [0, 1], "right": [10, 20]}
    y = {"left": [1, 2], "right": [3, 4]}
    try:
        lines = gs.line(
            targets,
            x,
            y,
            series=[0, 1],
            label=["L", "R"],
            c={"left": "red", "right": "blue"},
            marker=["o", "s"],
            lw=[1, 2],
        )
        assert isinstance(lines, tuple)
        assert [item[0].axes for item in lines] == list(targets.values())
        assert [item[0].get_label() for item in lines] == ["L", "R"]
        assert [item[0].get_color() for item in lines] == ["red", "blue"]
        assert [item[0].get_linewidth() for item in lines] == [1, 2]
        assert np.array_equal(lines[1][0].get_xdata(), [10, 20])

        points = gs.scatter(
            targets,
            [0, 1],
            [1, 0],
            marker=["^", "D"],
            c={"left": "black", "right": "gray"},
            s=[3, 5],
        )
        assert isinstance(points, tuple)
        assert [item.axes for item in points] == list(targets.values())
        assert [item.get_sizes()[0] for item in points] == [3, 5]
    finally:
        plt.close(figure)


def test_omission_and_explicit_default_values_control_config_precedence() -> None:
    """The hidden binder distinguishes omitted c from an explicit None value."""

    config = gs.Config.from_mapping(
        {"schema_version": 2, "plotting": {"default_color": "red"}}
    )
    figure, axis = gs.subplots(style=None)
    axis.set_prop_cycle(color=["blue"])
    try:
        assert gs.line(axis, [0, 1], [0, 1], config=config)[0].get_color() == "red"
        assert (
            gs.line(axis, [0, 1], [0, 1], c=None, config=config)[0].get_color()
            == "blue"
        )
        assert (
            gs.line(axis, [0, 1], [0, 1], c="red", config=config)[0].get_color()
            == "red"
        )
    finally:
        plt.close(figure)


def test_marker_face_alpha_and_retained_advanced_options_are_explicit() -> None:
    """Marker faces retain 0.x alpha semantics and long options remain usable."""

    figure, axis = gs.subplots(style=None)
    try:
        line = gs.line(
            axis,
            [0, 1],
            [0, 1],
            color="blue",
            markerfacecolor="red",
            alpha=0.5,
            alpha_mfc=0.4,
            markersize=3,
            antialiased=False,
        )[0]
        assert np.allclose(to_rgba(line.get_markerfacecolor()), (1, 0, 0, 0.2))
        assert line.get_markersize() == 3
        assert not line.get_antialiased()
        no_fill = gs.line(axis, [0, 1], [1, 2], mfc="none")[0]
        assert no_fill.get_markerfacecolor() == "none"

        points = gs.scatter(axis, [0, 1], [0, 1], size=4, c=[0.0, 1.0])
        assert points.get_sizes().tolist() == [4]
        assert np.array_equal(points.get_array(), [0.0, 1.0])
    finally:
        plt.close(figure)


def test_concise_scatter_color_avoids_matplotlib_c_ambiguity() -> None:
    """A color-like c value routes to color while numeric arrays retain c data."""

    figure, axis = gs.subplots(style=None)
    try:
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            points = gs.scatter(axis, [0, 1], [0, 1], c=(1.0, 0.0, 0.0))
        assert not captured
        assert np.allclose(points.get_facecolors()[0], to_rgba("red"))
    finally:
        plt.close(figure)


def test_all_multi_target_failures_are_atomic() -> None:
    """Data, mapping, alias, props, style, and Figure failures add no artists."""

    first_figure, axes = gs.subplots(1, 2, style=None)
    second_figure, other = gs.subplots(style=None)
    cases = (
        lambda: gs.line(axes, [0, 1], [0, 1], lw=[1, np.nan]),
        lambda: gs.line(axes, [0, 1], [0, 1], series=[0, 10]),
        lambda: gs.line(
            {"a": axes[0], "b": axes[1]},
            {"a": [0, 1]},
            {"a": [0, 1]},
        ),
        lambda: gs.line(axes, [0, 1], [0, 1], c="red", color="blue"),
        lambda: gs.line(axes, [0, 1], [0, 1], c="red", props={"color": "blue"}),
        lambda: gs.scatter(axes, [0, 1], [0, 1], c="red", props={"c": "blue"}),
        lambda: gs.scatter(axes, [0, 1], [0, 1], color="red", facecolors="blue"),
        lambda: gs.line([axes[0], other], [0, 1], [0, 1]),
    )
    try:
        for case in cases:
            with pytest.raises((gs.DataError, gs.PlotError, TypeError)):
                case()
            assert not axes[0].lines
            assert not axes[1].lines
            assert not axes[0].collections
            assert not axes[1].collections
    finally:
        plt.close(first_figure)
        plt.close(second_figure)
