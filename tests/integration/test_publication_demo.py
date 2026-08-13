"""Integration tests for the concise publication-style documentation."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import pytest
from matplotlib.figure import Figure
from mpl_toolkits.axes_grid1.inset_locator import BboxConnector, BboxPatch

DEMO_PATH = (
    Path(__file__).resolve().parents[2] / "demo" / "4_paper_plot" / "paper_plot.py"
)


def _load_demo() -> ModuleType:
    """Load the demo without executing its guarded entry point."""

    spec = spec_from_file_location("gsplot_publication_demo", DEMO_PATH)
    if spec is None or spec.loader is None:  # pragma: no cover - importlib guard
        raise RuntimeError("could not load the publication demo")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_publication_demo_uses_concise_defaults_and_closes_figure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The executable recipe preserves its science and explicit lifecycle."""

    demo = _load_demo()
    before = mpl.rcParams.copy()
    observed: dict[str, Any] = {}

    def fake_save(target: Figure, output: Path) -> tuple[Path, ...]:
        axes = {axis.get_label(): axis for axis in target.axes if axis.get_label()}
        observed.update(target=target, output=output, axes=axes)
        target.canvas.draw()
        return (output.with_suffix(".png"), output.with_suffix(".pdf"))

    monkeypatch.setattr(demo, "ROOT", tmp_path)
    monkeypatch.setattr(demo.gs, "save", fake_save)
    demo.main()

    figure = observed["target"]
    axes = observed["axes"]
    assert observed["output"] == tmp_path / "SC_cal"
    assert tuple(figure.get_size_inches()) == pytest.approx(
        (170 / 25.4, (170 / 3) / 25.4)
    )
    assert type(figure.get_layout_engine()).__name__ == "ConstrainedLayoutEngine"
    assert {name: len(axes[name].lines) for name in "ABC"} == {
        "A": 9,
        "B": 9,
        "C": 5,
    }
    assert len(axes["B"].child_axes) == 2
    assert sorted(len(axis.lines) for axis in axes["B"].child_axes) == [9, 9]
    assert all(
        line.get_markersize() == 0 for name in "ABC" for line in axes[name].lines
    )
    assert axes["A"].get_legend()._loc == 3
    assert axes["B"].get_legend() is None
    assert axes["C"].get_legend()._loc == 4
    assert tuple(axes[name].get_xlabel() for name in "ABC") == (
        "$T/T_c$",
        "$T/T_c$",
        "$T/T_c$",
    )
    assert tuple(axes[name].get_box_aspect() for name in "ABC") == (1.0, 1.0, 1.0)
    indicator = axes["B"].patches[-3:]
    assert isinstance(indicator[0], BboxPatch)
    assert all(isinstance(artist, BboxConnector) for artist in indicator[1:])
    assert tuple((artist.loc2, artist.loc1) for artist in indicator[1:]) == (
        (3, 2),
        (4, 1),
    )
    assert all(artist.get_zorder() == pytest.approx(4.99) for artist in indicator)
    assert not plt.fignum_exists(figure.number)
    assert mpl.rcParams == before


def test_publication_demo_closes_figure_when_output_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A failed export does not leak the Figure owned by the demo."""

    demo = _load_demo()
    observed: dict[str, Figure] = {}

    def fail_save(target: Figure, output: Path) -> tuple[Path, ...]:
        observed["target"] = target
        raise OSError("simulated output failure")

    monkeypatch.setattr(demo, "ROOT", tmp_path)
    monkeypatch.setattr(demo.gs, "save", fail_save)

    with pytest.raises(OSError, match="simulated output failure"):
        demo.main()

    assert not plt.fignum_exists(observed["target"].number)
