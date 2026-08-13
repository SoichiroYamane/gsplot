"""Integration tests for the concise publication-style documentation."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.figure import Figure

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


def test_publication_demo_uses_balanced_canvas_and_closes_figure(
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
    assert tuple(figure.get_size_inches()) == pytest.approx((8.3, 2.85))
    assert type(figure.get_layout_engine()).__name__ == "ConstrainedLayoutEngine"
    assert figure.get_layout_engine().get()["wspace"] == pytest.approx(0.08)
    assert {name: len(axes[name].lines) for name in "ABC"} == {
        "A": 9,
        "B": 9,
        "C": 5,
    }
    assert len(axes["B"].child_axes) == 1
    square = axes["B"].child_axes[0]
    assert len(square.lines) == 9
    gap = [
        np.genfromtxt(
            demo.DATA / "gap" / f"Gapeq_{name}.dat",
            delimiter="\t",
            skip_header=1,
            unpack=True,
        )
        for name in demo.NAMES
    ]
    capacity = [
        np.genfromtxt(
            demo.DATA / "c" / f"C_{name}.dat",
            delimiter="\t",
            skip_header=1,
            unpack=True,
        )
        for name in demo.NAMES
    ]
    yosida = [
        np.genfromtxt(
            demo.DATA / "yosida" / f"Y(T)_{name}.dat",
            delimiter="\t",
            skip_header=1,
            unpack=True,
        )
        for name in demo.EVEN
    ]
    for line, expected in zip(axes["A"].lines, gap):
        np.testing.assert_array_equal(line.get_xdata(), expected[0])
        np.testing.assert_array_equal(line.get_ydata(), expected[1])
    for position, expected in enumerate(capacity):
        temperature = np.append(expected[0], [1, 1.5])
        normalized = np.append(expected[1], [1, 1])
        np.testing.assert_array_equal(
            axes["B"].lines[position].get_xdata(), temperature
        )
        np.testing.assert_array_equal(axes["B"].lines[position].get_ydata(), normalized)
        np.testing.assert_array_equal(
            square.lines[position].get_xdata(), temperature**2
        )
        np.testing.assert_array_equal(square.lines[position].get_ydata(), normalized)
    for line, expected in zip(axes["C"].lines, yosida):
        np.testing.assert_array_equal(line.get_xdata(), expected[0])
        np.testing.assert_array_equal(line.get_ydata(), expected[1])
    assert all(
        line.get_markersize() == 0 for name in "ABC" for line in axes[name].lines
    )
    assert axes["A"].get_legend()._loc == 3
    assert axes["A"].get_legend()._ncols == 2
    assert axes["A"].get_legend().columnspacing == pytest.approx(0.4)
    assert axes["A"].get_legend().handlelength == pytest.approx(1.4)
    assert {text.get_fontsize() for text in axes["A"].get_legend().texts} == {7.0}
    assert [text.get_text() for text in axes["A"].get_legend().texts] == list(
        demo.LABELS
    )
    assert axes["B"].get_legend() is None
    assert axes["C"].get_legend()._loc == 2
    assert axes["C"].get_legend().columnspacing == pytest.approx(0.4)
    assert axes["C"].get_legend().handlelength == pytest.approx(1.4)
    assert {text.get_fontsize() for text in axes["C"].get_legend().texts} == {7.0}
    assert [text.get_text() for text in axes["C"].get_legend().texts] == [
        demo.LABELS[demo.NAMES.index(name)] for name in demo.EVEN
    ]
    assert square.xaxis.label.get_fontsize() == 7
    assert square.yaxis.label.get_fontsize() == 7
    renderer = figure.canvas.get_renderer()
    parent_labels = (
        *axes["B"].get_xticklabels(),
        *axes["B"].get_yticklabels(),
        axes["B"].xaxis.label,
        axes["B"].yaxis.label,
    )
    assert all(
        not square.get_tightbbox(renderer).overlaps(label.get_window_extent(renderer))
        for label in parent_labels
        if label.get_visible() and label.get_text()
    )
    parent_ylabels = [
        label for label in axes["B"].get_yticklabels() if label.get_visible()
    ]
    mm_per_pixel = 25.4 / figure.dpi
    assert (
        square.get_tightbbox(renderer).x0
        - max(label.get_window_extent(renderer).x1 for label in parent_ylabels)
    ) * mm_per_pixel >= 4
    xlabels = [label for label in square.get_xticklabels() if label.get_visible()]
    ylabels = [label for label in square.get_yticklabels() if label.get_visible()]
    assert (
        not xlabels[0]
        .get_window_extent(renderer)
        .overlaps(ylabels[0].get_window_extent(renderer))
    )
    assert tuple(axes[name].get_xlabel() for name in "ABC") == (
        "$T/T_c$",
        "$T/T_c$",
        "$T/T_c$",
    )
    assert tuple(axes[name].get_box_aspect() for name in "ABC") == (1.0, 1.0, 1.0)
    assert tuple(axes[name].get_ylabel() for name in "ABC") == (
        "$\\Delta_0(T)/k_BT_c$",
        "$C_s/C_n$",
        "$Y(T)$",
    )
    assert tuple(axes[name].get_xlim() for name in "ABC") == (
        (0.0, 1.2),
        (0.0, 1.2),
        (0.0, 1.0),
    )
    assert tuple(axes[name].get_ylim() for name in "ABC") == (
        (0.0, 3.0),
        (0.0, 3.0),
        (0.0, 1.0),
    )
    assert (
        square.get_xlabel(),
        square.get_ylabel(),
        square.get_xlim(),
        square.get_ylim(),
    ) == ("$(T/T_c)^2$", "$C_s/C_n$", (0.0, 0.25), (0.0, 1.0))
    assert tuple(axes[name].texts[0].get_text() for name in "ABC") == (
        "(a)",
        "(b)",
        "(c)",
    )
    assert len(axes["B"].patches) == 0
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
