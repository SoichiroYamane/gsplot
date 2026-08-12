"""Unit tests for explicit figure and axes ownership."""

import matplotlib.pyplot as plt
import numpy as np
import pytest

from gsplot import subplots
from gsplot._config import Config
from gsplot._core import LayoutError


def test_subplots_returns_explicit_figure_and_matplotlib_shapes() -> None:
    """Ordinary arrays and mosaics follow Matplotlib return conventions."""

    figure, axes = subplots(nrows=2, ncols=1, squeeze=False)
    assert axes.shape == (2, 1)
    assert all(axis.figure is figure for axis in axes.flat)

    mosaic_figure, mosaic_axes = subplots(mosaic="AB")
    assert set(mosaic_axes) == {"A", "B"}
    assert all(axis.figure is mosaic_figure for axis in mosaic_axes.values())
    plt.close("all")


def test_subplots_applies_config_and_converts_units() -> None:
    """Config values are used only when explicit arguments are omitted."""

    config = Config.from_mapping(
        {
            "schema_version": 2,
            "figure": {"size": [2.54, 5.08], "unit": "cm", "squeeze": False},
        }
    )
    figure, axes = subplots(config=config)
    assert np.allclose(figure.get_size_inches(), [1.0, 2.0])
    assert axes.shape == (1, 1)
    plt.close(figure)

    explicit_figure, explicit_axes = subplots(
        config=config, figsize=(1, 1), unit="in", squeeze=True
    )
    assert np.allclose(explicit_figure.get_size_inches(), [1.0, 1.0])
    assert explicit_axes.figure is explicit_figure
    plt.close(explicit_figure)


def test_subplots_validates_before_clearing_or_mutating_existing_figure() -> None:
    """Invalid layout combinations leave an existing figure untouched."""

    figure, _ = subplots()
    original_axes = tuple(figure.axes)
    with pytest.raises(LayoutError, match="mosaic"):
        subplots(fig=figure, mosaic="AB", nrows=2, clear=True)
    assert tuple(figure.axes) == original_axes

    with pytest.raises(LayoutError, match="cannot both"):
        subplots(fig=figure, tight_layout=True, constrained_layout=True, clear=True)
    assert tuple(figure.axes) == original_axes
    plt.close(figure)


def test_subplots_reuses_without_resizing_and_clears_only_when_requested() -> None:
    """Existing figures remain owned by the caller and are never resized."""

    figure, _ = subplots(figsize=(2, 3))
    original_size = figure.get_size_inches().copy()
    reused, axes = subplots(fig=figure, clear=False)
    assert reused is figure
    assert np.allclose(figure.get_size_inches(), original_size)
    assert axes.figure is figure
    assert len(figure.axes) == 2

    with pytest.raises(LayoutError, match="figsize"):
        subplots(fig=figure, figsize=(10, 10), clear=False)

    subplots(fig=figure, clear=True)
    assert len(figure.axes) == 1
    plt.close(figure)


def test_subplots_rejects_layout_engine_conflicts_before_clearing() -> None:
    """A requested engine never replaces a conflicting caller-owned engine."""

    figure, _ = subplots()
    figure.set_layout_engine("constrained")
    original_axes = tuple(figure.axes)
    with pytest.raises(LayoutError, match="tight_layout"):
        subplots(fig=figure, tight_layout=True, clear=True)
    assert tuple(figure.axes) == original_axes

    figure.set_layout_engine("tight")
    with pytest.raises(LayoutError, match="constrained_layout"):
        subplots(fig=figure, constrained_layout=True, clear=True)
    assert tuple(figure.axes) == original_axes
    plt.close(figure)
