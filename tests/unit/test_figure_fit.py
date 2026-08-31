"""Tests for the Figure-local independent-text fitting policy."""

import pickle
from typing import cast

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.axes import Axes
from matplotlib.backends.backend_pdf import FigureCanvasPdf
from matplotlib.backends.backend_svg import FigureCanvasSVG

import gsplot as gs
from gsplot._figure.fit import _figure_fit_state


def _assert_inside_figure(figure, text) -> None:
    """Assert that one visible text bounding box is inside the Figure canvas."""

    renderer = figure._get_renderer()
    box = text.get_window_extent(renderer)
    figure_box = figure.bbox
    assert box.x0 >= figure_box.x0 - 1e-6
    assert box.y0 >= figure_box.y0 - 1e-6
    assert box.x1 <= figure_box.x1 + 1e-6
    assert box.y1 <= figure_box.y1 + 1e-6


def test_figure_fit_preserves_canvas_and_fits_independent_annotations() -> None:
    """Figure fitting moves supported annotations without resizing the canvas."""

    figure, axis = gs.subplots(
        size=(240, 400),
        unit="pt",
        layout="none",
        style=None,
        figure_fit=True,
    )
    axis = cast(Axes, axis)
    try:
        axis.set_position((0, 0, 1, 1))
        index = gs.index(axis, loc="corner", offset=(-100, 100), size=10)
        panel = gs.panel_labels(axis, labels=("Panel",), loc="out", fontsize=10)[0]
        title = gs.title(axis, "Title", y=1.5, fontsize=10)
        suptitle = gs.suptitle(figure, "Suptitle", y=1.5, fontsize=10)

        figure.canvas.draw()

        for text in (index, panel, title, suptitle):
            _assert_inside_figure(figure, text)
        assert np.allclose(figure.get_size_inches(), np.array([240, 400]) / 72)
    finally:
        plt.close(figure)


def test_figure_fit_defaults_to_disabled() -> None:
    """Omitting figure_fit preserves the historical outside placement."""

    figure, axis = gs.subplots(size=(240, 400), unit="pt", layout="none", style=None)
    axis = cast(Axes, axis)
    try:
        axis.set_position((0, 0, 1, 1))
        index = gs.index(axis, loc="corner", offset=(-100, 0), size=10)
        figure.canvas.draw()
        assert index.get_window_extent(figure.canvas.get_renderer()).x0 < figure.bbox.x0
    finally:
        plt.close(figure)


def test_figure_fit_leaves_axes_managed_labels_unchanged() -> None:
    """Figure fitting does not move labels owned by an Axes."""

    figure, axis = gs.subplots(
        size=(240, 400),
        unit="pt",
        layout="none",
        style=None,
        figure_fit=True,
    )
    axis = cast(Axes, axis)
    try:
        axis.set_position((0, 0, 1, 1))
        axis.set_xlabel("x", labelpad=40)
        figure.canvas.draw()
        before = axis.xaxis.label.get_window_extent(figure.canvas.get_renderer())

        gs.index(axis, loc="corner", offset=(-100, 0), size=10)
        figure.canvas.draw()
        after = axis.xaxis.label.get_window_extent(figure.canvas.get_renderer())

        assert before.bounds == pytest.approx(after.bounds)
    finally:
        plt.close(figure)


def test_figure_fit_refits_registered_annotations_before_save(tmp_path) -> None:
    """Saving re-fits annotations after a caller changes Axes geometry."""

    figure, axis = gs.subplots(
        size=(240, 400),
        unit="pt",
        layout="none",
        style=None,
        figure_fit=True,
    )
    axis = cast(Axes, axis)
    try:
        index = gs.index(axis, loc="corner", offset=(0, 0), size=10)
        axis.set_position((-0.25, 0, 1, 1))
        paths = gs.save(
            figure,
            tmp_path / "figure.pdf",
            crop=False,
            show=False,
        )

        assert paths == ((tmp_path / "figure.pdf").resolve(),)
        figure.canvas.draw()
        _assert_inside_figure(figure, index)
        assert np.allclose(figure.get_size_inches(), np.array([240, 400]) / 72)
    finally:
        plt.close(figure)


