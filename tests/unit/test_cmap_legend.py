"""Regression tests for canonical and legacy colormap legends."""

from __future__ import annotations

import os
import pickle
import subprocess
import sys
import textwrap
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.colors import ListedColormap, Normalize
from matplotlib.legend import Legend
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

import gsplot as gs
import gsplot._style.legends as legends_module
from gsplot._core.errors import LayoutError, OptionError, PlotError
from gsplot._style.legends import cmap_legend, legend, legends


def _handler_rectangles(legend: Legend) -> list[Rectangle]:
    """Return handler-created rectangles while excluding the legend frame."""

    frame = legend.get_frame()
    return sorted(
        [artist for artist in legend.findobj(match=Rectangle) if artist is not frame],
        key=lambda artist: artist.get_x(),
    )


def test_cmap_legend_uses_one_gradient_entry() -> None:
    """A canonical colormap legend is one entry containing stripe rectangles."""

    figure, axis = plt.subplots()
    try:
        item = cmap_legend(axis, label="range", stripes=3)
        figure.canvas.draw()

        assert isinstance(item, Legend)
        assert len(item.legend_handles) == 1
        assert len(item.get_texts()) == 1
        assert len(_handler_rectangles(item)) == 3
        assert item.findobj(match=Line2D) == []
        assert sum(child is item for child in axis.get_children()) == 1
        assert axis.get_legend() is item
    finally:
        plt.close(figure)


def _facecolors(legend: Legend) -> np.ndarray:
    """Return handler rectangle colors in rendered left-to-right order."""

    return np.asarray(
        [artist.get_facecolor() for artist in _handler_rectangles(legend)]
    )


def test_cmap_legend_samples_then_reverses_with_an_asymmetric_norm() -> None:
    """Reverse applies to sampled RGBA rows, not to the colormap object."""

    colormap = ListedColormap(
        ((0.1, 0.2, 0.3, 1.0), (0.4, 0.5, 0.6, 1.0), (0.7, 0.8, 0.9, 1.0)),
        name="cmap_legend_test",
    )
    normalizer = Normalize(vmin=0, vmax=2)
    original_bounds = (normalizer.vmin, normalizer.vmax)
    figure, axis = plt.subplots()
    try:
        item = cmap_legend(
            axis,
            cmap=colormap,
            stripes=3,
            norm=normalizer,
            reverse=True,
            label="range",
        )
        figure.canvas.draw()

        expected = np.asarray(colormap([0.0, 0.25, 0.5]))[::-1]
        np.testing.assert_allclose(_facecolors(item), expected, rtol=0, atol=1e-12)
        assert (normalizer.vmin, normalizer.vmax) == original_bounds
    finally:
        plt.close(figure)


def test_cmap_legend_label_none_returns_empty_legend_and_obeys_replacement() -> None:
    """An unlabeled canonical call has no entries and follows replace policy."""

    figure, axis = plt.subplots()
    try:
        empty = cmap_legend(axis, label=None)
        assert empty.legend_handles == []
        assert empty.get_texts() == []
        assert _handler_rectangles(empty) == []
        with pytest.raises(LayoutError, match="replace"):
            cmap_legend(axis, label=None)
        replaced = cmap_legend(axis, label=None, replace=True)
        assert replaced is not empty
        assert axis.get_legend() is replaced
    finally:
        plt.close(figure)


@pytest.mark.parametrize("value", [0, -1, True, 1.5, "3", None])
def test_cmap_legend_rejects_invalid_stripe_counts(value: object) -> None:
    """Invalid stripe counts fail before creating a Legend."""

    figure, axis = plt.subplots()
    try:
        with pytest.raises(PlotError, match="stripes"):
            cmap_legend(axis, stripes=value)  # type: ignore[arg-type]
        assert axis.get_legend() is None
    finally:
        plt.close(figure)


def test_cmap_legend_clamps_large_counts() -> None:
    """Canonical stripe construction is bounded at 256 rectangles."""

    figure, axis = plt.subplots()
    try:
        item = cmap_legend(axis, label="range", stripes=300)
        figure.canvas.draw()
        assert len(_handler_rectangles(item)) == 256
    finally:
        plt.close(figure)


