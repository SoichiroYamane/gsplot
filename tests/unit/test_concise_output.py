"""Tests for concise transactional Figure output and display."""

from pathlib import Path

import matplotlib as mpl
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


def test_save_renders_every_format_before_ordered_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Successful concise output uses tight defaults, Type 42, then display."""

    figure = Figure()
    png = tmp_path / "plot.png"
    pdf = tmp_path / "plot.pdf"
    png.write_bytes(b"old-png")
    pdf.write_bytes(b"old-pdf")
    calls: list[tuple[Path, str, dict[str, object], int, int]] = []
    displays: list[Figure] = []
    original_pdf_fonttype = mpl.rcParams["pdf.fonttype"]
    original_ps_fonttype = mpl.rcParams["ps.fonttype"]

    def render(path: Path, *, format: str, **kwargs: object) -> None:
        calls.append(
            (
                path,
                format,
                kwargs,
                mpl.rcParams["pdf.fonttype"],
                mpl.rcParams["ps.fonttype"],
            )
        )
        assert png.read_bytes() == b"old-png"
        assert pdf.read_bytes() == b"old-pdf"
        path.write_bytes(format.encode("ascii"))

    monkeypatch.setattr(figure, "savefig", render)
    monkeypatch.setattr(output, "show", displays.append)

    paths = output.save(
        figure,
        tmp_path / "plot",
        show=True,
        metadata={"Title": "sample"},
    )

    assert paths == (png.resolve(), pdf.resolve())
    assert png.read_bytes() == b"png"
    assert pdf.read_bytes() == b"pdf"
    assert tuple(item[1] for item in calls) == ("png", "pdf")
    assert all(item[0].parent == tmp_path for item in calls)
    assert all(item[0] not in paths for item in calls)
    assert all(item[2]["dpi"] == 600.0 for item in calls)
    assert all(item[2]["bbox_inches"] == "tight" for item in calls)
    assert all(item[2]["pad_inches"] == 0.1 for item in calls)
    assert all(item[2]["metadata"] == {"Title": "sample"} for item in calls)
    assert all(item[3:] == (42, 42) for item in calls)
    assert mpl.rcParams["pdf.fonttype"] == original_pdf_fonttype
    assert mpl.rcParams["ps.fonttype"] == original_ps_fonttype
    assert displays == [figure]
    assert {path.name for path in tmp_path.iterdir()} == {"plot.png", "plot.pdf"}


def test_save_render_failure_preserves_every_existing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A later render failure removes temporaries without replacing finals."""

    figure = Figure()
    png = tmp_path / "plot.png"
    pdf = tmp_path / "plot.pdf"
    png.write_bytes(b"old-png")
    pdf.write_bytes(b"old-pdf")
    calls = 0

    def render(path: Path, *, format: str, **kwargs: object) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("render failed")
        path.write_bytes(format.encode("ascii"))

    monkeypatch.setattr(figure, "savefig", render)

    with pytest.raises(gs.OutputError, match="could not be rendered") as caught:
        output.save(figure, tmp_path / "plot", show=False)

    assert caught.value.committed_paths == ()
    assert png.read_bytes() == b"old-png"
    assert pdf.read_bytes() == b"old-pdf"
    assert {path.name for path in tmp_path.iterdir()} == {"plot.png", "plot.pdf"}


def test_save_partial_commit_reports_exact_paths_and_cleans_temporaries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A replacement failure exposes only finals already replaced in order."""

    figure = Figure()
    png = tmp_path / "plot.png"
    pdf = tmp_path / "plot.pdf"
    png.write_bytes(b"old-png")
    pdf.write_bytes(b"old-pdf")

    def render(path: Path, *, format: str, **kwargs: object) -> None:
        path.write_bytes(format.encode("ascii"))

    replacements = 0
    original_replace = output.os.replace

    def replace(source: Path, destination: Path) -> None:
        nonlocal replacements
        replacements += 1
        if replacements == 2:
            raise OSError("replace failed")
        original_replace(source, destination)

    monkeypatch.setattr(figure, "savefig", render)
    monkeypatch.setattr(output.os, "replace", replace)

    with pytest.raises(gs.OutputError, match="could not all be committed") as caught:
        output.save(figure, tmp_path / "plot", show=False)

    assert caught.value.committed_paths == (png.resolve(),)
    assert str(tmp_path) not in str(caught.value)
    assert png.read_bytes() == b"png"
    assert pdf.read_bytes() == b"old-pdf"
    assert {path.name for path in tmp_path.iterdir()} == {"plot.png", "plot.pdf"}


def test_save_exact_canvas_parent_creation_and_post_commit_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exact-canvas output creates parents and retains commit evidence."""

    figure = Figure()
    parent = tmp_path / "nested"
    calls: list[dict[str, object]] = []

    def render(path: Path, *, format: str, **kwargs: object) -> None:
        calls.append(kwargs)
        path.write_bytes(b"png")

    def fail_display(target: Figure) -> None:
        raise gs.OutputError("display failure")

    monkeypatch.setattr(figure, "savefig", render)
    monkeypatch.setattr(output, "show", fail_display)

    with pytest.raises(gs.OutputError, match="outputs were committed") as caught:
        output.save(
            figure,
            parent / "plot.png",
            crop=False,
            show=True,
            create_parent=True,
        )

    destination = (parent / "plot.png").resolve()
    assert destination.read_bytes() == b"png"
    assert caught.value.committed_paths == (destination,)
    assert "bbox_inches" not in calls[0]
    assert "pad_inches" not in calls[0]


def test_show_is_a_noninteractive_no_op_for_figure_and_axes_targets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A non-GUI canvas emits no warning and never calls Figure.show."""

    figure, axes = plt.subplots(1, 2)
    calls: list[bool] = []
    monkeypatch.setattr(figure, "show", lambda *, warn: calls.append(warn))
    try:
        output.show(figure)
        output.show(axes)
    finally:
        plt.close(figure)

    assert calls == []


def test_show_requires_a_manager_only_for_interactive_canvas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Interactive display invokes the resolved Figure exactly once."""

    figure, axis = plt.subplots()
    calls: list[bool] = []
    monkeypatch.setattr(
        type(figure.canvas), "required_interactive_framework", "test", raising=False
    )
    monkeypatch.setattr(figure.canvas, "manager", None)
    try:
        with pytest.raises(gs.OutputError, match="requires a managed Figure"):
            output.show(axis)

        monkeypatch.setattr(figure.canvas, "manager", object())
        monkeypatch.setattr(figure, "show", lambda *, warn: calls.append(warn))
        output.show(axis)
    finally:
        plt.close(figure)

    assert calls == [False]


def test_save_close_affects_only_the_resolved_figure(tmp_path: Path) -> None:
    """Successful close never depends on or closes another current Figure."""

    saved, saved_axis = plt.subplots()
    unrelated, _ = plt.subplots()
    try:
        plt.figure(unrelated.number)
        paths = output.save(
            saved_axis,
            tmp_path / "closed.png",
            show=False,
            close=True,
        )

        assert paths == ((tmp_path / "closed.png").resolve(),)
        assert not plt.fignum_exists(saved.number)
        assert plt.fignum_exists(unrelated.number)
    finally:
        plt.close("all")


def test_savefig_direct_kwargs(tmp_path: Path) -> None:
    """savefig accepts direct kwargs alongside props."""

    figure, ax = plt.subplots()
    try:
        paths = output.savefig(
            figure,
            tmp_path / "custom.png",
            show=False,
            transparent=True,
            facecolor="white",
        )
        assert len(paths) == 1
        assert paths[0].exists()
    finally:
        plt.close(figure)
