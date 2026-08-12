"""Tests for explicit output, data-loading, and metadata APIs."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pytest
from matplotlib.figure import Figure

from gsplot._core import DataError, MetadataError, MetadataSnapshot, OutputError
from gsplot._figure import output
from gsplot._io.arrays import read_array
from gsplot._io.build import build_info
from gsplot._io.metadata import write_meta


def test_savefig_validates_paths_and_displays_only_after_success(
    tmp_path, monkeypatch
) -> None:
    """Stems, parent creation, default display, and overwrite are explicit."""

    figure = Figure()
    displayed: list[Figure] = []
    monkeypatch.setattr(output, "show", displayed.append)
    destination = output.savefig(
        figure,
        tmp_path / "nested" / "plot",
        formats=("PNG", "svg"),
        create_parent=True,
    )
    assert destination == (
        (tmp_path / "nested" / "plot.png").resolve(),
        (tmp_path / "nested" / "plot.svg").resolve(),
    )
    assert displayed == [figure]
    with pytest.raises(OutputError, match="already exists"):
        output.savefig(figure, tmp_path / "nested" / "plot.png", show=False)
    with pytest.raises(OutputError, match="matching"):
        output.savefig(figure, tmp_path / "other.pdf", formats=("png",), show=False)
    with pytest.raises(OutputError, match="mutually"):
        output.savefig(figure, tmp_path / "closed.png", close=True, show=True)
    plt.close("all")


def test_show_is_noninteractive_noop_and_close_is_explicit(tmp_path) -> None:
    """Headless display does not save, and close follows successful writes."""

    output.show(Figure())
    figure, _ = plt.subplots()
    destination = output.savefig(
        figure,
        tmp_path / "closed.png",
        show=False,
        close=True,
    )
    assert destination[0].exists()
    assert not plt.fignum_exists(figure.number)


def test_read_array_has_one_loader_boundary_and_preserves_cwd(tmp_path) -> None:
    """The data adapter does not change process location or accept duplicate controls."""

    source = tmp_path / "values.txt"
    source.write_text("1 2\n3 4\n", encoding="utf-8")
    cwd = Path.cwd()
    loaded = read_array(source, loader="loadtxt")
    assert loaded.shape == (2, 2)
    assert Path.cwd() == cwd
    with pytest.raises(DataError, match="reserved"):
        read_array(source, options={"ndmin": 2})
    with pytest.raises(DataError, match="reserved"):
        read_array(source, options={"loader": "genfromtxt"})


def test_metadata_is_bounded_stable_and_no_replace_by_default(tmp_path) -> None:
    """Metadata writes use explicit destinations and stable public JSON."""

    snapshot = MetadataSnapshot(
        "0.4.0",
        labels={"experiment": "demo"},
        config_digest="abc",
    )
    destination = write_meta(
        snapshot, tmp_path / "meta" / "run.json", create_parent=True
    )
    assert destination.is_absolute()
    document = json.loads(destination.read_text(encoding="utf-8"))
    assert document["package_version"] == "0.4.0"
    assert list(document) == [
        "commit",
        "config_digest",
        "labels",
        "package_version",
        "schema_version",
    ]
    with pytest.raises(MetadataError, match="already exists"):
        write_meta(snapshot, destination)
    replacement = write_meta(snapshot, destination, overwrite=True)
    assert replacement == destination
    assert build_info().version


def test_metadata_and_legend_value_inputs_are_defensively_normalized() -> None:
    """Public sequence and optional mapping inputs are normalized and frozen."""

    from gsplot import LegendEntries

    labels = ["one"]
    handles = [object()]
    snapshot = MetadataSnapshot("0.4.0", labels={"run": "one"})
    entries = LegendEntries(handles=handles, labels=labels)
    labels.append("two")
    assert snapshot.labels == {"run": "one"}
    assert entries.labels == ("one",)
    assert entries.handler_map == {}
