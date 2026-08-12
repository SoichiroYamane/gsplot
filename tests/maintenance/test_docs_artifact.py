"""Tests for the documentation artifact size budget."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.maintenance.check_docs_artifact import ArtifactBudgetError, check_budget

ARTIFACT = {
    "file_count": 100,
    "uncompressed_bytes": 10_000,
    "compressed_bytes": 5_000,
}


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def test_artifact_budget_accepts_growth_at_or_below_twenty_percent(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "manifest.json"
    baseline = tmp_path / "baseline.json"
    _write(manifest, {"status": "success", "artifact": ARTIFACT})
    _write(
        baseline,
        {
            "schema_version": 1,
            "artifact": {
                "file_count": 84,
                "uncompressed_bytes": 8_334,
                "compressed_bytes": 4_167,
            },
            "issue_url": "https://github.com/SoichiroYamane/gsplot/issues/174",
            "source_commit": "a" * 40,
        },
    )

    assert check_budget(manifest, baseline) == ARTIFACT


def test_artifact_budget_rejects_growth_over_twenty_percent(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    baseline = tmp_path / "baseline.json"
    _write(manifest, {"status": "success", "artifact": ARTIFACT})
    _write(
        baseline,
        {
            "schema_version": 1,
            "artifact": {
                "file_count": 80,
                "uncompressed_bytes": 8_000,
                "compressed_bytes": 4_000,
            },
            "issue_url": "https://github.com/SoichiroYamane/gsplot/issues/174",
            "source_commit": "a" * 40,
        },
    )

    with pytest.raises(ArtifactBudgetError, match="20% budget"):
        check_budget(manifest, baseline)
