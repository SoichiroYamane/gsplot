"""Tests for root-level canonical/legacy dispatch boundaries."""

import inspect
import warnings
from pathlib import Path
from typing import get_args, get_type_hints

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.colors import to_rgba

import gsplot as gs
from gsplot._compat import root_api
from gsplot._compat.legacy.figure.store import StoreSingleton
from gsplot._compat.legacy.plot.line_base import NumLines


def test_root_canonical_signature_and_finite_line_options_are_available() -> None:
    """The concise view and retained long or positional styles share one binder."""

    figure, ax = gs.subplots()
    assert "props" in str(inspect.signature(gs.line))
    canonical = gs.line(ax, [0, 1], [1, 2], props={"label": "canonical"})
    assert canonical[0].axes is ax
    advanced = gs.line(ax, [0, 1], [2, 3], color="red", marker="o")
    positional = gs.line(ax, [0, 1], [3, 4], "blue", "s")
    assert advanced[0].axes is ax
    assert np.allclose(to_rgba(positional[0].get_color()), to_rgba("blue"))
    plt.close(figure)


def test_root_default_colors_use_each_native_axes_cycle_without_hidden_state() -> None:
    """Line and scatter use their target cycles rather than a shared counter."""

    NumLines.reset()
    figure, ax = plt.subplots()
    ax.set_prop_cycle(color=["red", "blue"])
    try:
        line = gs.line(ax, [0, 1], [1, 2])[0]
        scatter = gs.scatter(ax, [0, 1], [2, 3])
        assert np.allclose(to_rgba(line.get_color()), to_rgba("red"))
        assert line.get_marker() == "o"
        assert line.get_markersize() == 7.0
        assert line.get_markeredgewidth() == 1.5
        assert line.get_linestyle() == "--"
        assert line.get_linewidth() == 1.0
        assert to_rgba(line.get_markerfacecolor())[3] == pytest.approx(0.2)
        assert np.allclose(scatter.get_facecolors()[0], to_rgba("red"))
        assert scatter.get_sizes().tolist() == [1.0]
        assert scatter.get_alpha() == 1.0
    finally:
        NumLines.reset()
        plt.close(figure)


def test_legacy_axes_preserve_the_shared_viridis_plot_sequence() -> None:
    """Only deprecated gs.axes targets retain the shared 0.3 color counter."""

    with pytest.warns(DeprecationWarning, match="gsplot.axes"):
        axes = gs.axes()
    axis = axes[0]
    figure = axis.figure
    axis.set_prop_cycle(color=["red", "blue"])
    try:
        line = gs.line(axis, [0, 1], [1, 2])[0]
        scatter = gs.scatter(axis, [0, 1], [2, 3])
        expected = gs.sample_cmap("viridis", count=5)
        assert np.allclose(to_rgba(line.get_color()), expected[0])
        assert np.allclose(scatter.get_facecolors()[0], expected[1])
    finally:
        NumLines.reset()
        plt.close(figure)


def test_legacy_axes_and_show_preserve_layout_and_store_defaults(
    tmp_path, monkeypatch
) -> None:
    """The current-object adapter keeps its old layout and save gate."""

    monkeypatch.chdir(tmp_path)
    StoreSingleton().store = False
    try:
        with pytest.warns(DeprecationWarning, match="gsplot.axes"):
            axes = gs.axes()
        figure = axes[0].figure
        assert tuple(figure.get_size_inches()) == (5.0, 5.0)
        assert figure.get_layout_engine() is not None

        with pytest.warns(DeprecationWarning, match="legacy gsplot.show"):
            gs.show(show=False)
        assert not tuple(tmp_path.iterdir())

        with pytest.warns(DeprecationWarning, match="gsplot.axes"):
            gs.axes(store=True)
        with pytest.warns(DeprecationWarning, match="legacy gsplot.show"):
            gs.show(show=False)
        assert {path.name for path in tmp_path.iterdir()} == {
            "gsplot.png",
            "gsplot.pdf",
        }
    finally:
        StoreSingleton().store = False
        NumLines.reset()
        plt.close("all")


def test_legacy_show_restores_the_historical_tight_crop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The 0.3 save adapter supplies tight cropping unless overridden."""

    calls: list[dict[str, object]] = []

    def capture(*args: object, **kwargs: object) -> tuple[Path, ...]:
        calls.append(dict(kwargs))
        return ()

    monkeypatch.setattr(root_api, "_savefig", capture)
    StoreSingleton().store = True
    try:
        with pytest.warns(DeprecationWarning, match="legacy gsplot.show"):
            gs.show(show=False)
    finally:
        StoreSingleton().store = False

    assert calls[0]["props"] == {"bbox_inches": "tight"}


def test_root_canonical_annotations_are_runtime_resolvable() -> None:
    """Lazy root adapters preserve evaluated canonical type annotations."""

    config_hint = get_type_hints(gs.line)["config"]
    assert config_hint.__args__[0].__name__ == "Config"
    assert any(
        value.__name__ == "PathCollection"
        for value in get_args(get_type_hints(gs.scatter)["return"])
    )
    assert get_type_hints(gs.show)["return"] is type(None)
    assert "AxesTarget" in str(inspect.signature(gs.show))
    assert get_type_hints(gs.label)["xlabel"] != object
    assert "LabelRecords" in str(inspect.signature(gs.label))
    assert get_type_hints(gs.legend)["loc"] == str | int


def test_root_show_dispatches_axes_targets_without_legacy_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Explicit Axes collections select canonical display-only behavior."""

    figure, axes = plt.subplots(1, 2)
    calls: list[object] = []
    monkeypatch.setattr(root_api, "_show", calls.append)
    try:
        assert gs.show(axes) is None
    finally:
        plt.close(figure)

    assert calls == [axes]