def test_cmap_legend_does_not_mutate_default_handler_map_or_axes_patches() -> None:
    """The local handler stays isolated from Matplotlib global and Axes state."""

    before_handlers = dict(Legend.get_default_handler_map())
    figure, axis = plt.subplots()
    try:
        before_patches = tuple(axis.patches)
        item = cmap_legend(axis, label="range", stripes=3)
        figure.canvas.draw()

        after_handlers = dict(Legend.get_default_handler_map())
        assert after_handlers.keys() == before_handlers.keys()
        assert all(
            after_handlers[key] is before_handlers[key] for key in before_handlers
        )
        assert tuple(axis.patches) == before_patches
        assert sum(child is item for child in axis.get_children()) == 1
        assert axis.get_legend() is item
    finally:
        plt.close(figure)


def test_ordinary_legend_and_legends_attach_once_and_remove_cleanly() -> None:
    """All canonical Legend helpers use one native attachment path."""

    figure, axes = plt.subplots(1, 2)
    try:
        axes[0].plot([0, 1], [0, 1], label="one")
        axes[1].plot([0, 1], [1, 0], label="two")
        item = legend(axes[0])
        assert sum(child is item for child in axes[0].get_children()) == 1
        item.remove()
        assert axes[0].get_legend() is None

        items = legends(figure)
        assert len(items) == 2
        assert all(
            sum(child is created for child in axis.get_children()) == 1
            for axis, created in zip(axes, items)
        )
    finally:
        plt.close(figure)


def test_legacy_root_uses_raw_bounds_and_unconditional_replacement() -> None:
    """The root legacy route preserves v0.2.0 sampling and replacement."""

    figure, axis = plt.subplots()
    try:
        with pytest.warns(
            DeprecationWarning,
            match=r"gsplot\.legend_colormap is deprecated; use cmap_legend",
        ):
            first = gs.legend_colormap(
                axis,
                cmap="viridis",
                label="range",
                num_stripes=3,
                vmin=0,
                vmax=100,
            )
        figure.canvas.draw()

        expected = mpl.colormaps.get_cmap("viridis")(np.linspace(0, 100, 3))
        np.testing.assert_allclose(_facecolors(first), expected, rtol=0, atol=1e-12)
        assert len(first.legend_handles) == 1
        assert len(_handler_rectangles(first)) == 3

        with pytest.warns(DeprecationWarning):
            second = gs.legend_colormap(axis, label=None, num_stripes=3)
        assert second is not first
        assert second.legend_handles == []
        assert axis.get_legend() is second
    finally:
        plt.close(figure)


def test_canonical_and_legacy_legend_styles_use_their_declared_defaults() -> None:
    """Canonical defaults stay fixed while legacy defaults read rcParams."""

    figure, (canonical_axis, legacy_axis) = plt.subplots(1, 2)
    try:
        with mpl.rc_context(
            {
                "legend.frameon": True,
                "legend.fancybox": True,
                "legend.labelspacing": 1.7,
            }
        ):
            canonical = cmap_legend(canonical_axis, label="range")
            with pytest.warns(DeprecationWarning):
                legacy = gs.legend_colormap(legacy_axis, label="range")
        assert canonical.get_frame_on() is False
        assert type(canonical.get_frame().get_boxstyle()).__name__ == "Square"
        assert canonical.labelspacing == 0.3
        assert legacy.get_frame_on() is True
        assert type(legacy.get_frame().get_boxstyle()).__name__ == "Round"
        assert legacy.labelspacing == 1.7
    finally:
        plt.close(figure)


def test_cmap_legend_clips_out_of_range_normalizer_results_after_validation() -> None:
    """Finite normalizer output is clipped only after shape/finiteness checks."""

    class OutOfRangeNormalizer:
        """Return finite values outside the colormap domain."""

        def __call__(
            self, values: object, clip: bool | None = None
        ) -> np.ndarray[Any, Any]:
            del clip
            return np.linspace(-0.5, 1.5, len(values))  # type: ignore[arg-type]

    figure, axis = plt.subplots()
    try:
        item = cmap_legend(
            axis,
            cmap="viridis",
            stripes=3,
            norm=OutOfRangeNormalizer(),  # type: ignore[arg-type]
            label="range",
        )
        figure.canvas.draw()
        expected = mpl.colormaps.get_cmap("viridis")([0.0, 0.5, 1.0])
        np.testing.assert_allclose(_facecolors(item), expected, rtol=0, atol=1e-12)
    finally:
        plt.close(figure)


