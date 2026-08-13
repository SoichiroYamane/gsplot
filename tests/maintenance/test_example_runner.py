"""Tests for the isolated executable-example contract."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from tools.maintenance.example_runner import (
    ExampleError,
    _isolated_environment,
    load_manifest,
    run_examples,
)


def _project(
    root: Path,
    *,
    script: str = "from pathlib import Path\nPath('figure.png').write_text('new')\n",
    output: str = "examples/plotting/figure.png",
) -> Path:
    source = root / "examples/plotting/example.py"
    page = root / "docs/guides/examples/example.md"
    source.parent.mkdir(parents=True)
    page.parent.mkdir(parents=True)
    source.write_text(script, encoding="utf-8")
    relative_output = "../../../" + output
    page.write_text(
        "# Example\n\n"
        "```{literalinclude} ../../../examples/plotting/example.py\n"
        "```\n\n"
        f"```{{image}} {relative_output}\n```\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": 1,
        "examples": [
            {
                "id": "plotting-example",
                "script": "examples/plotting/example.py",
                "page": "docs/guides/examples/example.md",
                "outputs": [output],
            }
        ],
    }
    (root / "examples/manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return root


def test_manifest_and_runner_require_fresh_declared_outputs(tmp_path: Path) -> None:
    root = _project(tmp_path)

    examples = run_examples(root, announce=lambda _: None)

    assert [example.identifier for example in examples] == ["plotting-example"]
    assert (root / "examples/plotting/figure.png").read_text() == "new"


def test_runner_rejects_stale_and_unexpected_files(tmp_path: Path) -> None:
    root = _project(tmp_path, script="pass\n")
    output = root / "examples/plotting/figure.png"
    output.write_text("old", encoding="utf-8")
    with pytest.raises(ExampleError, match="left required output"):
        run_examples(root, announce=lambda _: None)

    root = _project(
        tmp_path / "unexpected",
        script=(
            "from pathlib import Path\n"
            "Path('figure.png').write_text('new')\n"
            "Path('unexpected.txt').write_text('unexpected')\n"
        ),
    )
    with pytest.raises(ExampleError, match="outside its output allowlist"):
        run_examples(root, announce=lambda _: None)


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("script", "../private.py", "stay under examples"),
        ("script", "examples\\private.py", "normalized non-empty POSIX"),
        ("page", "docs/other.md", "docs/guides/examples"),
    ],
)
def test_manifest_rejects_unsafe_paths(
    tmp_path: Path, field: str, value: str, match: str
) -> None:
    root = _project(tmp_path)
    manifest_path = root / "examples/manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["examples"][0][field] = value
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ExampleError, match=match):
        load_manifest(root)


def test_manifest_rejects_undocumented_outputs_and_scripts(tmp_path: Path) -> None:
    root = _project(tmp_path)
    page = root / "docs/guides/examples/example.md"
    page.write_text(
        "```{literalinclude} ../../../examples/plotting/example.py\n```\n",
        encoding="utf-8",
    )
    with pytest.raises(ExampleError, match="must reference"):
        load_manifest(root)

    page.write_text(
        "```{literalinclude} ../../../examples/plotting/example.py\n```\n"
        "```{image} ../../../examples/plotting/figure.png\n```\n",
        encoding="utf-8",
    )
    (root / "examples/plotting/other.py").write_text("pass\n", encoding="utf-8")
    with pytest.raises(ExampleError, match="does not match executable scripts"):
        load_manifest(root)


def test_manifest_rejects_an_output_symlink_outside_examples(tmp_path: Path) -> None:
    root = _project(tmp_path)
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"not an example output")
    (root / "examples/plotting/figure.png").symlink_to(outside)

    with pytest.raises(ExampleError, match="resolves outside examples"):
        load_manifest(root)


def test_isolated_environment_scrubs_credentials_and_indexes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "not-public")
    monkeypatch.setenv("PIP_INDEX_URL", "https://user:password@example.test")
    monkeypatch.setenv("PYTHONPATH", "/untrusted")
    monkeypatch.setenv("UNRELATED_SETTING", "not inherited")

    environment = _isolated_environment(tmp_path)

    assert "UNRELATED_SETTING" not in environment
    assert environment["MPLBACKEND"] == "Agg"
    assert environment["HOME"] == str(tmp_path / "home")
    assert "GITHUB_TOKEN" not in environment
    assert "PIP_INDEX_URL" not in environment
    assert "PYTHONPATH" not in environment
    assert os.path.isdir(environment["MPLCONFIGDIR"])
