"""Integration-edge coverage for canonical I/O, layout, and styling APIs."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.colors import Normalize
from matplotlib.figure import Figure

import gsplot as gs
from gsplot._core import DataError, LayoutError, OutputError, PlotError
from gsplot._core.errors import OptionError
from gsplot._figure import output
from gsplot._io.arrays import read_array
from gsplot._io.metadata import write_meta
from gsplot._io.paths import resolve_path
from gsplot._plot.colormap import cmap_from_config, map_values


def test_array_and_metadata_io_are_explicit_and_atomic(tmp_path: Path) -> None:
    """Text and metadata operations validate controls and preserve files."""

    source = tmp_path / "values.txt"
    source.write_text("1 2\n3 4\n", encoding="utf-8")
    assert read_array(source, loader="loadtxt", ndmin=2).shape == (2, 2)
    assert read_array(source, options={"delimiter": " "}).shape == (2, 2)
    for kwargs in (
        {"path": ""},
        {"path": source, "loader": "bad"},
        {"path": source, "ndmin": 0},
        {"path": source, "options": []},
        {"path": source, "options": {1: "bad"}},
    ):
        with pytest.raises(DataError):
            read_array(**kwargs)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        read_array(source, options={"fname": "other"})
    with pytest.raises(DataError):
        read_array(tmp_path / "missing.txt")

    snapshot = gs.MetadataSnapshot("1.0", labels={"kind": "test"})
    destination = tmp_path / "metadata" / "result.json"
    with pytest.raises(gs.MetadataError):
        write_meta(snapshot, destination)
    written = write_meta(snapshot, destination, create_parent=True)
    assert written == destination.resolve()
    assert '"kind":"test"' in written.read_text(encoding="utf-8")
    with pytest.raises(gs.MetadataError):
        write_meta(snapshot, destination)
    replacement = gs.MetadataSnapshot("1.1", labels={"kind": "updated"})
    write_meta(replacement, destination, overwrite=True)
    assert '"1.1"' in destination.read_text(encoding="utf-8")
    with pytest.raises(gs.MetadataError):
        write_meta(object(), destination)  # type: ignore[arg-type]
    with pytest.raises(gs.MetadataError):
        write_meta(snapshot, destination, overwrite=1)  # type: ignore[arg-type]
    assert resolve_path(destination) == destination.resolve()
    with pytest.raises(OutputError):
        resolve_path("")


def test_output_controls_save_all_formats_before_optional_display(
    tmp_path: Path, monkeypatch
) -> None:
    """Saving validates every destination and displays only after writes."""

    figure, _ = gs.subplots()
    try:
        display_calls: list[object] = []
        original_show = output.show
        monkeypatch.setattr(output, "show", display_calls.append)
        destinations = output.savefig(
            figure,
            tmp_path / "nested" / "plot",
            formats=("png", "pdf"),
            create_parent=True,
            overwrite=True,
            show=True,
        )
        assert tuple(path.suffix for path in destinations) == (".png", ".pdf")
        assert display_calls == [figure]
        with pytest.raises(OutputError):
            output.savefig(figure, destinations[0], show=False)
        output.savefig(figure, destinations[0], overwrite=True, show=False)
        output.savefig(
            figure,
            tmp_path / "closed.png",
            overwrite=True,
            close=True,
            show=False,
        )
        assert not plt.fignum_exists(figure.number)
    finally:
        plt.close("all")

    unmanaged = Figure()
    with pytest.raises(OutputError):
        original_show(unmanaged)
    plt.close("all")


def test_layout_styling_panels_and_themes_cover_explicit_targets() -> None:
    """All renderer-neutral styling helpers operate on supplied objects."""

    figure, axes = gs.subplots(ncols=2, tight_layout=True)
    try:
        assert figure.get_layout_engine() is not None
        figure2, axis2 = gs.subplots(constrained_layout=True)
        assert figure2.get_layout_engine() is not None
        plt.close(figure2)

        spec = gs.AxisSpec(
            xlabel="time",
            ylabel="value",
            xlim=(1, 2),
            ylim=(1, 2),
            xticks=(1, 2),
            yticks=(1, 2),
            xminor=True,
            yminor=False,
            xlabelpad=1,
            ylabelpad=2,
        )
        gs.style_axes(axes, spec)
        assert axes[0].get_xlabel() == "time"
        gs.title(axes[0], "Panel", props={"fontsize": 10})
        gs.suptitle(figure, "Figure", props={"fontsize": 11})
        gs.minor_ticks(axes, False, axis="both")
        gs.box_aspect(axes, 1.0)
        gs.box_aspect(axes, None)
        labels = gs.panel_labels(axes)
        assert tuple(label.get_text() for label in labels) == ("A", "B")
        assert len(gs.panel_labels(axes, labels=("left", "right"))) == 2
        with pytest.raises(LayoutError):
            gs.panel_labels(axes, labels=("one",))
        with pytest.raises(OptionError):
            gs.title(axes[0], "bad", props={"unknown": True})
        with pytest.raises(OptionError):
            gs.legend(axes[0], props={"ncol": 1, "ncols": 1})

        theme = gs.Theme(
            axes_facecolor="white",
            text_color="black",
            spine_color="red",
            tick_color="blue",
            grid=True,
            grid_color="gray",
            grid_alpha=0.5,
        )
        gs.set_theme(axes[0], theme)
        gs.set_theme(figure, gs.Theme(figure_facecolor="white"))
        gs.fig_facecolor(figure, "black")
        with pytest.raises(PlotError):
            gs.set_theme(axes[0], gs.Theme(figure_facecolor="white"))
    finally:
        plt.close(figure)


def test_colormap_and_colored_plot_controls_are_local() -> None:
    """Colormap normalization and colored artists cover public edge paths."""

    assert cmap_from_config(None) == "viridis"
    config = gs.Config.from_mapping(
        {"schema_version": 1, "plotting": {"default_cmap": "plasma"}}
    )
    assert cmap_from_config(config) == "plasma"
    with pytest.raises(PlotError):
        cmap_from_config(object())  # type: ignore[arg-type]
    assert map_values([0, 1], cmap="viridis", norm=Normalize(0, 1)).shape == (2, 4)
    assert map_values([0, 1], cmap="viridis", norm=lambda value, clip: value).shape == (
        2,
        4,
    )

    figure, axis = gs.subplots()
    try:
        collection = gs.cmap_line(axis, [0, 1], [0, 1], [0, 1], norm=(0, 1))
        dashed = gs.cmap_dash(
            axis, [0, 1], [1, 0], [0, 1], dash=(2, 3), props={"alpha": 0.5}
        )
        points = gs.cmap_scatter(axis, [0, 1], [0, 1], [0, 1])
        assert collection.axes is axis
        assert len(dashed) == 1
        assert points.axes is axis
        with pytest.raises(OptionError):
            gs.cmap_dash(
                axis,
                [0, 1],
                [0, 1],
                [0, 1],
                dash=(1, 1),
                props={"linestyles": "solid"},
            )
        with pytest.raises(DataError):
            gs.cmap_scatter(axis, [0, 1], [0, 1], [0])
    finally:
        plt.close(figure)