@pytest.mark.parametrize(
    "normalizer",
    [
        lambda values, *, clip=False: np.asarray(values)[:-1],
        lambda values, *, clip=False: np.array([0.0, np.nan, 1.0]),
    ],
)
def test_cmap_legend_rejects_invalid_normalizer_results(normalizer) -> None:
    """Wrong-shape or non-finite normalizer output fails before attachment."""

    figure, axis = plt.subplots()
    try:
        with pytest.raises(PlotError, match="norm"):
            cmap_legend(axis, norm=normalizer, stripes=3, label="range")
        assert axis.get_legend() is None
    finally:
        plt.close(figure)


def test_cmap_legend_rejects_unbound_normalizer_and_unknown_properties() -> None:
    """Invalid normalization and closed property schemas are preflighted."""

    figure, axis = plt.subplots()
    try:
        with pytest.raises(PlotError, match="norm bounds"):
            cmap_legend(axis, norm=Normalize(), label="range")
        with pytest.raises(OptionError, match="unknown"):
            cmap_legend(axis, label="range", unknown_legend_option=True)
        assert axis.get_legend() is None
    finally:
        plt.close(figure)


def test_deprecated_module_route_has_separate_import_and_call_warnings() -> None:
    """The historical module warns twice on import and once on call."""

    script = textwrap.dedent("""
        import importlib
        import warnings
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
        import gsplot as gs

        with warnings.catch_warnings(record=True) as import_warnings:
            warnings.simplefilter("always")
            module = importlib.import_module("gsplot.style.legend_colormap")
        assert len(import_warnings) == 2
        assert all(item.category is DeprecationWarning for item in import_warnings)
        assert {str(item.message) for item in import_warnings} == {
            "gsplot.style is a deprecated compatibility module; migrate to the canonical gsplot root API",
            "gsplot.style.legend_colormap is a deprecated compatibility module; migrate to the canonical gsplot root API",
        }
        assert module.legend_colormap is gs.legend_colormap

        figure, axis = plt.subplots()
        with warnings.catch_warnings(record=True) as call_warnings:
            warnings.simplefilter("always")
            item = module.legend_colormap(axis, label="range", num_stripes=3)
        assert len(call_warnings) == 1
        assert call_warnings[0].category is DeprecationWarning
        assert str(call_warnings[0].message) == "gsplot.legend_colormap is deprecated; use cmap_legend"
        figure.canvas.draw()
        rectangles = [
            artist for artist in item.findobj(match=Rectangle)
            if artist is not item.get_frame()
        ]
        assert len(item.legend_handles) == 1
        assert len(rectangles) == 3
        assert sum(child is item for child in axis.get_children()) == 1
        plt.close(figure)
        """)
    environment = os.environ.copy()
    environment["MPLBACKEND"] = "Agg"
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert result.returncode == 0, result.stderr


def test_cmap_legend_one_stripe_uses_the_first_sampled_color() -> None:
    """A one-stripe legend does not sample an implicit midpoint."""

    figure, axis = plt.subplots()
    try:
        item = cmap_legend(axis, cmap="viridis", stripes=1, label="range")
        figure.canvas.draw()
        expected = mpl.colormaps.get_cmap("viridis")([0.0])
        np.testing.assert_allclose(_facecolors(item), expected, rtol=0, atol=1e-12)
    finally:
        plt.close(figure)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"cmap": ""},
        {"cmap": object()},
        {"reverse": 1},
        {"norm": (0.0, 0.0)},
        {"norm": (1.0, 0.0)},
        {"norm": (0.0, np.nan)},
    ],
)
def test_cmap_legend_rejects_invalid_cmap_controls(kwargs) -> None:
    """Invalid colormap controls fail before changing the Axes."""

    figure, axis = plt.subplots()
    try:
        with pytest.raises(PlotError):
            cmap_legend(axis, label="range", **kwargs)
        assert axis.get_legend() is None
    finally:
        plt.close(figure)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"num_stripes": True},
        {"num_stripes": 3.0},
        {"num_stripes": "3"},
        {"num_stripes": None},
        {"vmin": True},
        {"vmax": "1"},
        {"vmin": np.inf},
        {"reverse": 1},
        {"cmap": object()},
    ],
)
def test_legacy_colormap_rejects_invalid_controls(kwargs) -> None:
    """Legacy input validation rejects non-historical scalar types early."""

    figure, axis = plt.subplots()
    try:
        with pytest.warns(DeprecationWarning):
            with pytest.raises(PlotError):
                gs.legend_colormap(axis, label="range", **kwargs)
        assert axis.get_legend() is None
    finally:
        plt.close(figure)


