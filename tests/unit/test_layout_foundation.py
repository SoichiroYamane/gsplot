"""Unit tests for publication-aware Figure and Axes ownership."""

import inspect

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.layout_engine import ConstrainedLayoutEngine, TightLayoutEngine

from gsplot import subplots
from gsplot._config import Config
from gsplot._core import LayoutError


def test_subplots_defaults_are_concise_publication_defaults() -> None:
    """One call creates an 85 mm square paper-styled constrained Figure."""

    figure, axis = subplots()
    assert np.allclose(figure.get_size_inches(), np.array([85, 85]) / 25.4)
    assert isinstance(figure.get_layout_engine(), ConstrainedLayoutEngine)
    assert figure.get_facecolor() == (1.0, 1.0, 1.0, 1.0)
    assert axis.get_facecolor() == (1.0, 1.0, 1.0, 1.0)
    assert axis.margins() == (0.0, 0.0)
    assert axis.xaxis.label.get_fontsize() == 10
    plt.close(figure)


def test_subplots_accepts_each_unambiguous_shape_form() -> None:
    """Grid and mosaic forms retain ordinary Matplotlib return containers."""

    row_figure, row_axes = subplots(2)
    assert row_axes.shape == (2,)
    assert np.allclose(row_figure.get_size_inches(), np.array([85, 170]) / 25.4)

    grid_figure, grid_axes = subplots(2, 2, squeeze=False)
    assert grid_axes.shape == (2, 2)
    assert np.allclose(grid_figure.get_size_inches(), np.array([170, 170]) / 25.4)

    mosaic_figure, mosaic_axes = subplots("AB;CC")
    assert tuple(mosaic_axes) == ("A", "B", "C")
    assert all(axis.figure is mosaic_figure for axis in mosaic_axes.values())

    blank_figure, blank_axes = subplots(mosaic=(("A", None),))
    assert tuple(blank_axes) == ("A",)
    plt.close("all")


def test_subplots_applies_config_and_distinguishes_omitted_defaults() -> None:
    """Direct values override Config even when equal to documented defaults."""

    config = Config.from_mapping(
        {
            "schema_version": 2,
            "figure": {
                "size": [2.54, 5.08],
                "unit": "cm",
                "squeeze": False,
                "layout": "tight",
            },
        }
    )
    configured, axes = subplots(config=config, style=None)
    assert np.allclose(configured.get_size_inches(), [1.0, 2.0])
    assert axes.shape == (1, 1)
    assert isinstance(configured.get_layout_engine(), TightLayoutEngine)

    explicit, axis = subplots(
        config=config,
        size="auto",
        unit="in",
        squeeze=True,
        layout="auto",
        style=None,
    )
    assert np.allclose(explicit.get_size_inches(), np.array([85, 85]) / 25.4)
    assert axis.figure is explicit
    assert isinstance(explicit.get_layout_engine(), ConstrainedLayoutEngine)
    plt.close("all")


@pytest.mark.parametrize(
    "call",
    [
        lambda: subplots(1, 2, ncols=2),
        lambda: subplots(1, 2, 3),
        lambda: subplots(mosaic="AB", nrows=1),
        lambda: subplots(mosaic="AA;A."),
        lambda: subplots(mosaic=(("A",), ("A", "B"))),
        lambda: subplots(mosaic=((1,),)),
        lambda: subplots(nrows=True),
    ],
)
def test_subplots_rejects_ambiguous_or_invalid_shape_before_creation(call) -> None:
    """Every shape conflict fails without registering a new pyplot Figure."""

    plt.close("all")
    before = tuple(plt.get_fignums())
    with pytest.raises(LayoutError):
        call()
    assert tuple(plt.get_fignums()) == before


def test_named_size_guardrails_and_unit_conversion() -> None:
    """Named presets stay readable while tuples retain exact physical units."""

    triple, axes = subplots(1, 3, style=None)
    assert axes.shape == (3,)
    assert np.allclose(triple.get_size_inches(), np.array([170, 170 / 3]) / 25.4)
    plt.close(triple)

    for kwargs in (
        {"ncols": 4},
        {"nrows": 3},
        {"ncols": 2, "size": "single"},
        {"ncols": 2, "width_ratios": (1, 10)},
    ):
        with pytest.raises(LayoutError, match="explicit size"):
            subplots(**kwargs)

    exact, _ = subplots(size=(25.4, 50.8), unit="mm", style=None)
    assert np.allclose(exact.get_size_inches(), (1, 2))
    with pytest.raises(LayoutError, match="unit must be 'in'"):
        subplots(size="single", unit="cm")
    plt.close("all")


