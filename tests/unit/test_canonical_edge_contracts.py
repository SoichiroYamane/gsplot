"""Boundary coverage for the canonical value and Matplotlib adapters."""

from dataclasses import FrozenInstanceError

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.figure import Figure

import gsplot as gs
from gsplot._config.schema import parse_json_text
from gsplot._core import (
    DataError,
    LayoutError,
    MetadataError,
    PlotError,
    ensure_bool,
    ensure_finite_real,
    ensure_iterable,
    ensure_mapping,
    ensure_nonempty_text,
    ensure_nonnegative,
    ensure_positive,
    reject_unknown_keys,
)
from gsplot._figure import output
from gsplot._figure.backend import use_backend
from gsplot._figure.inset import inset_axes
from gsplot._style.axes import style_axes


@pytest.mark.parametrize(
    ("function", "value"),
    [
        (ensure_finite_real, "bad"),
        (ensure_finite_real, float("inf")),
        (ensure_positive, 0),
        (ensure_nonnegative, -1),
        (ensure_bool, 1),
        (ensure_nonempty_text, " "),
        (ensure_mapping, []),
        (ensure_iterable, 1),
    ],
)
def test_validation_helpers_reject_invalid_values(function, value) -> None:
    """Shared validators use their typed error boundary."""

    error = (
        DataError if function in {ensure_finite_real, ensure_iterable} else LayoutError
    )
    if function in {ensure_bool, ensure_nonempty_text, ensure_mapping}:
        error = LayoutError if function is ensure_bool else DataError
    with pytest.raises(Exception):
        function(value, "value", error=error)

    with pytest.raises(Exception):
        reject_unknown_keys({"unexpected": 1}, set(), "test")


def test_value_types_reject_invalid_colors_layouts_and_metadata() -> None:
    """Immutable public values validate all boundary fields before mutation."""

    with pytest.raises(LayoutError):
        gs.AxisSpec(xscale=None)  # type: ignore[arg-type]
    with pytest.raises(LayoutError):
        gs.AxisSpec(xlim=(1, 1))
    with pytest.raises(LayoutError):
        gs.AxisSpec(xticks="bad")  # type: ignore[arg-type]
    with pytest.raises(PlotError):
        gs.Theme(axes_facecolor="not-a-color")
    with pytest.raises(PlotError):
        gs.Theme(grid_alpha=float("nan"))
    with pytest.raises(PlotError):
        gs.Theme(grid="yes")  # type: ignore[arg-type]

    with pytest.raises(LayoutError):
        gs.InsetSpec()
    with pytest.raises(LayoutError):
        gs.InsetSpec(bounds=(0, 0, 0, 1))
    with pytest.raises(LayoutError):
        gs.InsetSpec(width="0%", height="20%")
    with pytest.raises(LayoutError):
        gs.InsetSpec(width="20%", height="20%", loc="invalid")
    with pytest.raises(LayoutError):
        gs.InsetSpec(width=1, height=1, bbox_to_anchor=(1,))
    with pytest.raises(LayoutError, match="bbox_to_anchor"):
        gs.InsetSpec(width=1, height=1, bbox_to_anchor=1)  # type: ignore[arg-type]
    with pytest.raises(LayoutError):
        gs.InsetSpec(width=1, height=1, borderpad=-1)

    with pytest.raises(MetadataError):
        gs.MetadataSnapshot("")
    with pytest.raises(MetadataError):
        gs.MetadataSnapshot("1", commit="")
    with pytest.raises(MetadataError):
        gs.MetadataSnapshot("1", labels={"x": 1})  # type: ignore[dict-item]
    with pytest.raises(MetadataError):
        gs.MetadataSnapshot("1", labels=[])  # type: ignore[arg-type]
    with pytest.raises(MetadataError):
        gs.MetadataSnapshot("1", labels={"x" * 257: "value"})
    with pytest.raises(MetadataError):
        gs.BuildInfo("")
    with pytest.raises(PlotError):
        gs.LegendEntries(handles=[object()], labels=[])
    with pytest.raises(PlotError):
        gs.LegendEntries(handles=[object()], labels=[1])  # type: ignore[list-item]
    with pytest.raises(PlotError):
        gs.LegendEntries(handles=object(), labels=())  # type: ignore[arg-type]
    with pytest.raises(PlotError):
        gs.LegendEntries(handles=(), labels=(), handler_map=[])  # type: ignore[arg-type]


def test_strict_json_and_colormap_edges() -> None:
    """Strict parsers and pure color sampling reject ambiguous controls."""

    with pytest.raises(gs.ConfigError):
        parse_json_text("[]")
    with pytest.raises(gs.ConfigError):
        parse_json_text('{"x": NaN}')
    with pytest.raises(gs.ConfigError):
        parse_json_text('{"x": 1} trailing')
    with pytest.raises(gs.ConfigError):
        parse_json_text('{"x": 1, "x": 2}')

    with pytest.raises(PlotError):
        gs.sample_cmap("viridis", count=0)
    with pytest.raises(PlotError):
        gs.sample_cmap("viridis", count=2, values=[0, 1])
    with pytest.raises(Exception):
        gs.sample_cmap("viridis", values=[0, 1], norm=(1, 0))
    with pytest.raises(PlotError):
        gs.sample_cmap("missing-colormap", count=2)
    colors = gs.sample_cmap("viridis", values=[3, 3])
    assert np.allclose(colors[0], colors[1])


