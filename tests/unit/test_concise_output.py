"""Tests for concise transactional Figure output and display."""

from pathlib import Path

import matplotlib.pyplot as plt
import pytest
from matplotlib.figure import Figure

import gsplot as gs
from gsplot._figure import output


def test_output_error_records_committed_paths_as_an_immutable_tuple(
    tmp_path: Path,
) -> None:
    """Output failures expose exact machine-readable commit evidence."""

    destination = (tmp_path / "plot.png").resolve()
    error = gs.OutputError("public-safe failure", committed_paths=[destination])

    assert str(error) == "public-safe failure"
    assert error.committed_paths == (destination,)
    assert isinstance(error.committed_paths, tuple)


def test_save_plan_resolves_one_figure_and_historical_defaults(tmp_path: Path) -> None:
    """Figure and Axes targets produce one immutable normalized output plan."""

    figure, axes = plt.subplots(1, 2)
    try:
        plan = output._save_plan(
            axes,
            tmp_path / "plot",
            formats=None,
            dpi=600,
            crop=True,
            pad=None,
            show=True,
            close=False,
            create_parent=False,
            overwrite=True,
            transparent=False,
            metadata={"Title": "sample"},
        )

        assert plan.figure is figure
        assert plan.formats == ("png", "pdf")
        assert tuple(path.suffix for path in plan.destinations) == (".png", ".pdf")
        assert all(path.is_absolute() for path in plan.destinations)
        assert plan.dpi == 600.0
        assert plan.pad == 0.1
        assert plan.metadata == (("Title", "sample"),)
    finally:
        plt.close(figure)


@pytest.mark.parametrize(
    ("updates", "message"),
    [
        ({"formats": ()}, "formats must not be empty"),
        ({"formats": ("PNG", ".png")}, "unique"),
        ({"formats": ("../png",)}, "path separator"),
        ({"dpi": 0}, "dpi"),
        ({"dpi": True}, "dpi"),
        ({"crop": False, "pad": 0}, "pad requires"),
        ({"pad": -1}, "pad"),
        ({"close": True}, "mutually exclusive"),
        ({"metadata": {1: "bad"}}, "metadata"),
    ],
)
def test_save_plan_rejects_invalid_controls_before_mutation(
    tmp_path: Path, updates: dict[str, object], message: str
) -> None:
    """Every concise control is validated before output paths are changed."""

    options: dict[str, object] = {
        "formats": None,
        "dpi": 600,
        "crop": True,
        "pad": None,
        "show": True,
        "close": False,
        "create_parent": False,
        "overwrite": True,
        "transparent": False,
        "metadata": None,
    }
    options.update(updates)

    with pytest.raises(gs.OutputError, match=message):
        output._save_plan(Figure(), tmp_path / "plot", **options)  # type: ignore[arg-type]
    assert not tuple(tmp_path.iterdir())


def test_save_plan_rejects_ambiguous_targets_and_unsafe_destinations(
    tmp_path: Path,
) -> None:
    """Mixed Figures, symlinks, non-files, and forbidden replacement fail."""

    first, first_axis = plt.subplots()
    second, second_axis = plt.subplots()
    options = {
        "formats": None,
        "dpi": 600,
        "crop": True,
        "pad": None,
        "show": False,
        "close": False,
        "create_parent": False,
        "overwrite": True,
        "transparent": False,
        "metadata": None,
    }
    try:
        with pytest.raises(gs.OutputError, match="exactly one"):
            output._save_plan([first_axis, second_axis], tmp_path / "mixed", **options)

        regular = tmp_path / "regular.png"
        regular.write_bytes(b"original")
        with pytest.raises(gs.OutputError, match="already exists"):
            output._save_plan(
                first,
                regular,
                **{**options, "formats": "png", "overwrite": False},
            )

        symlink = tmp_path / "linked.png"
        symlink.symlink_to(regular)
        with pytest.raises(gs.OutputError, match="symlink"):
            output._save_plan(first, symlink, **{**options, "formats": "png"})

        directory = tmp_path / "directory.png"
        directory.mkdir()
        with pytest.raises(gs.OutputError, match="regular file"):
            output._save_plan(first, directory, **{**options, "formats": "png"})
    finally:
        plt.close(first)
        plt.close(second)


def test_save_plan_allows_opt_in_parent_creation_without_creating_it(
    tmp_path: Path,
) -> None:
    """Preflight is side-effect free even when parent creation is authorized."""

    parent = tmp_path / "nested"
    plan = output._save_plan(
        Figure(),
        parent / "plot.PDF",
        formats="pdf",
        dpi=600,
        crop=False,
        pad=None,
        show=False,
        close=False,
        create_parent=True,
        overwrite=True,
        transparent=True,
        metadata=None,
    )

    assert plan.destinations == ((parent / "plot.pdf").resolve(),)
    assert plan.pad is None
    assert not parent.exists()
