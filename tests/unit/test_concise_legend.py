"""Tests for concise deterministic legend construction."""

import inspect

import matplotlib.pyplot as plt
import pytest
from matplotlib.legend import Legend
from matplotlib.legend_handler import HandlerLine2D

from gsplot._core import LayoutError, PlotError
from gsplot._style.legends import legend


def test_concise_legend_signature_and_defaults_are_publication_ready() -> None:
    """Runtime defaults are finite, visible, and independent of rcParams."""

    signature = inspect.signature(legend)
    assert signature.parameters["loc"].default == "best"
    assert signature.parameters["frameon"].default is False
    assert signature.parameters["fancybox"].default is False
    assert signature.parameters["labelspacing"].default == 0.3
    assert signature.parameters["handlelength"].default is None

    figure, axis = plt.subplots()
    try:
        axis.plot([0, 1], [0, 1], label="signal")
        created = legend(axis)

        assert isinstance(created, Legend)
        assert created._loc == 0
        assert created.get_frame_on() is False
        assert created.labelspacing == 0.3
        assert created.get_frame().get_boxstyle().__class__.__name__ == "Square"
    finally:
        plt.close(figure)


def test_direct_legend_options_and_props_conflicts_are_deterministic() -> None:
    """Direct controls override ambient values and cannot duplicate props."""

    figure, axis = plt.subplots()
    try:
        axis.plot([0, 1], [0, 1], label="signal")
        created = legend(
            axis,
            loc="lower right",
            frameon=True,
            fancybox=True,
            labelspacing=0.5,
            handlelength=3,
        )
        assert created._loc == 4
        assert created.get_frame_on() is True
        assert created.labelspacing == 0.5
        assert created.handlelength == 3
        assert created.get_frame().get_boxstyle().__class__.__name__ == "Round"

        with pytest.raises(LayoutError, match="replace"):
            legend(axis, props={"loc": "upper left"})
        with pytest.raises(LayoutError, match="replace"):
            legend(axis, replace=False)
        with pytest.raises(PlotError, match="conflicts"):
            legend(axis, replace=True, loc="best", props={"loc": "upper left"})
    finally:
        plt.close(figure)


def test_collection_legends_skip_empty_axes_and_preserve_target_order() -> None:
    """Discovery returns only created legends in normalized target order."""

    figure, axes = plt.subplots(1, 3)
    try:
        axes[0].plot([0, 1], [0, 1], label="first")
        axes[2].plot([0, 1], [1, 0], label="third")
        created = legend({"C": axes[2], "B": axes[1], "A": axes[0]})

        assert isinstance(created, tuple)
        assert tuple(item.axes for item in created) == (axes[2], axes[0])
        assert axes[1].get_legend() is None

        empty_figure, empty_axis = plt.subplots()
        try:
            assert legend((empty_axis,)) == ()
            with pytest.raises(LayoutError, match="no legend entries"):
                legend(empty_axis)
        finally:
            plt.close(empty_figure)
    finally:
        plt.close(figure)


def test_explicit_multi_target_entries_require_exact_mappings() -> None:
    """Shared entry sequences are never guessed to be per-target values."""

    figure, axes = plt.subplots(1, 2)
    try:
        first = axes[0].plot([0, 1], [0, 1])[0]
        second = axes[1].plot([0, 1], [1, 0])[0]
        target = {"left": axes[0], "right": axes[1]}

        with pytest.raises(LayoutError, match="exact-key mappings"):
            legend(target, handles=(first, second), labels=("one", "two"))
        assert all(axis.get_legend() is None for axis in axes)

        created = legend(
            target,
            handles={"left": (first,), "right": (second,)},
            labels={"left": ("one",), "right": ("two",)},
        )
        assert tuple(item.axes for item in created) == tuple(axes)
        assert tuple(item.get_texts()[0].get_text() for item in created) == (
            "one",
            "two",
        )
    finally:
        plt.close(figure)


def test_legend_preflight_checks_every_target_before_attachment() -> None:
    """A later replacement conflict cannot attach an earlier planned legend."""

    figure, axes = plt.subplots(1, 2)
    try:
        for position, axis in enumerate(axes):
            axis.plot([0, 1], [position, position + 1], label=str(position))
        axes[1].legend()

        with pytest.raises(LayoutError, match="replace"):
            legend(axes)
        assert axes[0].get_legend() is None
        assert axes[1].get_legend() is not None

        with pytest.raises(PlotError, match="HandlerBase"):
            legend(axes, replace=True, handler_map={object: object()})  # type: ignore[dict-item]
        assert axes[0].get_legend() is None

        created = legend(
            axes,
            replace=True,
            reverse=True,
            handler_map={type(axes[0].lines[0]): HandlerLine2D()},
        )
        assert len(created) == 2
    finally:
        plt.close(figure)


def test_legend_attachment_failure_restores_replaced_legends(monkeypatch) -> None:
    """Unexpected attachment errors roll every target back to its old legend."""

    figure, axes = plt.subplots(1, 2)
    try:
        for position, axis in enumerate(axes):
            axis.plot([0, 1], [position, position + 1], label=str(position))
        previous = (axes[0].legend(), axes[1].legend())
        second_add_artist = axes[1].add_artist

        def fail_new_legend(artist):
            if artist is not previous[1]:
                raise RuntimeError("attachment failed")
            return second_add_artist(artist)

        monkeypatch.setattr(axes[1], "add_artist", fail_new_legend)
        with pytest.raises(RuntimeError, match="attachment failed"):
            legend(axes, replace=True)

        assert axes[0].get_legend() is previous[0]
        assert axes[1].get_legend() is previous[1]
        assert all(item in axis.get_children() for item, axis in zip(previous, axes))
    finally:
        plt.close(figure)


def test_legend_direct_kwargs() -> None:
    """legend accepts direct kwargs merged into props, with kwargs taking precedence."""

    figure, axis = plt.subplots()
    try:
        axis.plot([0, 1], [0, 1], label="signal 1")
        axis.plot([0, 1], [0, 2], label="signal 2")
        created = legend(
            axis,
            title="MyLegend",
            fontsize=8,
            ncols=2,
            framealpha=0.6,
            props={"fontsize": 10},
        )
        assert created.get_title().get_text() == "MyLegend"
        assert created._ncols == 2
        # kwargs (fontsize=8) overrides props (fontsize=10)
        assert any(text.get_fontsize() == 8.0 for text in created.get_texts())
    finally:
        plt.close(figure)