def test_layout_inset_and_style_edges_are_explicit() -> None:
    """Layout and styling errors occur without implicit current-object targets."""

    with pytest.raises(LayoutError):
        gs.subplots(nrows=0)
    with pytest.raises(LayoutError):
        gs.subplots(mosaic=[])
    with pytest.raises(LayoutError):
        gs.subplots(mosaic=[["A"], ["A", "B"]])
    with pytest.raises(LayoutError):
        gs.subplots(mosaic=[[1]])  # type: ignore[list-item]
    with pytest.raises(LayoutError):
        gs.subplots(figsize=(1, 1), unit="bad")  # type: ignore[arg-type]

    figure, axis = gs.subplots()
    try:
        child = inset_axes(axis, gs.InsetSpec(width="25%", height="25%"))
        assert child.figure is figure
        with pytest.raises(LayoutError):
            inset_axes(axis, object())  # type: ignore[arg-type]
        with pytest.raises(LayoutError):
            style_axes(axis, object())  # type: ignore[arg-type]
        with pytest.raises(Exception):
            gs.title(object(), "bad")  # type: ignore[arg-type]
        with pytest.raises(PlotError):
            gs.suptitle(object(), "bad")  # type: ignore[arg-type]
        with pytest.raises(LayoutError):
            gs.minor_ticks(axis, True, axis="bad")  # type: ignore[arg-type]
        with pytest.raises(LayoutError):
            gs.box_aspect(axis, 0)
        with pytest.raises(PlotError):
            gs.fig_facecolor(object(), "white")  # type: ignore[arg-type]
    finally:
        plt.close(figure)

    with pytest.raises(gs.ConfigError):
        use_backend("")


def test_output_validation_happens_before_writes(tmp_path, monkeypatch) -> None:
    """Output controls and save failures cannot trigger a partial display."""

    figure = Figure()
    displayed: list[Figure] = []
    monkeypatch.setattr(output, "show", displayed.append)
    with pytest.raises(gs.OutputError):
        output.savefig(figure, tmp_path / "plot", formats=(), show=False)
    with pytest.raises(gs.OutputError):
        output.savefig(figure, tmp_path / "plot", formats=("jpg",), show=False)
    with pytest.raises(gs.OutputError):
        output.savefig(figure, tmp_path / "plot", formats=("png",), dpi=0, show=False)
    with pytest.raises(TypeError):
        output.savefig(figure, tmp_path / "plot", props={"show": False}, show=False)
    missing_parent = tmp_path / "private" / "user" / "home" / "secret" / "out"
    with pytest.raises(gs.OutputError) as missing_error:
        output.savefig(figure, missing_parent / "plot", show=False)
    assert str(missing_parent) not in str(missing_error.value)

    def fail(*args, **kwargs):
        raise RuntimeError("save failure")

    monkeypatch.setattr(figure, "savefig", fail)
    output_path = tmp_path / "private" / "user" / "home" / "secret" / "plot.png"
    output_path.parent.mkdir(parents=True)
    with pytest.raises(gs.OutputError) as save_error:
        output.savefig(figure, output_path, show=True, overwrite=True)
    assert str(output_path) not in str(save_error.value)
    assert save_error.value.committed_paths == ()
    assert isinstance(save_error.value.__cause__, RuntimeError)
    assert displayed == []
    plt.close(figure)


def test_legend_and_theme_operations_keep_state_local() -> None:
    """Legend replacement and theme operations use explicit local targets."""

    figure, axis = gs.subplots()
    try:
        gs.line(axis, [0, 1], [0, 1], props={"label": "one"})
        first = gs.legend(axis)
        with pytest.raises(LayoutError):
            gs.legend(axis)
        second = gs.legend(axis, replace=True)
        assert first not in axis.get_children()
        assert second in axis.get_children()
        created = gs.legends(figure, replace=True)
        assert len(created) == 1
        assert created[0] in axis.get_children()
        with pytest.raises(PlotError):
            gs.legend(object())  # type: ignore[arg-type]
        with pytest.raises(PlotError):
            gs.legends([])
        entries = gs.legend_entries(axis)
        assert entries.labels == ("one",)
        gs.set_theme(figure, gs.Theme.transparent())
        assert figure.patch.get_facecolor()[3] == 0
    finally:
        plt.close(figure)


def test_basic_and_colored_plotters_reject_invalid_controls_without_artists() -> None:
    """Plot adapters validate data and controlled properties before mutation."""

    figure, axis = gs.subplots()
    try:
        with pytest.raises(DataError):
            gs.line(axis, [0, np.inf], [0, 1])
        with pytest.raises(DataError):
            gs.scatter(axis, [0], [0, 1])
        with pytest.raises(PlotError):
            gs.cmap_dash(axis, [0, 1], [0, 1], [0, 1], dash=(0, 1))
        with pytest.raises(PlotError):
            gs.cmap_line(axis, [0, 1], [0, 1], [0, 1], props={"color": "red"})
        with pytest.raises(PlotError):
            gs.cmap_scatter(
                axis,
                [0, 1],
                [0, 1],
                [0, 1],
                props={"facecolors": "red"},
            )
        with pytest.raises(TypeError):
            gs.scatter(axis, [0, 1], [0, 1], props={"color": "red", "c": "blue"})
        assert not axis.lines
        assert not axis.collections
    finally:
        plt.close(figure)


def test_immutable_values_remain_detached_from_inputs() -> None:
    """Frozen values do not retain mutable caller containers."""

    source = [0.0, 1.0]
    spec = gs.AxisSpec(xlim=source)
    source[0] = 99
    assert spec.xlim == (0.0, 1.0)
    with pytest.raises(FrozenInstanceError):
        spec.xlim = (1.0, 2.0)  # type: ignore[misc]