def test_subplots_validates_before_clearing_or_mutating_existing_figure() -> None:
    """Invalid shape and layout combinations leave a reused Figure untouched."""

    figure, _ = subplots(style=None)
    original_axes = tuple(figure.axes)
    with pytest.raises(LayoutError, match="mosaic"):
        subplots(fig=figure, mosaic="AB", nrows=2, clear=True)
    assert tuple(figure.axes) == original_axes

    with pytest.raises(LayoutError, match="cannot both"):
        subplots(fig=figure, tight_layout=True, constrained_layout=True, clear=True)
    assert tuple(figure.axes) == original_axes
    plt.close(figure)


def test_subplots_reuse_preserves_size_layout_and_existing_style() -> None:
    """Ambient reuse is non-destructive; explicit compatible values are local."""

    figure, first = subplots(size=(2, 3), layout="none", style=None)
    first.set_facecolor("red")
    original_size = figure.get_size_inches().copy()

    reused, second = subplots(fig=figure)
    assert reused is figure
    assert np.allclose(figure.get_size_inches(), original_size)
    assert figure.get_layout_engine() is None
    assert first.get_facecolor() == (1.0, 0.0, 0.0, 1.0)
    assert second.xaxis.labelpad != 6

    _, styled = subplots(fig=figure, style="paper")
    assert styled.get_facecolor() == (1.0, 1.0, 1.0, 1.0)
    assert first.get_facecolor() == (1.0, 0.0, 0.0, 1.0)

    subplots(fig=figure, size=(2, 3), layout="constrained", style=None)
    assert isinstance(figure.get_layout_engine(), ConstrainedLayoutEngine)
    with pytest.raises(LayoutError, match="requested size"):
        subplots(fig=figure, size=(10, 10), clear=True)
    with pytest.raises(LayoutError, match="conflicts"):
        subplots(fig=figure, layout="tight", clear=True)
    plt.close(figure)


def test_subplots_clear_ratios_sharing_and_subplot_options() -> None:
    """Finite Matplotlib layout options are validated and forwarded coherently."""

    figure, axes = subplots(
        1,
        2,
        size=(4, 2),
        layout="none",
        style=None,
        sharey="all",
        width_ratios=np.array([1, 2]),
        subplot_kw={"facecolor": "ivory"},
    )
    assert axes[0].get_shared_y_axes().joined(axes[0], axes[1])
    assert axes[0].get_position().width < axes[1].get_position().width
    assert axes[0].get_facecolor() == (1.0, 1.0, 0.9411764705882353, 1.0)

    with pytest.raises(LayoutError, match="exactly 2"):
        subplots(fig=figure, ncols=2, width_ratios=(1,), clear=True)
    assert len(figure.axes) == 2
    subplots(fig=figure, clear=True)
    assert len(figure.axes) == 1
    plt.close(figure)


def test_deprecated_layout_spellings_remain_finite_and_introspectable() -> None:
    """The 1.x aliases warn while public introspection shows resolved defaults."""

    signature = inspect.signature(subplots)
    assert signature.parameters["size"].default == "auto"
    assert signature.parameters["unit"].default == "in"
    assert signature.parameters["squeeze"].default is True
    assert signature.parameters["layout"].default == "auto"
    assert signature.parameters["style"].default == "auto"
    assert signature.parameters["figsize"].default is None

    with pytest.warns(DeprecationWarning, match="deprecated") as caught:
        figure, _ = subplots(figsize=(2, 3), tight_layout=True, style=None)
    assert len(caught) == 1
    assert np.allclose(figure.get_size_inches(), (2, 3))
    assert isinstance(figure.get_layout_engine(), TightLayoutEngine)
    with pytest.raises(LayoutError, match="cannot be combined"):
        subplots(layout="auto", constrained_layout=True)
    plt.close(figure)


