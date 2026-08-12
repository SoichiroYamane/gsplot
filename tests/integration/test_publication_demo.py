"""Integration tests for the publication-style executable documentation."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Any

import matplotlib as mpl
import matplotlib.pyplot as plt
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


def test_publication_demo_restores_native_visual_contract() -> None:
    """The builder restores historical artists without leaking rcParams."""

    demo = _load_demo()
    before = {name: mpl.rcParams[name] for name in demo.PUBLICATION_RCPARAMS}
    figure, axes, insets = demo.build_publication_figure()
    try:
        assert tuple(figure.get_size_inches()) == pytest.approx((15.0, 5.0))
        assert type(figure.get_layout_engine()).__name__ == "TightLayoutEngine"
        assert {name: len(axis.lines) for name, axis in axes.items()} == {
            "A": 9,
            "B": 9,
            "C": 5,
        }
        assert {name: len(axis.lines) for name, axis in insets.items()} == {
            "heat": 9,
            "square": 9,
        }
        assert all(
            line.get_markersize() == 0 for axis in axes.values() for line in axis.lines
        )
        assert tuple(line.get_linestyle() for line in axes["A"].lines[:4]) == (
            "-",
            "--",
            "-.",
            ":",
        )
        assert (
            tuple(
                getattr(line, "_unscaled_dash_pattern") for line in axes["A"].lines[4:]
            )
            == demo.LINE_STYLES[4:]
        )
        assert all(axis.get_box_aspect() == 1 for axis in axes.values())
        assert axes["A"].get_legend() is not None
        assert axes["B"].get_legend() is None
        assert axes["C"].get_legend() is not None
        assert tuple(text.get_text() for text in figure.texts) == (
            "($\\,$a$\\,$)",
            "($\\,$b$\\,$)",
            "($\\,$c$\\,$)",
        )
        assert len(axes["B"].child_axes) == 2
        assert any(
            type(artist).__name__ == "InsetIndicator" for artist in axes["B"].artists
        )

        figure.canvas.draw()
        first_tick = axes["A"].xaxis.get_major_ticks()[0]
        assert first_tick.tick1line.get_marker() == 2
        assert first_tick.tick2line.get_marker() == 3
        assert first_tick.tick2line.get_visible()
        assert insets["heat"].get_xlim() == pytest.approx((0.9, 1.01))
        assert insets["heat"].get_ylim() == pytest.approx((1.5, 1.8))
        assert insets["square"].get_xlabel() == "($T/T_{\\rm{c}})^2$"
        assert all(mpl.rcParams[name] == value for name, value in before.items())
    finally:
        plt.close(figure)


def test_publication_export_uses_one_explicit_figure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """PNG and PDF export share one Figure and scoped Type 42 settings."""

    demo = _load_demo()
    figure = Figure()
    observed: dict[str, Any] = {}

    def fake_savefig(target: Figure, path: Path, **options: Any) -> tuple[Path, ...]:
        observed.update(target=target, path=path, options=options)
        observed["fonttypes"] = (
            mpl.rcParams["pdf.fonttype"],
            mpl.rcParams["ps.fonttype"],
        )
        return (path.with_suffix(".png"), path.with_suffix(".pdf"))

    before = (mpl.rcParams["pdf.fonttype"], mpl.rcParams["ps.fonttype"])
    monkeypatch.setattr(demo.gs, "savefig", fake_savefig)
    path = tmp_path / "SC_cal"

    assert demo.save_publication_figure(figure, path) == (
        path.with_suffix(".png"),
        path.with_suffix(".pdf"),
    )
    assert observed == {
        "target": figure,
        "path": path,
        "options": {
            "formats": ("png", "pdf"),
            "dpi": 600,
            "props": {"bbox_inches": "tight"},
            "show": True,
            "overwrite": True,
        },
        "fonttypes": (42, 42),
    }
    assert (mpl.rcParams["pdf.fonttype"], mpl.rcParams["ps.fonttype"]) == before
