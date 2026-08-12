"""Integration tests for the isolated documentation site builder."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tools.maintenance.docs_site.catalog import (
    ReleaseCatalog,
    ReleaseRecord,
    write_catalog,
)
from tools.maintenance.docs_site.orchestrator import (
    BuildError,
    _sanitize_and_validate_output,
    build_site,
)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _repository(
    tmp_path: Path, *, include_static: bool = True
) -> tuple[Path, str, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "tests@example.invalid")
    _git(repo, "config", "user.name", "gsplot tests")
    static_config = (
        "html_static_path = ['_static']\n"
        if include_static
        else "raise RuntimeError('intentional fixture build failure')\n"
    )
    _write(
        repo / "docs/conf.py",
        "project = 'fixture'\n" "extensions = ['myst_parser']\n" + static_config,
    )
    _write(repo / "docs/index.md", "# Fixture documentation\n")
    if include_static:
        _write(repo / "docs/_static/site.css", "body { color: black; }\n")
    _write(repo / "src/gsplot/__init__.py", "__version__ = '0.3.0'\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "fixture release")
    release_commit = _git(repo, "rev-parse", "HEAD")
    _git(repo, "tag", "v0.3.0")
    _write(repo / "src/gsplot/__init__.py", "__version__ = '0.4.0'\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "fixture main")
    main_commit = _git(repo, "rev-parse", "HEAD")
    return repo, main_commit, release_commit


def _catalog(path: Path, main_commit: str, release_commit: str) -> None:
    write_catalog(
        ReleaseCatalog(
            main_commit=main_commit,
            stable_tag="v0.3.0",
            releases=(
                ReleaseRecord(
                    tag="v0.3.0",
                    version="0.3.0",
                    commit=release_commit,
                    published_at="2026-08-11T00:00:00Z",
                    url="https://github.com/SoichiroYamane/gsplot/releases/tag/v0.3.0",
                ),
            ),
        ),
        path,
    )


def test_build_site_records_provenance_and_stable_alias(tmp_path: Path) -> None:
    repo, main_commit, release_commit = _repository(tmp_path)
    catalog_path = tmp_path / "catalog.json"
    output = tmp_path / "site"
    _catalog(catalog_path, main_commit, release_commit)

    manifest = build_site(catalog_path, output, repo_root=repo)

    assert (output / "dev/index.html").is_file()
    assert (output / "v0.3.0/index.html").is_file()
    assert (output / "stable/index.html").is_file()
    assert (output / "_meta/catalog.json").is_file()
    assert (output / "_meta/build-manifest.json").is_file()
    assert not list(output.rglob("*.buildinfo"))
    assert not list(output.rglob("create_switcher.py"))
    assert [record.channel for record in manifest.builds] == [
        "dev",
        "release",
        "stable",
    ]
    assert manifest.builds[0].source_commit == main_commit
    assert manifest.builds[1].source_commit == release_commit
    assert manifest.builds[1].package_version == "0.3.0"
    assert manifest.builds[1].package_source == "src/gsplot"
    assert manifest.file_count == sum(1 for item in output.rglob("*") if item.is_file())
    assert manifest.uncompressed_bytes == sum(
        item.stat().st_size for item in output.rglob("*") if item.is_file()
    )
    public_manifest = json.loads(
        (output / "_meta/build-manifest.json").read_text(encoding="utf-8")
    )
    assert public_manifest["stable_tag"] == "v0.3.0"
    assert all(
        not Path(value).is_absolute()
        for record in public_manifest["builds"]
        for value in record.values()
        if isinstance(value, str) and "path" in record
    )


def test_build_site_is_idempotent_and_replaces_stale_output(tmp_path: Path) -> None:
    repo, main_commit, release_commit = _repository(tmp_path)
    catalog_path = tmp_path / "catalog.json"
    output = tmp_path / "site"
    _catalog(catalog_path, main_commit, release_commit)

    first = build_site(catalog_path, output, repo_root=repo)
    (output / "stale.txt").write_text("must disappear", encoding="utf-8")
    second = build_site(catalog_path, output, repo_root=repo)

    assert first.to_mapping() == second.to_mapping()
    assert not (output / "stale.txt").exists()


def test_build_site_cleans_failed_worktree_and_does_not_publish_partial_site(
    tmp_path: Path,
) -> None:
    repo, main_commit, release_commit = _repository(tmp_path, include_static=False)
    catalog_path = tmp_path / "catalog.json"
    output = tmp_path / "site"
    _catalog(catalog_path, main_commit, release_commit)

    with pytest.raises(BuildError, match="command returned"):
        build_site(catalog_path, output, repo_root=repo)

    assert not output.exists()
    worktrees = _git(repo, "worktree", "list", "--porcelain")
    assert worktrees.count("worktree ") == 1


def test_build_site_rejects_repository_output_target(tmp_path: Path) -> None:
    repo, main_commit, release_commit = _repository(tmp_path)
    catalog_path = tmp_path / "catalog.json"
    _catalog(catalog_path, main_commit, release_commit)

    with pytest.raises(BuildError, match="outside the repository"):
        build_site(catalog_path, repo / "site", repo_root=repo)


def test_output_validation_rejects_missing_static_assets(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.mkdir()
    (output / "index.html").write_text("<html></html>\n", encoding="utf-8")

    with pytest.raises(BuildError, match="required static assets"):
        _sanitize_and_validate_output(
            output,
            "v0.3.0",
            "v0.3.0",
            "python -m sphinx -W -b html docs <output>",
        )
