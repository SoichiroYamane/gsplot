"""Tests for the revision-pair reform benchmark."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.maintenance import benchmark_reform as benchmark


@pytest.mark.parametrize(
    ("baseline", "candidate", "absolute", "material"),
    [
        (100.0, 114.0, 10.0, False),
        (100.0, 116.0, 20.0, False),
        (100.0, 116.0, 10.0, True),
        (100.0, 115.0, 10.0, False),
        (100.0, 90.0, 1.0, False),
    ],
)
def test_material_regression_requires_both_thresholds(
    baseline: float,
    candidate: float,
    absolute: float,
    material: bool,
) -> None:
    """Noise and improvements cannot fail the relative performance gate."""

    result = benchmark.compare_metric(baseline, candidate, absolute)

    assert result["material_regression"] is material
    assert result["relative_threshold_percent"] == 15.0
    assert result["absolute_threshold_ms"] == absolute


@pytest.mark.parametrize(
    ("baseline", "candidate", "absolute"),
    [
        (0.0, 1.0, 1.0),
        (-1.0, 1.0, 1.0),
        (1.0, -1.0, 1.0),
        (1.0, 1.0, -1.0),
        (1.0, float("inf"), 1.0),
    ],
)
def test_metric_comparison_rejects_invalid_values(
    baseline: float, candidate: float, absolute: float
) -> None:
    """Malformed timing data cannot silently become an acceptance result."""

    with pytest.raises(ValueError, match="finite and valid"):
        benchmark.compare_metric(baseline, candidate, absolute)


@pytest.mark.parametrize(
    "name",
    ["/absolute", "../escape", "nested/../escape", "nested\\escape", "", "a\x00b"],
)
def test_archive_member_validation_rejects_unsafe_paths(name: str) -> None:
    """Exported revisions cannot escape their temporary extraction root."""

    with pytest.raises(benchmark.BenchmarkError, match="unsafe member"):
        benchmark._safe_archive_name(name)


def test_sanitized_environment_drops_credentials_and_python_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Revision code receives only the small reviewed process environment."""

    monkeypatch.setenv("PYTHONPATH", "/untrusted")
    monkeypatch.setenv("GITHUB_TOKEN", "not-a-real-token")
    monkeypatch.setenv("PATH", "/usr/bin")

    result = benchmark._sanitized_environment(tmp_path)

    assert result["PATH"] == "/usr/bin"
    assert "PYTHONPATH" not in result
    assert "GITHUB_TOKEN" not in result
    assert result["MPLBACKEND"] == "Agg"
    assert result["GSPLOT_DOCS_VERSION"] == "dev"


def test_public_result_contains_no_temporary_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The serialized record contains commits and aggregates, not local paths."""

    monkeypatch.setattr(benchmark, "_require_clean_tracked_tree", lambda: None)
    commits = {"base": "a" * 40, "tip": "b" * 40}
    monkeypatch.setattr(benchmark, "_resolve_commit", commits.__getitem__)
    monkeypatch.setattr(
        benchmark,
        "_prepare_revision",
        lambda root, *, label, ref, commit: benchmark.RevisionEnvironment(
            label, ref, commit, root / label / "private-source", Path("python")
        ),
    )
    comparisons = {
        name: benchmark.compare_metric(100.0, 101.0, threshold)
        for name, threshold in benchmark.ABSOLUTE_THRESHOLDS_MS.items()
    }
    monkeypatch.setattr(
        benchmark,
        "_measure",
        lambda *args: (
            comparisons,
            {
                "backend": "Agg",
                "implementation": "CPython",
                "machine": "x86_64",
                "matplotlib": "3.10.0",
                "numpy": "2.0.0",
                "platform": "Linux",
                "python": "3.12.0",
            },
        ),
    )

    result = benchmark.run_benchmark("base", "tip")
    serialized = json.dumps(result, sort_keys=True)

    assert result["status"] == "pass"
    assert result["material_regressions"] == []
    assert "private-source" not in serialized
    assert set(result["revisions"]) == {"baseline", "candidate"}
    assert result["protocol"] == {
        "docs_builds": 3,
        "fresh_import_iterations": 20,
        "plot_iterations": 10,
        "plot_warmups": 1,
    }
