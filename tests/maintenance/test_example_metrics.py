"""Tests for frozen publication-reform baselines and source metrics."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

from tools.maintenance.check_example_metrics import (
    Metrics,
    check_budgets,
    compare_expected,
    load_manifest,
    main,
    measure,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = PROJECT_ROOT / "tools/maintenance/example-metrics.json"
PROTOTYPE_PATH = (
    PROJECT_ROOT / "tools/maintenance/fixtures/publication_tuple_prototype.py"
)
STYLE_PATH = PROJECT_ROOT / "tests/fixtures/reform/publication-style-v1.json"


def test_metrics_are_token_and_ast_aware(tmp_path: Path) -> None:
    """Comments are removed without stripping hashes inside Python strings."""

    source = tmp_path / "fixture.py"
    source.write_text(
        '"""A # inside a docstring is not a comment."""\n'
        "\n"
        'value = "# inside a string"  # remove this inline comment\n'
        "# remove this full-line comment\n"
        'value += "!"  # and remove this comment\n',
        encoding="utf-8",
    )

    assert measure(source) == Metrics(
        physical_lines=5,
        comment_free_lines=3,
        comment_free_chars=85,
        executable_lines=2,
        executable_chars=39,
        lexical_chars=35,
        gsplot_calls=0,
    )


def test_docstring_mask_preserves_code_on_the_same_line(tmp_path: Path) -> None:
    """Only a true docstring token is excluded from executable measurements."""

    source = tmp_path / "inline.py"
    source.write_text('"""Documentation."""; value = 1\n', encoding="utf-8")

    metrics = measure(source)

    assert metrics.comment_free_lines == 1
    assert metrics.executable_lines == 1
    assert metrics.lexical_chars == len(";value=1")


def test_metrics_accept_standard_input(monkeypatch: pytest.MonkeyPatch) -> None:
    """Historical tagged source can be measured without a temporary file."""

    monkeypatch.setattr(sys, "stdin", io.StringIO("value = 1\n"))

    assert measure(Path("-")).executable_lines == 1


def test_selected_prototype_reproduces_frozen_metrics() -> None:
    """The accepted native-tuple design fixture retains its reviewed budget."""

    manifest = load_manifest(MANIFEST_PATH)
    metrics = measure(PROTOTYPE_PATH)

    assert (
        compare_expected(metrics, manifest["baselines"]["selected_tuple_prototype"])
        == []
    )
    assert (
        check_budgets(
            metrics,
            manifest["budgets"],
            manifest["baselines"]["issue_181_repair"],
        )
        == []
    )


def test_metrics_cli_reports_failures_without_executing_source(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CLI baseline checking returns a non-zero result for changed source."""

    source = tmp_path / "changed.py"
    source.write_text("import gsplot as gs\ngs.line(None, [], [])\n", encoding="utf-8")

    result = main(
        [
            str(source),
            "--manifest",
            str(MANIFEST_PATH),
            "--expect",
            "selected_tuple_prototype",
        ]
    )

    assert result == 1
    assert "error: physical_lines" in capsys.readouterr().out


def test_publication_style_fixture_is_complete_and_versioned() -> None:
    """The first paper implementation must agree with one finite golden table."""

    profile = json.loads(STYLE_PATH.read_text(encoding="utf-8"))

    assert set(profile) == {
        "axes",
        "figure",
        "legend",
        "paper_cycle_rgba",
        "schema_version",
        "series",
        "spines",
        "ticks",
        "typography",
    }
    assert profile["schema_version"] == 1
    assert len(profile["paper_cycle_rgba"]) == 5
    assert len(profile["series"]["colors_rgba"]) == 10
    assert len(profile["series"]["line_styles"]) == 10
    assert profile["series"]["markers"] == [
        "o",
        "s",
        "^",
        "D",
        "v",
        "P",
        "X",
        "<",
        ">",
        "*",
    ]
    assert profile["ticks"] == {
        "bottom": True,
        "direction": "in",
        "left": True,
        "major_length_pt": 3.5,
        "major_pad_pt": 6.0,
        "major_width_pt": 0.8,
        "minor_length_pt": 2.0,
        "minor_ticks": True,
        "minor_width_pt": 0.6,
        "right": True,
        "top": True,
    }