def test_figure_fit_refits_registered_annotations_before_savefig(tmp_path) -> None:
    """The conservative savefig path also honors the Figure-fit policy."""

    figure, axis = gs.subplots(
        size=(240, 400),
        unit="pt",
        layout="none",
        style=None,
        figure_fit=True,
    )
    axis = cast(Axes, axis)
    try:
        index = gs.index(axis, loc="corner", offset=(0, 0), size=10)
        axis.set_position((-0.25, 0, 1, 1))
        paths = gs.savefig(
            figure,
            tmp_path / "figure.pdf",
            show=False,
        )

        assert paths == ((tmp_path / "figure.pdf").resolve(),)
        figure.canvas.draw()
        _assert_inside_figure(figure, index)
        assert np.allclose(figure.get_size_inches(), np.array([240, 400]) / 72)
    finally:
        plt.close(figure)


def test_figure_fit_rejects_an_annotation_larger_than_the_canvas() -> None:
    """Fitting fails explicitly rather than silently shrinking an annotation."""

    figure, _ = gs.subplots(
        size=(1, 1), unit="pt", layout="none", style=None, figure_fit=True
    )
    try:
        with pytest.raises(gs.LayoutError, match="does not fit"):
            gs.suptitle(figure, "This annotation is too wide", fontsize=10)
    finally:
        plt.close(figure)


def test_figure_fit_requires_a_boolean() -> None:
    """The new Figure policy uses strict boolean validation."""

    with pytest.raises(gs.LayoutError, match="figure_fit"):
        gs.subplots(figure_fit="yes")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("canvas_class", "extension"),
    ((FigureCanvasPdf, "pdf"), (FigureCanvasSVG, "svg")),
)
def test_figure_fit_supports_vector_renderers(
    canvas_class, extension, tmp_path
) -> None:
    """Fitting uses Matplotlib's backend-neutral Figure renderer."""

    figure, _ = gs.subplots(
        size=(240, 240),
        unit="pt",
        layout="none",
        style=None,
        figure_fit=True,
    )
    canvas_class(figure)
    try:
        text = gs.suptitle(figure, "Suptitle", y=1.5, fontsize=10)
        figure.canvas.draw()
        _assert_inside_figure(figure, text)
        output = tmp_path / f"figure.{extension}"
        figure.savefig(output, format=extension)
        assert output.is_file()
    finally:
        plt.close(figure)


def test_figure_fit_includes_visible_text_bbox_patch() -> None:
    """A visible Text bbox decoration is kept inside the Figure too."""

    figure, _ = gs.subplots(
        size=(240, 240),
        unit="pt",
        layout="none",
        style=None,
        figure_fit=True,
    )
    try:
        text = gs.suptitle(
            figure,
            "Suptitle",
            y=0,
            fontsize=10,
            bbox={"facecolor": "red", "pad": 10},
        )
        figure.canvas.draw()
        renderer = figure._get_renderer()
        patch = text.get_bbox_patch()
        assert patch is not None
        patch_box = patch.get_window_extent(renderer)
        figure_box = figure.bbox
        assert patch_box.x0 >= figure_box.x0 - 1e-6
        assert patch_box.y0 >= figure_box.y0 - 1e-6
        assert patch_box.x1 <= figure_box.x1 + 1e-6
        assert patch_box.y1 <= figure_box.y1 + 1e-6
    finally:
        plt.close(figure)