def test_cmap_legend_validates_properties_before_replacing_existing_legend() -> None:
    """Invalid replacement properties leave the current Legend untouched."""

    figure, axis = plt.subplots()
    try:
        current = cmap_legend(axis, label="old")
        with pytest.raises(OptionError, match="unknown"):
            cmap_legend(
                axis,
                label="new",
                replace=True,
                props={"not_a_legend_property": True},
            )
        assert axis.get_legend() is current
    finally:
        plt.close(figure)


def test_legacy_raw_sampling_preserves_custom_under_and_over_colors() -> None:
    """Legacy raw values reach the colormap's configured under/over colors."""

    name = "_gsplot_cmap_legend_under_over"
    colormap = ListedColormap(
        ((0.1, 0.2, 0.3, 1.0), (0.4, 0.5, 0.6, 1.0), (0.7, 0.8, 0.9, 1.0)),
        name=name,
    )
    colormap.set_under((1.0, 0.0, 0.0, 1.0))
    colormap.set_over((0.0, 0.0, 1.0, 1.0))
    mpl.colormaps.register(colormap, name=name)
    figure, axis = plt.subplots()
    try:
        with pytest.warns(DeprecationWarning):
            item = gs.legend_colormap(
                axis,
                cmap=name,
                label="range",
                num_stripes=3,
                vmin=-1,
                vmax=2,
            )
        figure.canvas.draw()
        expected = mpl.colormaps.get_cmap(name)(np.linspace(-1, 2, 3))
        np.testing.assert_allclose(_facecolors(item), expected, rtol=0, atol=1e-12)
    finally:
        mpl.colormaps.unregister(name)
        plt.close(figure)


def test_legacy_count_clamp_happens_before_sampling() -> None:
    """Counts 256 and 257 produce the same bounded color sequence."""

    figure, (first_axis, second_axis) = plt.subplots(1, 2)
    try:
        with pytest.warns(DeprecationWarning):
            first = gs.legend_colormap(first_axis, label="range", num_stripes=256)
        with pytest.warns(DeprecationWarning):
            second = gs.legend_colormap(second_axis, label="range", num_stripes=257)
        figure.canvas.draw()
        np.testing.assert_allclose(
            _facecolors(first), _facecolors(second), rtol=0, atol=1e-12
        )
        assert len(_handler_rectangles(second)) == 256
    finally:
        plt.close(figure)


def test_cmap_legend_direct_kwargs_override_props() -> None:
    """Direct Legend keywords retain precedence over the property mapping."""

    figure, axis = plt.subplots()
    try:
        item = cmap_legend(
            axis,
            label="range",
            props={"frameon": False},
            frameon=True,
        )
        assert item.get_frame_on() is True
        with pytest.raises(OptionError, match="both"):
            cmap_legend(axis, label="new", replace=True, props={"ncol": 1, "ncols": 1})
    finally:
        plt.close(figure)


def test_cmap_legend_pickle_round_trip_keeps_local_handler() -> None:
    """A pickled Figure redraws its local colormap handler."""

    figure, axis = plt.subplots()
    restored = None
    try:
        cmap_legend(axis, label="range", stripes=3)
        figure.canvas.draw()
        # Safe self-round-trip: bytes are produced from this in-memory Figure above.
        restored = pickle.loads(pickle.dumps(figure))
        restored.canvas.draw()
        restored_legend = restored.axes[0].get_legend()
        assert restored_legend is not None
        assert len(_handler_rectangles(restored_legend)) == 3
    finally:
        plt.close(figure)
        if restored is not None:
            plt.close(restored)


