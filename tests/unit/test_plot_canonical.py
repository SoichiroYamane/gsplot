"""Unit and adapter tests for the canonical explicit-Axes plot API."""

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.collections import LineCollection, PathCollection

from gsplot._config import Config
from gsplot._core import DataError, PlotError
from gsplot._plot.basic import line, scatter
from gsplot._plot.colored import cmap_dash, cmap_line, cmap_scatter
from gsplot._plot.colormap import sample_cmap


def test_sample_cmap_is_bounded_and_deterministic() -> None:
    """Count and value sampling return independent RGBA arrays."""

    samples = sample_cmap("viridis", count=3)
    assert samples.shape == (3, 4)
    assert np.all((samples >= 0) & (samples <= 1))
    assert np.allclose(sample_cmap("viridis", count=3, reverse=True), samples[::-1])

    constant = sample_cmap("viridis", values=[4.0, 4.0])
    assert np.allclose(constant[0], sample_cmap("viridis", values=[0.5])[0])
    with pytest.raises(PlotError, match="exactly one"):
        sample_cmap("viridis")
    with pytest.raises(PlotError, match="exactly one"):
        sample_cmap("viridis", count=2, values=[0, 1])


def test_basic_plotters_own_their_axes_and_validate_before_mutation() -> None:
    """Basic adapters return native artists and reject closed-schema typos."""

    figure, ax = plt.subplots()
    artists = line(ax, [0], [1], props={"label": "one"})
    collection = scatter(
        ax,
        [0, 1],
        [1, 2],
        config=Config.from_mapping({"plotting": {"default_color": "red"}}),
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
