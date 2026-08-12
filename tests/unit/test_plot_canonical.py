"""Unit and adapter tests for the canonical explicit-Axes plot API."""

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.collections import LineCollection, PathCollection
from matplotlib.colors import ListedColormap, Normalize

from gsplot._config import Config
from gsplot._core import DataError, PlotError
from gsplot._plot.basic import line, scatter
from gsplot._plot.colored import cmap_dash, cmap_line, cmap_scatter
from gsplot._plot.colormap import colors, sample_cmap


def test_colors_uses_inclusive_positions_and_one_color_midpoint() -> None:
    """The concise sampler returns independent deterministic RGBA rows."""

    colormap = ListedColormap(["black", "red", "white"])
    palette = colors(3, colormap)
    assert palette.shape == (3, 4)
    assert palette.dtype == np.float64
    assert np.all(np.isfinite(palette))
    assert np.allclose(palette[0], colormap(0.0))
    assert np.allclose(palette[-1], colormap(1.0))
    assert np.allclose(colors(1, colormap)[0], colormap(0.5))
    assert np.allclose(colors(3, colormap, reverse=True), palette[::-1])

    another = colors(3, colormap)
    palette[0] = np.nan
    assert np.all(np.isfinite(another))


@pytest.mark.parametrize("n", (True, 0, -1, 1.5))
def test_colors_rejects_invalid_counts(n: object) -> None:
    """Counts are exact positive integers rather than integer-like values."""

    with pytest.raises(PlotError, match="colors: n"):
        colors(n)  # type: ignore[arg-type]


def test_colors_rejects_invalid_colormap_and_reverse_controls() -> None:
    """Colormap lookup and reversal use the concise typed error contract."""

    with pytest.raises(PlotError, match="colors: cmap"):
        colors(cmap="")
    with pytest.raises(PlotError, match="unknown"):
        colors(cmap="missing-colormap")
    with pytest.raises(PlotError, match="colors: cmap"):
        colors(cmap=object())  # type: ignore[arg-type]
    with pytest.raises(PlotError, match="colors: reverse"):
        colors(reverse=1)  # type: ignore[arg-type]


def test_sample_cmap_is_bounded_and_deterministic() -> None:
    """Count and value sampling return independent RGBA arrays."""

    samples = sample_cmap("viridis", count=3)
    assert samples.shape == (3, 4)
    assert np.all((samples >= 0) & (samples <= 1))
    assert np.allclose(sample_cmap("viridis", count=3, reverse=True), samples[::-1])

    constant = sample_cmap("viridis", values=[4.0, 4.0])
    assert np.allclose(constant[0], sample_cmap("viridis", values=[0.5])[0])
    assert sample_cmap("viridis").shape == (10, 4)
    with pytest.raises(PlotError, match="cannot"):
        sample_cmap("viridis", count=2, values=[0, 1])


def test_sample_cmap_accepts_native_colormaps_without_mutating_normalizers() -> None:
    """Native colormaps and Normalize inputs retain their caller ownership."""

    normalizer = Normalize()
    colors = sample_cmap(
        ListedColormap(["black", "white"]), values=[2, 3], norm=normalizer
    )
    assert colors.shape == (2, 4)
    assert normalizer.vmin is None
    assert normalizer.vmax is None
    with pytest.raises(TypeError, match="norm requires"):
        sample_cmap("viridis", count=2, norm=(0, 1))
    with pytest.raises(PlotError, match="increasing"):
        sample_cmap("viridis", values=[0, 1], norm=(1, 0))


def test_basic_plotters_own_their_axes_and_validate_before_mutation() -> None:
    """Basic adapters return native artists and reject closed-schema typos."""

    figure, ax = plt.subplots()
    artists = line(ax, [0], [1], props={"label": "one"})
    collection = scatter(
        ax,
        [0, 1],
        [1, 2],
        config=Config.from_mapping(
            {"schema_version": 2, "plotting": {"default_color": "red"}}
        ),
    )
    assert len(artists) == 1
    assert artists[0].axes is ax
    assert isinstance(collection, PathCollection)
    lines_before = len(ax.lines)
    collections_before = len(ax.collections)
    with pytest.raises(PlotError, match="unknown key"):
        line(ax, [0, 1], [1, 2], props={"not_a_line_property": True})
    with pytest.raises(PlotError, match="unknown key"):
        scatter(ax, [0, 1], [1, 2], props={"not_a_scatter_property": True})
    assert len(ax.lines) == lines_before
    assert len(ax.collections) == collections_before
    plt.close(figure)


def test_colored_plotters_skip_repeated_points_and_return_native_collections() -> None:
    """Repeated coordinates are harmless while an all-zero path is rejected."""

    figure, ax = plt.subplots()
    collection = cmap_line(
        ax,
        [0, 0, 1, 1, 2],
        [0, 0, 1, 1, 0],
        [0, 0.25, 0.5, 0.75, 1],
    )
    dashed = cmap_dash(
        ax,
        [0, 1, 2],
        [0, 1, 0],
        [0, 0.5, 1],
        dash=(3, 2),
    )
    colored = cmap_scatter(ax, [0, 1], [1, 2], [0, 1])
    assert isinstance(collection, LineCollection)
    assert len(collection.get_segments()) == 2
    assert len(dashed) == 1
    assert isinstance(dashed[0], LineCollection)
    assert isinstance(colored, PathCollection)

    collections_before = len(ax.collections)
    with pytest.raises(DataError, match="same"):
        cmap_line(ax, [0, 1], [0, 1], [0])
    assert len(ax.collections) == collections_before
    with pytest.raises(DataError, match="non-zero"):
        cmap_line(ax, [0, 0], [0, 0], [0, 1])
    plt.close(figure)


def test_colored_plotters_have_explicit_compatible_defaults() -> None:
    """Canonical colored helpers do not inherit surprising Matplotlib defaults."""

    figure, ax = plt.subplots()
    try:
        solid = cmap_line(ax, [0, 1], [0, 1], [0, 1])
        dashed = cmap_dash(ax, [0, 1], [1, 0], [0, 1])
        points = cmap_scatter(ax, [0, 1], [1, 2], [0, 1])
        assert solid.get_linewidths().tolist() == [1.0]
        assert dashed[0].get_linewidths().tolist() == [1.0]
        assert np.allclose(dashed[0].get_linestyles()[0][1], (10.0, 10.0))
        assert points.get_sizes().tolist() == [1.0]
        assert points.get_alpha() == 1.0
    finally:
        plt.close(figure)