def test_figure_fit_refreshes_an_existing_title() -> None:
    """Updating an Axes title preserves the caller's new padding."""

    figure, axis = gs.subplots(
        size=(240, 240),
        unit="pt",
        layout="none",
        style=None,
        figure_fit=True,
    )
    axis = cast(Axes, axis)
    try:
        title = gs.title(axis, "Title", pad=0, fontsize=10)
        figure.canvas.draw()
        before = title.get_window_extent(figure._get_renderer()).bounds
        gs.title(axis, "Title", pad=40, fontsize=10)
        figure.canvas.draw()
        after = title.get_window_extent(figure._get_renderer()).bounds
        assert after[1] > before[1]
    finally:
        plt.close(figure)


def test_figure_fit_state_is_pickleable() -> None:
    """A Figure with fitting state can be serialized by Matplotlib."""

    figure, axis = gs.subplots(
        size=(240, 240),
        unit="pt",
        layout="none",
        style=None,
        figure_fit=True,
    )
    try:
        gs.index(cast(Axes, axis), loc="corner", offset=(-100, 0), size=10)
        # Round-trip only bytes produced from this in-memory Figure above.
        restored = pickle.loads(pickle.dumps(figure))
        try:
            restored.canvas.draw()
            restored_index = restored.axes[0].texts[0]
            _assert_inside_figure(restored, restored_index)
        finally:
            plt.close(restored)
    finally:
        plt.close(figure)


def test_figure_fit_reuse_preserves_policy_until_explicitly_disabled() -> None:
    """Reusing a Figure preserves an omitted policy and honors explicit False."""

    figure, _ = gs.subplots(
        size=(240, 240),
        unit="pt",
        layout="none",
        style=None,
        figure_fit=True,
    )
    try:
        _, reused_axis = gs.subplots(
            fig=figure,
            size=None,
            layout="none",
            style=None,
        )
        reused_axis = cast(Axes, reused_axis)
        preserved = gs.index(reused_axis, loc="corner", offset=(-100, 0), size=10)
        figure.canvas.draw()
        _assert_inside_figure(figure, preserved)

        _, disabled_axis = gs.subplots(
            fig=figure,
            size=None,
            layout="none",
            style=None,
            figure_fit=False,
        )
        disabled_axis = cast(Axes, disabled_axis)
        disabled = gs.index(disabled_axis, loc="corner", offset=(-100, 0), size=10)
        figure.canvas.draw()
        assert disabled.get_window_extent(figure._get_renderer()).x0 < figure.bbox.x0
    finally:
        plt.close(figure)


def test_figure_fit_discards_annotations_removed_by_figure_clear() -> None:
    """Clearing a Figure does not retain detached annotations in its registry."""

    figure, axis = gs.subplots(
        size=(240, 240),
        unit="pt",
        layout="none",
        style=None,
        figure_fit=True,
    )
    try:
        gs.index(cast(Axes, axis), loc="corner", offset=(-100, 0), size=10)
        figure.clear()
        _, new_axis = gs.subplots(
            fig=figure,
            size=None,
            layout="none",
            style=None,
        )
        gs.index(cast(Axes, new_axis), loc="corner", offset=(-100, 0), size=10)
        state = _figure_fit_state(figure)
        assert state is not None
        assert len(state.annotations) == 1
    finally:
        plt.close(figure)


def test_figure_fit_rolls_back_existing_annotation_metadata_on_failure() -> None:
    """A failed registration restores prior artist and controller state."""

    figure, axis = gs.subplots(
        size=(240, 240),
        unit="pt",
        layout="none",
        style=None,
        figure_fit=True,
    )
    axis = cast(Axes, axis)
    try:
        title = gs.title(axis, "Title", y=1.5, fontsize=10)
        state = _figure_fit_state(figure)
        assert state is not None
        before_transform = title.get_transform()
        assert state.annotations[title].applied_transform is before_transform

        with pytest.raises(gs.LayoutError, match="does not fit"):
            gs.suptitle(figure, "X" * 200, fontsize=10)

        restored_state = _figure_fit_state(figure)
        assert restored_state is not None
        assert (
            restored_state.annotations[title].applied_transform is title.get_transform()
        )
        assert title.get_transform() is before_transform
    finally:
        plt.close(figure)
