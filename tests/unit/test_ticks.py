"""Tests for canonical ticks API and tick edge controls across minor_ticks and label."""

import inspect

import matplotlib.pyplot as plt
import pytest

from gsplot._core import LayoutError
from gsplot._style.axes import label, minor_ticks, ticks


def test_ticks_signature_defaults() -> None:
    """Introspection publishes canonical parameter defaults."""

    sig = inspect.signature(ticks)
    assert sig.parameters["minor"].default is None
    assert sig.parameters["axis"].default == "both"
    assert sig.parameters["top"].default is None
    assert sig.parameters["bottom"].default is None
    assert sig.parameters["left"].default is None
    assert sig.parameters["right"].default is None
    assert sig.parameters["direction"].default is None
    assert sig.parameters["which"].default == "both"

    minor_sig = inspect.signature(minor_ticks)
    assert minor_sig.parameters["top"].default is None
    assert minor_sig.parameters["bottom"].default is None
    assert minor_sig.parameters["left"].default is None
    assert minor_sig.parameters["right"].default is None

    label_sig = inspect.signature(label)
    assert label_sig.parameters["top"].default is None
    assert label_sig.parameters["bottom"].default is None
    assert label_sig.parameters["left"].default is None
    assert label_sig.parameters["right"].default is None
    assert label_sig.parameters["direction"].default is None


def test_ticks_basic_and_direction() -> None:
    """ticks enables minor ticks, applies direction, and configures edge visibility."""

    figure, ax = plt.subplots()
    try:
        ticks(ax, minor=True, right=False, direction="in")

        # Minor ticks locator is active
        assert ax.xaxis.get_minor_locator().__class__.__name__ == "AutoMinorLocator"
        assert ax.yaxis.get_minor_locator().__class__.__name__ == "AutoMinorLocator"

        # Check tick lines
        ytick_lines = ax.yaxis.get_ticklines()
        assert len(ytick_lines) > 0
    finally:
        plt.close(figure)


def test_minor_ticks_with_edges() -> None:
    """minor_ticks accepts edge visibility flags."""

    figure, ax = plt.subplots()
    try:
        minor_ticks(ax, True, axis="y", right=False)
        assert ax.yaxis.get_minor_locator().__class__.__name__ == "AutoMinorLocator"

        minor_ticks(ax, False, axis="y")
        assert ax.yaxis.get_minor_locator().__class__.__name__ == "NullLocator"
    finally:
        plt.close(figure)


def test_label_with_tick_controls() -> None:
    """label forwards tick edge and direction options to AxisSpec."""

    figure, ax = plt.subplots()
    try:
        label(ax, "Time (s)", "Signal (V)", right=False, top=False, direction="in")
        assert ax.get_xlabel() == "Time (s)"
        assert ax.get_ylabel() == "Signal (V)"
    finally:
        plt.close(figure)


def test_twinx_pattern() -> None:
    """ticks seamlessly styles two y-axes (twinx) without tick collisions."""

    figure, ax_left = plt.subplots()
    try:
        ax_right = ax_left.twinx()

        ticks(ax_left, minor=True, right=False, direction="in")
        ticks(ax_right, minor=True, left=False, right=True, direction="in")

        assert (
            ax_left.yaxis.get_minor_locator().__class__.__name__ == "AutoMinorLocator"
        )
        assert (
            ax_right.yaxis.get_minor_locator().__class__.__name__ == "AutoMinorLocator"
        )
    finally:
        plt.close(figure)


def test_ticks_multi_axes() -> None:
    """ticks applies options across multiple Axes targets."""

    figure, axes = plt.subplots(1, 3)
    try:
        ticks(axes, minor=True, top=False, right=False)
        for ax in axes:
            assert ax.xaxis.get_minor_locator().__class__.__name__ == "AutoMinorLocator"
            assert ax.yaxis.get_minor_locator().__class__.__name__ == "AutoMinorLocator"
    finally:
        plt.close(figure)


def test_ticks_validation_errors() -> None:
    """ticks and minor_ticks validate input arguments strictly."""

    figure, ax = plt.subplots()
    try:
        with pytest.raises(LayoutError, match="axis"):
            ticks(ax, axis="invalid")  # type: ignore[arg-type]
        with pytest.raises(LayoutError, match="which"):
            ticks(ax, which="invalid")  # type: ignore[arg-type]
        with pytest.raises(LayoutError, match="direction"):
            ticks(ax, direction="invalid")  # type: ignore[arg-type]
        with pytest.raises(LayoutError, match="right"):
            ticks(ax, right="invalid")  # type: ignore[arg-type]
        with pytest.raises(LayoutError, match="minor"):
            ticks(ax, minor="invalid")  # type: ignore[arg-type]

        with pytest.raises(LayoutError, match="right"):
            minor_ticks(ax, True, right="invalid")  # type: ignore[arg-type]

        with pytest.raises(LayoutError, match="label: right"):
            label(ax, right="invalid")  # type: ignore[arg-type]
        with pytest.raises(LayoutError, match="label: direction"):
            label(ax, direction="invalid")  # type: ignore[arg-type]
    finally:
        plt.close(figure)