def test_subplots_live_mode_reuses_and_clears_active_figure() -> None:
    """live=True automatically reuses the active figure and clears axes."""

    plt.close("all")
    plt.ioff()
    fig1, ax1 = subplots(live=True)
    assert plt.isinteractive()
    assert len(fig1.axes) == 1
    assert all(t._tickdir == "in" for t in ax1.xaxis.majorTicks)
    original_fignum = fig1.number

    # Second call reuses the active figure and clears it for the new mosaic layout
    fig2, axes2 = subplots("AB", live=True)
    assert fig2 is fig1
    assert fig2.number == original_fignum
    assert len(fig2.axes) == 2
    assert tuple(axes2) == ("A", "B")
    # Verified that paper styling (tick direction 'in') is reapplied on cleared reuse
    assert all(t._tickdir == "in" for t in axes2["A"].xaxis.majorTicks)
    assert all(t._tickdir == "in" for t in axes2["B"].xaxis.majorTicks)

    # Explicit fig combined with live=True reuses that explicit figure
    custom_fig = plt.figure()
    fig3, axes3 = subplots("A", fig=custom_fig, live=True)
    assert fig3 is custom_fig
    assert len(fig3.axes) == 1
    assert all(t._tickdir == "in" for t in axes3["A"].xaxis.majorTicks)

    plt.close("all")


def test_subplots_live_rejects_non_boolean() -> None:
    """live argument must be a strict boolean."""

    with pytest.raises(LayoutError, match="live"):
        subplots(live="yes")  # type: ignore[arg-type]


def test_axes_dict_indexing_supports_labels_integers_and_slices() -> None:
    """AxesDict allows accessing subplots by label name, integer index, and slice."""

    figure, axes = subplots("AB;CD")
    assert isinstance(axes, dict)
    assert len(axes) == 4
    assert tuple(axes.keys()) == ("A", "B", "C", "D")

    # Access by label name
    assert axes["A"] is axes[0]
    assert axes["B"] is axes[1]
    assert axes["C"] is axes[2]
    assert axes["D"] is axes[3]

    # Access by negative integer index
    assert axes[-1] is axes["D"]
    assert axes[-2] is axes["C"]

    # Access by slice
    sliced = axes[0:2]
    assert len(sliced) == 2
    assert sliced[0] is axes["A"]
    assert sliced[1] is axes["B"]

    # Out of range index raises IndexError
    with pytest.raises(IndexError, match="out of range"):
        _ = axes[10]

    # Non-existent string key raises KeyError
    with pytest.raises(KeyError):
        _ = axes["UNKNOWN"]

    plt.close(figure)


def test_subplots_padding_and_spacing_options() -> None:
    """subplots configures padding and spacing on constrained and tight layout engines."""

    from matplotlib.layout_engine import ConstrainedLayoutEngine, TightLayoutEngine

    # 1. Constrained layout with xpad, ypad, xspace, yspace
    fig1, _ = subplots("AB", xpad=0.1, ypad=0.2, xspace=0.3, yspace=0.4)
    engine1 = fig1.get_layout_engine()
    assert isinstance(engine1, ConstrainedLayoutEngine)
    params1 = getattr(engine1, "_params", {})
    assert params1["w_pad"] == 0.1
    assert params1["h_pad"] == 0.2
    assert params1["wspace"] == 0.3
    assert params1["hspace"] == 0.4
    plt.close(fig1)

    # 2. General pad falls back to w_pad and h_pad in constrained layout
    fig2, _ = subplots("AB", pad=0.05)
    engine2 = fig2.get_layout_engine()
    assert isinstance(engine2, ConstrainedLayoutEngine)
    params2 = getattr(engine2, "_params", {})
    assert params2["w_pad"] == 0.05
    assert params2["h_pad"] == 0.05
    plt.close(fig2)

    # 3. Aliases w_pad, h_pad, wspace, hspace
    fig3, _ = subplots("AB", w_pad=0.15, h_pad=0.25, wspace=0.35, hspace=0.45)
    engine3 = fig3.get_layout_engine()
    assert isinstance(engine3, ConstrainedLayoutEngine)
    params3 = getattr(engine3, "_params", {})
    assert params3["w_pad"] == 0.15
    assert params3["h_pad"] == 0.25
    assert params3["wspace"] == 0.35
    assert params3["hspace"] == 0.45
    plt.close(fig3)

    # 4. Tight layout with pad, xpad, ypad
    fig4, _ = subplots(1, 2, layout="tight", pad=1.5, xpad=1.0, ypad=2.0)
    engine4 = fig4.get_layout_engine()
    assert isinstance(engine4, TightLayoutEngine)
    params4 = getattr(engine4, "_params", {})
    assert params4["pad"] == 1.5
    assert params4["w_pad"] == 1.0
    assert params4["h_pad"] == 2.0
    plt.close(fig4)

    # 5. Negative values raise LayoutError
    with pytest.raises(LayoutError, match="xpad"):
        subplots("AB", xpad=-0.5)

    # 6. Conflicting alias values raise LayoutError
    with pytest.raises(LayoutError, match="cannot both be supplied"):
        subplots("AB", xpad=0.1, w_pad=0.2)
