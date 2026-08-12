"""Check the published documentation artifact against its size budget."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class ArtifactBudgetError(ValueError):
    """Raised when a documentation artifact exceeds its reviewed budget."""


_ARTIFACT_KEYS = {"file_count", "uncompressed_bytes", "compressed_bytes"}
_BASELINE_KEYS = {"schema_version", "artifact", "issue_url", "source_commit"}


def _load_json(path: Path, description: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactBudgetError(f"{description} could not be read") from exc
    if not isinstance(value, Mapping):
        raise ArtifactBudgetError(f"{description} must contain an object")
    return value


def _artifact(value: Mapping[str, Any], description: str) -> dict[str, int]:
    if not isinstance(value, Mapping):
        raise ArtifactBudgetError(f"{description} must contain an object")
    if set(value) != _ARTIFACT_KEYS:
        raise ArtifactBudgetError(f"{description} has an invalid schema")
    result: dict[str, int] = {}
    for key in sorted(_ARTIFACT_KEYS):
        item = value[key]
        if type(item) is not int or item < 1:
            raise ArtifactBudgetError(f"{description}.{key} must be positive")
        result[key] = item
    return result


def load_baseline(path: Path) -> dict[str, int]:
    """Load the reviewed public artifact baseline."""

    value = _load_json(path, "artifact baseline")
    if set(value) != _BASELINE_KEYS:
        raise ArtifactBudgetError("artifact baseline has an invalid schema")
    if value["schema_version"] != 1:
        raise ArtifactBudgetError("unsupported artifact baseline schema")
    source_commit = value["source_commit"]
    issue_url = value["issue_url"]
    if not isinstance(source_commit, str) or not source_commit:
        raise ArtifactBudgetError("artifact baseline source_commit is invalid")
    if not isinstance(issue_url, str) or not issue_url.startswith("https://"):
        raise ArtifactBudgetError("artifact baseline issue_url is invalid")
    return _artifact(value["artifact"], "artifact baseline artifact")


def check_budget(manifest_path: Path, baseline_path: Path) -> dict[str, int]:
    """Fail when any artifact metric grows by more than twenty percent."""

    manifest = _load_json(manifest_path, "build manifest")
    if manifest.get("status") != "success":
        raise ArtifactBudgetError("build manifest is not successful")
    current = _artifact(manifest.get("artifact", {}), "build manifest artifact")
    baseline = load_baseline(baseline_path)
    exceeded = [
        key
        for key in sorted(_ARTIFACT_KEYS)
        if current[key] * 100 > baseline[key] * 120
    ]
    if exceeded:
        details = ", ".join(
            f"{key}={current[key]} (baseline={baseline[key]})" for key in exceeded
        )
        raise ArtifactBudgetError(
            "documentation artifact exceeds the reviewed 20% budget: " + details
        )
    return current


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check a versioned documentation artifact size budget."
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the artifact budget check and print a public-safe result."""

    args = _parser().parse_args(argv)
    try:
        artifact = check_budget(args.manifest, args.baseline)
    except ArtifactBudgetError as exc:
        print(f"documentation artifact budget failed: {exc}", file=sys.stderr)
        return 1
    print(
        "documentation artifact budget passed: "
        + ", ".join(f"{key}={artifact[key]}" for key in sorted(artifact))
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
