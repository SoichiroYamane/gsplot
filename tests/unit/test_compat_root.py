"""Tests for root-level canonical/legacy dispatch boundaries."""

import inspect

import matplotlib.pyplot as plt
import pytest

import gsplot as gs


def test_root_canonical_signature_and_legacy_line_options_are_separate() -> None:
    """Canonical calls stay strict while named legacy styles remain available."""

    figure, ax = gs.subplots()
    assert "props" in str(inspect.signature(gs.line))
    canonical = gs.line(ax, [0, 1], [1, 2], props={"label": "canonical"})
    assert canonical[0].axes is ax
    with pytest.warns(DeprecationWarning, match="legacy"):
        legacy = gs.line(ax, [0, 1], [2, 3], color="red", marker="o")
    assert legacy[0].axes is ax
    plt.close(figure)


def test_root_title_and_show_dispatch_by_explicit_target() -> None:
    """Figure/Axes targets select canonical behavior without current-object lookup."""

    figure, ax = gs.subplots()
    assert gs.title(ax, "canonical").axes is ax
    with pytest.warns(DeprecationWarning, match="legacy"):
        old_title = gs.title("legacy")
    assert old_title.figure is figure
    assert gs.show(figure) is None
    plt.close(figure)