def test_root_show_rejects_every_legacy_save_option_for_canonical_targets() -> None:
    """Canonical Figure and Axes display cannot silently ignore save options."""

    figure, axis = plt.subplots()
    try:
        with pytest.raises(TypeError, match="does not accept legacy save options"):
            gs.show(figure, bbox_inches="tight")
        with pytest.raises(TypeError, match="does not accept legacy save options"):
            gs.show(axis, transparent=True)
    finally:
        plt.close(figure)


def test_root_label_dispatches_without_current_figure_guessing() -> None:
    """Explicit targets stay concise while non-empty old records remain usable."""

    figure, axis = plt.subplots()
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            gs.label(axis, "time", "signal", square=True, index="in")
        assert not any(issubclass(item.category, DeprecationWarning) for item in caught)
        assert axis.get_xlabel() == "time"
        assert axis.get_ylabel() == "signal"
        assert axis.get_box_aspect() == 1
        assert axis.texts[0].get_text() == "(a)"

        with pytest.warns(DeprecationWarning, match="gsplot.label"):
            gs.label([["legacy x", "legacy y"]], 7, 8, False, False, 3, 4)
        assert axis.get_xlabel() == "legacy x"
        assert axis.get_ylabel() == "legacy y"
        assert axis.xaxis.labelpad == 7
        assert axis.yaxis.labelpad == 8

        with pytest.warns(DeprecationWarning, match="gsplot.label"):
            gs.label(lab_lims=[["keyword x", "keyword y"]], tight_layout=False)
        assert axis.get_xlabel() == "keyword x"
        assert axis.get_ylabel() == "keyword y"
    finally:
        plt.close(figure)


def test_root_label_rejects_empty_or_unknown_forms_before_pyplot_state() -> None:
    """Ambiguous first arguments fail without creating a current Figure."""

    plt.close("all")
    before = tuple(plt.get_fignums())
    with pytest.raises(TypeError, match="non-empty"):
        gs.label([])
    with pytest.raises(TypeError, match="AxesTarget"):
        gs.label(["x", "y"])
    assert tuple(plt.get_fignums()) == before


def test_root_legend_treats_publication_controls_as_canonical() -> None:
    """Direct concise controls do not enter the deprecated legacy branch."""

    figure, axis = plt.subplots()
    try:
        axis.plot([0, 1], [0, 1], label="signal")
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            created = gs.legend(axis, loc="lower right", handlelength=3)
        assert not any(issubclass(item.category, DeprecationWarning) for item in caught)
        assert created._loc == 4
        assert created.handlelength == 3

        with pytest.warns(DeprecationWarning, match="legacy gsplot.legend"):
            replaced = gs.legend(axis, ncols=1, replace=True)
        assert replaced.axes is axis
    finally:
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


def test_nontranslating_legacy_helpers_warn_without_side_effects(capsys) -> None:
    """Legacy helpers that have no canonical translation do not mutate state."""

    original = Path.cwd()
    with pytest.warns(DeprecationWarning, match="no-op"):
        assert gs.pwd_move() is None
    assert Path.cwd() == original

    with pytest.warns(DeprecationWarning, match="documentation-only"):
        assert gs.hello_world() is None
    assert capsys.readouterr().out == ""

    with pytest.warns(DeprecationWarning, match="MetadataSnapshot"), pytest.raises(
        gs.MetadataError, match="implicit metadata"
    ):
        gs.save_metadata()


def test_historical_logger_is_a_side_effect_free_noop(tmp_path, monkeypatch) -> None:
    """The retained root lookup cannot recreate the removed application log."""

    monkeypatch.setenv("HOME", str(tmp_path))
    before = tuple(tmp_path.rglob("*"))
    with pytest.warns(DeprecationWarning, match="no-op"):
        assert gs.logger() is None
    assert tuple(tmp_path.rglob("*")) == before


def test_root_load_config_translates_only_schema_less_legacy_files(tmp_path) -> None:
    """The root boundary warns for old files while canonical files stay strict."""

    legacy = tmp_path / "legacy.json"
    legacy.write_text(
        '{"rcParams": {"figure.figsize": [2, 3]}, "metadata": false}',
        encoding="utf-8",
    )
    with pytest.warns(DeprecationWarning, match="schema-less"):
        config = gs.load_config(legacy)
    with pytest.warns(DeprecationWarning, match="figsize"):
        assert config.figure.figsize == (2.0, 3.0)
    assert config.schema_version == 2

    strict = tmp_path / "strict.json"
    strict.write_text('{"figure": {"figsize": [2, 3]}}', encoding="utf-8")
    with pytest.raises(gs.ConfigError, match="schema_version"):
        gs.Config.from_file(strict)