def test_cmap_legend_vector_backends_draw_and_save(tmp_path) -> None:
    """Agg, PDF, and SVG subprocesses draw the custom handler successfully."""

    script = textwrap.dedent("""
        import sys
        import matplotlib.pyplot as plt
        from matplotlib.lines import Line2D
        from matplotlib.patches import Rectangle
        from gsplot import cmap_legend

        figure, axis = plt.subplots()
        item = cmap_legend(axis, label="range", stripes=3)
        figure.canvas.draw()
        rectangles = [
            artist for artist in item.findobj(match=Rectangle)
            if artist is not item.get_frame()
        ]
        assert len(rectangles) == 3
        assert item.findobj(match=Line2D) == []
        figure.savefig(sys.argv[1])
        plt.close(figure)
        """)
    for backend, suffix in (("Agg", ".png"), ("pdf", ".pdf"), ("svg", ".svg")):
        output = tmp_path / f"legend-{backend}{suffix}"
        environment = os.environ.copy()
        environment["MPLBACKEND"] = backend
        result = subprocess.run(
            [sys.executable, "-c", script, str(output)],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )
        assert result.returncode == 0, result.stderr
        assert output.stat().st_size > 0


def test_legends_attachment_failure_restores_all_previous_legends(monkeypatch) -> None:
    """Multi-Axes legend creation is atomic when attachment fails."""

    figure, axes = plt.subplots(1, 2)
    try:
        axes[0].plot([0, 1], [0, 1], label="one")
        axes[1].plot([0, 1], [1, 0], label="two")
        previous = legends(figure)

        original_attach = legends_module._attach_legend

        def fail_second(axis, item):
            if axis is axes[1]:
                raise RuntimeError("injected attachment failure")
            original_attach(axis, item)

        monkeypatch.setattr(legends_module, "_attach_legend", fail_second)
        with pytest.raises(RuntimeError, match="injected"):
            legends(figure, replace=True)

        assert tuple(axis.get_legend() for axis in axes) == previous
        assert all(
            sum(child is item for child in axis.get_children()) == 1
            for axis, item in zip(axes, previous)
        )
    finally:
        plt.close(figure)


def test_legacy_colormap_accepts_positional_descending_and_reverse_arguments() -> None:
    """Historical positional arguments preserve descending raw sample order."""

    figure, axis = plt.subplots()
    try:
        with pytest.warns(DeprecationWarning):
            item = gs.legend_colormap(axis, "viridis", "range", 3, 1, 0, True)
        figure.canvas.draw()
        expected = mpl.colormaps.get_cmap("viridis")(np.linspace(1, 0, 3))[::-1]
        np.testing.assert_allclose(_facecolors(item), expected, rtol=0, atol=1e-12)
    finally:
        plt.close(figure)


def test_legacy_replace_keyword_is_rejected_as_an_unknown_property() -> None:
    """The old function has unconditional replacement, not a replace option."""

    figure, axis = plt.subplots()
    try:
        with pytest.warns(DeprecationWarning):
            with pytest.raises(OptionError, match="replace"):
                gs.legend_colormap(axis, label="range", replace=True)
        assert axis.get_legend() is None
    finally:
        plt.close(figure)


def test_cmap_legend_rejects_invalid_target_as_layout_error() -> None:
    """Target errors remain distinct from colormap input errors."""

    with pytest.raises(LayoutError, match="ax"):
        cmap_legend(object(), label="range")  # type: ignore[arg-type]


def test_cmap_legend_attachment_failure_preserves_existing_legend(monkeypatch) -> None:
    """Failed canonical replacement restores the old Legend and Axes state."""

    figure, axis = plt.subplots()
    try:
        current = cmap_legend(axis, label="old", stripes=3)
        before_children = tuple(axis.get_children())
        before_patches = tuple(axis.patches)

        def fail_attach(axis, item):
            raise RuntimeError("injected cmap attachment failure")

        monkeypatch.setattr(legends_module, "_attach_legend", fail_attach)
        with pytest.raises(RuntimeError, match="injected cmap"):
            cmap_legend(axis, label="new", replace=True)

        assert axis.get_legend() is current
        assert tuple(axis.get_children()) == before_children
        assert tuple(axis.patches) == before_patches
    finally:
        plt.close(figure)
