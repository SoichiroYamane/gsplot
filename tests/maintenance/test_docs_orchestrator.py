"""Integration tests for the isolated documentation site builder."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tools.maintenance.docs_site.catalog import (
    ReleaseCatalog,
    ReleaseRecord,
    load_catalog,
    write_catalog,
)
from tools.maintenance.docs_site.orchestrator import (
    BuildError,
    _isolated_environment,
    _sanitize_and_validate_output,
    _strip_legacy_runtime_references,
    build_site,
)
from tools.maintenance.docs_site.switcher import load_switcher, validate_switcher


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
        "project = 'fixture'\n"
        "extensions = ['myst_parser', 'sphinxext.opengraph']\n"
        "html_theme = 'pydata_sphinx_theme'\n" + static_config,
    )
    _write(
        repo / "docs/index.md",
        "# Fixture documentation\n\n"
        "```{image} _images/SC_cal.png\n"
        ":alt: Fixture compatibility image\n"
        "```\n\n"
        "```{toctree}\n"
        ":maxdepth: 1\n\n"
        "api_reference/index\n"
        "```\n",
    )
    _write(repo / "docs/api_reference/index.md", "# Fixture API\n")
    if include_static:
        _write(repo / "docs/_images/SC_cal.png", "fixture image\n")
        _write(repo / "docs/_static/site.css", "body { color: black; }\n")
        _write(repo / "docs/_static/logo_gsplot.svg", "<svg></svg>\n")
        _write(repo / "docs/_static/logo/logo_title_gsplot.png", "fixture logo\n")
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
    release_index = (output / "v0.3.0/index.html").read_text(encoding="utf-8")
    assert (
        '<meta property="og:image" content="https://soichiroyamane.github.io/gsplot/v0.3.0/'
        '_static/logo/logo_title_gsplot.png" />'
    ) in release_index
    assert (
        '<meta property="og:image:alt" content="gsplot documentation page preview"'
        in (release_index)
    )
    assert (output / "stable/index.html").read_text(encoding="utf-8") == release_index
    dev_index = (output / "dev/index.html").read_text(encoding="utf-8")
    assert '<meta name="robots" content="noindex, follow" />' in dev_index
    assert "gsplot dev documentation" in dev_index
    root_entry = (output / "index.html").read_text(encoding="utf-8")
    assert 'http-equiv="refresh"' in root_entry
    assert "/gsplot/stable/" in root_entry
    assert (output / "404.html").is_file()
    assert (output / "robots.txt").read_text(encoding="utf-8").count("Sitemap:") == 1
    sitemap = (output / "sitemap.xml").read_text(encoding="utf-8")
    assert "/v0.3.0/index.html" in sitemap
    assert "/stable/" not in sitemap
    assert "/dev/" not in sitemap
    redirect = (output / "genindex.html").read_text(encoding="utf-8")
    assert 'http-equiv="refresh"' in redirect
    assert "/gsplot/dev/genindex.html" in redirect
    api_redirect = (output / "api_reference/index.html").read_text(encoding="utf-8")
    assert "/gsplot/dev/api_reference/index.html" in api_redirect
    assert (output / "_meta/catalog.json").is_file()
    assert (output / "_meta/switcher.json").is_file()
    assert (output / "_meta/build-manifest.json").is_file()
    assert (output / "_sources/index.md.txt").is_file()
    assert (output / "_images/SC_cal.png").is_file()
    assert not list(output.rglob("*.buildinfo"))
    assert not list(output.rglob("create_switcher.py"))
    legacy_tippy = output / "_static/tippy"
    assert [path.name for path in legacy_tippy.glob("*.js")] == [
        "index.e4541f43-c3c4-4f8e-910e-1cc2b87bf3db.js"
    ]
    assert not (output / "_static/webpack-macros.html").exists()
    assert not (output / "_static/tutorial").exists()
    assert not list(output.glob("v0.3.0/_sources"))
    assert not list(output.glob("v0.3.0/_modules"))
    assert not list(output.glob("v0.3.0/_static/tippy"))
    assert not any(
        "_sources/" in page.read_text(encoding="utf-8")
        for page in (output / "v0.3.0").rglob("*.html")
    )
    assert [record.channel for record in manifest.builds] == [
        "dev",
        "release",
        "stable",
    ]
    assert manifest.builds[0].source_commit == main_commit
    assert manifest.builds[1].source_commit == release_commit
    assert manifest.builds[1].package_version == "0.3.0"
    assert manifest.builds[1].package_source == "src/gsplot"
    assert manifest.file_count == sum(
        1
        for item in output.rglob("*")
        if item.is_file() and item.name != "build-manifest.json"
    )
    assert manifest.uncompressed_bytes == sum(
        item.stat().st_size
        for item in output.rglob("*")
        if item.is_file() and item.name != "build-manifest.json"
    )
    assert manifest.compressed_bytes > 0
    public_manifest = json.loads(
        (output / "_meta/build-manifest.json").read_text(encoding="utf-8")
    )
    assert public_manifest["stable_tag"] == "v0.3.0"
    assert public_manifest["artifact"]["compressed_bytes"] == (
        manifest.compressed_bytes
    )
    switcher = load_switcher(output / "_meta/switcher.json")
    validate_switcher(
        switcher,
        load_catalog(catalog_path),
    )
    assert isinstance(switcher[1]["url"], str)
    assert switcher[1]["url"].endswith("/stable/")
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


def test_runtime_sanitizer_keeps_html_structure_and_rejects_external_runtime(
    tmp_path: Path,
) -> None:
    output = tmp_path / "output"
    output.mkdir()
    (output / "_static").mkdir()
    (output / "_static/site.css").write_text("body {}\n", encoding="utf-8")
    page = output / "index.html"
    page.write_text(
        "<html><head>"
        '<script>DOCUMENTATION_OPTIONS.pagename = "index";</script>'
        '<link rel="canonical" href="https://example.test/index.html" />'
        "</head><body>"
        '<script defer src="_static/tippy/page.random.js"></script>'
        '<script>var togglebuttonSelector = ".toggle";</script>'
        "</body></html>\n",
        encoding="utf-8",
    )

    _strip_legacy_runtime_references(output)
    sanitized = page.read_text(encoding="utf-8")
    assert '<link rel="canonical"' in sanitized
    assert "togglebutton" not in sanitized

    page.write_text(
        sanitized.replace(
            "</body>",
            '<script src="https://cdn.example.test/runtime.js"></script></body>',
        ),
        encoding="utf-8",
    )
    with pytest.raises(BuildError, match="external runtime resource"):
        _sanitize_and_validate_output(
            output,
            "v0.3.0",
            "v0.3.0",
            "python -m sphinx -W -b html docs <output>",
        )

    static_page = output / "_static/runtime.html"
    static_page.write_text(
        '<script src="https://cdn.example.test/runtime.js"></script>\n',
        encoding="utf-8",
    )
    page.write_text(sanitized, encoding="utf-8")
    with pytest.raises(BuildError, match="external runtime resource"):
        _sanitize_and_validate_output(
            output,
            "v0.3.0",
            "v0.3.0",
            "python -m sphinx -W -b html docs <output>",
        )


def test_isolated_environment_removes_credentials_and_private_indexes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    package_path = worktree / "src"
    package_path.mkdir()
    environment_root = tmp_path / "environment"
    monkeypatch.setenv("GITHUB_TOKEN", "must-not-pass")
    monkeypatch.setenv("PIP_INDEX_URL", "https://private.example.test/simple")
    monkeypatch.setenv("PIP_CONFIG_FILE", "/private/pip.conf")
    monkeypatch.setenv("PYTHONPATH", "/private/pythonpath")

    environment = _isolated_environment(
        worktree=worktree,
        package_path=package_path,
        environment_root=environment_root,
        docs_version="dev",
        source_commit="a" * 40,
        site_base_url="https://docs.example.test/gsplot",
    )

    assert "GITHUB_TOKEN" not in environment
    assert "PIP_INDEX_URL" not in environment
    assert "PIP_CONFIG_FILE" not in environment
    assert environment["PYTHONPATH"] == str(package_path)
    assert environment["GSPLOT_DOCS_BASE_URL"] == "https://docs.example.test/gsplot"
