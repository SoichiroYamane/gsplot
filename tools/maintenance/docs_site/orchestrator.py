"""Isolated, provenance-aware documentation site build orchestration.

The orchestrator consumes a validated release catalog and builds every site
channel in temporary Git worktrees. It intentionally uses the current pinned
documentation toolchain with an explicit source path for each package instead
of installing untrusted release code into the maintainer environment.
"""

from __future__ import annotations

import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from .catalog import ReleaseCatalog, ReleaseRecord, load_catalog
from .site import SiteError, finalize_site
from .switcher import (
    DEFAULT_BASE_URL,
    generate_switcher,
    normalize_base_url,
    write_switcher,
)

BUILD_MANIFEST_SCHEMA_VERSION = 2
_ALLOWED_OUTPUT_DIRECTORIES = {
    "_downloads",
    "_images",
    "_modules",
    "_sources",
    "_sphinx_design_static",
    "_static",
    "api_reference",
    "demo",
    "guides",
    "project",
    "reference",
    "tutorial",
}
_TRANSIENT_OUTPUT_NAMES = {
    ".buildinfo",
    ".doctrees",
    "create_switcher.py",
    "tippy_doi_cache.json",
    "tippy_rtd_cache.json",
    "tippy_wiki_cache.json",
}
_SENSITIVE_ENV_MARKERS = (
    "CREDENTIAL",
    "PASSWORD",
    "SECRET",
    "TOKEN",
    "OIDC",
    "PYPI_API",
    "ACCESS_KEY",
    "PRIVATE_KEY",
    "SSH_AUTH",
    "AWS_",
    "AZURE_",
    "GOOGLE_APPLICATION_CREDENTIALS",
)
_UNTRUSTED_ENV_NAMES = {
    "GIT_CONFIG_GLOBAL",
    "GIT_CONFIG_SYSTEM",
    "NETRC",
    "PIP_CERT",
    "PIP_CLIENT_CERT",
    "PIP_CONFIG_FILE",
    "PIP_EXTRA_INDEX_URL",
    "PIP_INDEX_URL",
    "PIP_PROXY",
    "PIP_TRUSTED_HOST",
    "SSH_AUTH_SOCK",
    "UV_EXTRA_INDEX_URL",
    "UV_INDEX",
    "UV_INDEX_URL",
    "NODE_OPTIONS",
    "NODE_PATH",
    "NPM_CONFIG_GLOBALCONFIG",
    "NPM_CONFIG_USERCONFIG",
    "NPM_CONFIG_REGISTRY",
}
_CURRENT_SPHINX_EXTENSIONS = (
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "myst_parser",
    "sphinx_copybutton",
    "sphinxext.opengraph",
)
# Published v0.1.1-v0.3.0 pages declare these extensions and the pre-cutover
# root asset inventory includes their generated theme files.  They are kept in
# the historical compatibility profile until the final deployment workflow can
# retire those root assets explicitly.
_HISTORICAL_SPHINX_EXTENSIONS = _CURRENT_SPHINX_EXTENSIONS + (
    "sphinxcontrib.mermaid",
    "sphinx_design",
    "sphinx_pyscript",
    "sphinx_tippy",
    "sphinx_togglebutton",
)
_LEGACY_RUNTIME_TAG = re.compile(
    r"\s*<script\b[^>]*(?:tippy|togglebutton|design-tabs|unpkg\.com)"
    r"[^>]*>.*?</script>\s*",
    re.IGNORECASE | re.DOTALL,
)
_LEGACY_RUNTIME_BODY_TAG = re.compile(
    r"\s*<script\b[^>]*>(?:(?!</script>).)*"
    r"(?:tippy|togglebutton|design-tabs|unpkg\.com|jsdelivr\.net|mermaid)"
    r"(?:(?!</script>).)*</script>\s*",
    re.IGNORECASE | re.DOTALL,
)
_LEGACY_RUNTIME_LINK = re.compile(
    r"\s*<link\b[^>]*(?:togglebutton|sphinx-design)[^>]*/?>\s*",
    re.IGNORECASE,
)
_EXTERNAL_RUNTIME_RESOURCE = re.compile(
    r"<script\b[^>]*\bsrc\s*=\s*['\"]https?://"
    r"|<script\b[^>]*>(?:(?!</script>).)*"
    r"(?:unpkg\.com|jsdelivr\.net|cdnjs\.cloudflare\.com)"
    r"(?:(?!</script>).)*</script>"
    r"|<link\b(?=[^>]*\brel\s*=\s*['\"](?:stylesheet|preload|modulepreload))"
    r"[^>]*\bhref\s*=\s*['\"]https?://",
    re.IGNORECASE,
)
_CANONICAL_LINK = re.compile(r'<link\s+rel="canonical"\s+href="([^"]+)"', re.IGNORECASE)
_META_VALUE = re.compile(
    r'<meta\s+property="([^"]+)"\s+content="([^"]*)"\s*/?>',
    re.IGNORECASE,
)
_META_NAME_VALUE = re.compile(
    r'<meta\s+name="([^"]+)"\s+content="([^"]*)"\s*/?>', re.IGNORECASE
)
_OG_IMAGE_ALT = re.compile(
    r'(<meta\s+property="og:image:alt"\s+content=")[^"]*("\s*/?>)',
    re.IGNORECASE,
)
_TITLE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_NON_INDEXABLE_PAGES = {"genindex.html", "py-modindex.html", "search.html"}


class BuildError(RuntimeError):
    """A safe, structured documentation build failure."""

    def __init__(self, version: str, ref: str, command: str, reason: str) -> None:
        self.version = version
        self.ref = ref
        self.command = command
        self.reason = reason
        super().__init__(self.__str__())

    def __str__(self) -> str:
        """Return only public identifiers and a safe reason."""

        return (
            f"documentation build failed for {self.version} at {self.ref}: "
            f"{self.reason}; command={self.command}"
        )


@dataclass(frozen=True, slots=True)
class BuildRecord:
    """Provenance and validation results for one published site directory."""

    channel: str
    source_ref: str
    source_commit: str
    package_ref: str
    package_version: str
    package_source: str
    docs_version: str
    output_path: str
    checks: tuple[str, ...]

    def to_mapping(self) -> dict[str, Any]:
        """Return the public-safe manifest representation."""

        return {
            "channel": self.channel,
            "source_ref": self.source_ref,
            "source_commit": self.source_commit,
            "package_ref": self.package_ref,
            "package_version": self.package_version,
            "package_source": self.package_source,
            "docs_version": self.docs_version,
            "output_path": self.output_path,
            "checks": list(self.checks),
        }


@dataclass(frozen=True, slots=True)
class BuildManifest:
    """Machine-readable result for one complete documentation site build."""

    main_commit: str
    stable_tag: str
    builds: tuple[BuildRecord, ...]
    exclusions: tuple[Mapping[str, Any], ...]
    file_count: int
    uncompressed_bytes: int
    compressed_bytes: int
    warnings: tuple[str, ...] = ()
    schema_version: int = BUILD_MANIFEST_SCHEMA_VERSION
    status: str = "success"

    def __post_init__(self) -> None:
        """Validate manifest invariants before it can be published."""

        if self.schema_version != BUILD_MANIFEST_SCHEMA_VERSION:
            raise BuildError("site", "manifest", "manifest", "unsupported schema")
        if self.status != "success":
            raise BuildError("site", "manifest", "manifest", "status is not success")
        if not self.builds:
            raise BuildError("site", "manifest", "manifest", "no build records")
        if (
            self.file_count < 1
            or self.uncompressed_bytes < 1
            or self.compressed_bytes < 1
        ):
            raise BuildError("site", "manifest", "manifest", "empty artifact")
        stable_records = [item for item in self.builds if item.channel == "stable"]
        if len(stable_records) != 1:
            raise BuildError(
                "site", "manifest", "manifest", "manifest must contain one stable alias"
            )

    def to_mapping(self) -> dict[str, Any]:
        """Return the deterministic public manifest mapping."""

        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "main_commit": self.main_commit,
            "stable_tag": self.stable_tag,
            "builds": [item.to_mapping() for item in self.builds],
            "exclusions": [dict(item) for item in self.exclusions],
            "warnings": list(self.warnings),
            "artifact": {
                "file_count": self.file_count,
                "uncompressed_bytes": self.uncompressed_bytes,
                "compressed_bytes": self.compressed_bytes,
            },
        }


def build_site(
    catalog_path: Path,
    output_dir: Path,
    *,
    repo_root: Path = Path("."),
    python_executable: str | Path = sys.executable,
    base_url: str = DEFAULT_BASE_URL,
) -> BuildManifest:
    """Build ``dev``, every immutable release, and the stable alias.

    The output is promoted only after all version builds and validation checks
    succeed. Existing output is replaced by an empty directory at the start;
    the path must be outside the source repository to make this operation
    narrowly scoped and recoverable by the caller.
    """

    repo = repo_root.resolve()
    output = output_dir.resolve()
    _validate_output_target(repo, output)
    catalog = load_catalog(catalog_path.resolve())
    site_base_url = normalize_base_url(base_url)
    output.parent.mkdir(parents=True, exist_ok=True)
    _remove_output(output)

    temporary_root = _temporary_root(repo)
    with tempfile.TemporaryDirectory(
        prefix="gsplot-docs-build-", dir=temporary_root
    ) as temporary_name:
        temporary = Path(temporary_name)
        staging = Path(tempfile.mkdtemp(prefix="site-", dir=output.parent))
        promoted = False
        try:
            records: list[BuildRecord] = []
            dev_record = _build_channel(
                catalog=catalog,
                channel="dev",
                source_ref="main",
                source_commit=catalog.main_commit,
                docs_version="dev",
                output_dir=staging / "dev",
                repo_root=repo,
                temporary_root=temporary,
                python_executable=python_executable,
                site_base_url=site_base_url,
            )
            records.append(dev_record)
            release_records: dict[str, BuildRecord] = {}
            for release in catalog.releases:
                record = _build_channel(
                    catalog=catalog,
                    channel="release",
                    source_ref=release.tag,
                    source_commit=release.commit,
                    docs_version=release.version,
                    output_dir=staging / release.tag,
                    repo_root=repo,
                    temporary_root=temporary,
                    python_executable=python_executable,
                    release=release,
                    site_base_url=site_base_url,
                )
                records.append(record)
                release_records[release.tag] = record

            stable_source = staging / catalog.stable_tag
            if not stable_source.is_dir():
                raise BuildError(
                    catalog.stable_tag,
                    catalog.stable_tag,
                    "copy immutable release to stable",
                    "stable source output is missing",
                )
            shutil.copytree(stable_source, staging / "stable")
            stable_record = release_records[catalog.stable_tag]
            records.append(
                BuildRecord(
                    channel="stable",
                    source_ref=stable_record.source_ref,
                    source_commit=stable_record.source_commit,
                    package_ref=stable_record.package_ref,
                    package_version=stable_record.package_version,
                    package_source=stable_record.package_source,
                    docs_version=stable_record.docs_version,
                    output_path="stable/",
                    checks=stable_record.checks + ("stable-alias",),
                )
            )

            _write_json(staging / "_meta" / "catalog.json", catalog.to_mapping())
            write_switcher(
                generate_switcher(catalog, base_url=site_base_url),
                staging / "_meta" / "switcher.json",
            )
            try:
                finalize_site(staging, catalog, base_url=site_base_url)
            except SiteError as exc:
                raise BuildError(
                    "site",
                    "site",
                    "finalize static site",
                    str(exc),
                ) from exc
            except OSError as exc:
                raise BuildError(
                    "site",
                    "site",
                    "finalize static site",
                    "site finalization could not complete",
                ) from exc
            file_count, uncompressed_bytes, compressed_bytes = _artifact_stats(staging)
            manifest = BuildManifest(
                main_commit=catalog.main_commit,
                stable_tag=catalog.stable_tag,
                builds=tuple(records),
                exclusions=tuple(item.to_mapping() for item in catalog.exclusions),
                file_count=file_count,
                uncompressed_bytes=uncompressed_bytes,
                compressed_bytes=compressed_bytes,
                warnings=(),
            )
            for _ in range(5):
                _write_json(
                    staging / "_meta" / "build-manifest.json", manifest.to_mapping()
                )
                updated_stats = _artifact_stats(staging)
                if updated_stats == (
                    manifest.file_count,
                    manifest.uncompressed_bytes,
                    manifest.compressed_bytes,
                ):
                    break
                manifest = BuildManifest(
                    main_commit=catalog.main_commit,
                    stable_tag=catalog.stable_tag,
                    builds=tuple(records),
                    exclusions=tuple(item.to_mapping() for item in catalog.exclusions),
                    file_count=updated_stats[0],
                    uncompressed_bytes=updated_stats[1],
                    compressed_bytes=updated_stats[2],
                    warnings=(),
                )
            else:
                raise BuildError(
                    "site",
                    "manifest",
                    "write public manifest",
                    "artifact size did not stabilize",
                )
            _promote(staging, output)
            promoted = True
            return manifest
        finally:
            if not promoted:
                shutil.rmtree(staging, ignore_errors=True)


def _build_channel(
    *,
    catalog: ReleaseCatalog,
    channel: str,
    source_ref: str,
    source_commit: str,
    docs_version: str,
    output_dir: Path,
    repo_root: Path,
    temporary_root: Path,
    python_executable: str | Path,
    site_base_url: str,
    release: ReleaseRecord | None = None,
) -> BuildRecord:
    """Build and validate one source commit in a temporary worktree."""

    del catalog  # Reserved for future per-catalog build configuration.
    ref_for_error = source_ref
    command = "python -m sphinx -W -b html docs <output>"
    worktree_path = temporary_root / f"worktree-{channel}-{docs_version}"
    environment_root = temporary_root / f"environment-{channel}-{docs_version}"
    environment_root.mkdir(parents=True, exist_ok=False)
    with _GitWorktree(repo_root, worktree_path, source_commit, source_ref) as worktree:
        package_path, package_source = _package_import_path(worktree)
        environment = _isolated_environment(
            worktree=worktree,
            package_path=package_path,
            environment_root=environment_root,
            docs_version=docs_version,
            source_commit=source_commit,
            site_base_url=site_base_url,
        )
        package_version = _probe_package(
            python_executable,
            worktree,
            environment,
            docs_version,
            ref_for_error,
        )
        if release is not None and package_version != release.version:
            raise BuildError(
                docs_version,
                ref_for_error,
                command,
                "package version disagrees with catalog release",
            )
        output_dir.mkdir(parents=True, exist_ok=False)
        doctree_dir = environment_root / "doctrees"
        mermaid_config = None
        mermaid_puppeteer_config = None
        if release is not None:
            mermaid_config = environment_root / "mermaid-config.json"
            _write_json(mermaid_config, {"handDrawnSeed": 1})
            mermaid_puppeteer_config = environment_root / "puppeteer-config.json"
            _write_puppeteer_config(
                mermaid_puppeteer_config,
                environment.get("GSPLOT_MERMAID_CHROME_PATH"),
            )
        extensions = (
            _HISTORICAL_SPHINX_EXTENSIONS
            if release is not None
            else _CURRENT_SPHINX_EXTENSIONS
        )
        channel_name = "dev" if release is None else release.tag
        channel_base_url = f"{site_base_url}/{channel_name}/"
        theme_options = {
            "announcement": (
                "You are reading the development documentation (main)."
                if release is None
                else f"You are reading release {release.tag}."
            ),
            "check_switcher": False,
            "logo": {
                "text": "gsplot 📈",
                "image_light": "_static/logo/logo_gsplot.svg",
                "image_dark": "_static/logo/logo_gsplot.svg",
            },
            "pygments_light_style": "manni",
            "pygments_dark_style": "monokai",
            "navbar_start": ["navbar-logo"],
            "footer_start": ["copyright"],
            "footer_end": ["version-switcher"],
            "use_edit_page_button": True,
            "icon_links": [
                {
                    "name": "GitHub",
                    "url": "https://github.com/SoichiroYamane/gsplot",
                    "icon": "fa-brands fa-square-github",
                    "type": "fontawesome",
                }
            ],
            "switcher": {
                "version_match": "dev" if release is None else release.tag,
                "json_url": f"{site_base_url}/_meta/switcher.json",
            },
        }
        html_context = {
            "github_user": "SoichiroYamane",
            "github_repo": "gsplot",
            "github_version": source_ref,
            "doc_path": "docs",
            "default_mode": "dark",
            "gsplot_is_development": release is None,
        }
        _append_config_overrides(
            worktree / "docs" / "conf.py",
            version=docs_version,
            channel_base_url=channel_base_url,
            theme_options=theme_options,
            html_context=html_context,
            historical=release is not None,
            mermaid_config=mermaid_config,
            mermaid_puppeteer_config=mermaid_puppeteer_config,
        )
        _run_process(
            [
                str(python_executable),
                "-m",
                "sphinx.cmd.build",
                "-W",
                "-E",
                "-D",
                "extensions=" + ",".join(extensions),
                *(["-D", "mermaid_output_format=svg"] if release else []),
                "-b",
                "html",
                "-d",
                str(doctree_dir),
                str(worktree / "docs"),
                str(output_dir),
            ],
            cwd=worktree / "docs",
            env=environment,
            version=docs_version,
            ref=ref_for_error,
            command=command,
        )
        _sanitize_and_validate_output(
            output_dir,
            docs_version,
            ref_for_error,
            command,
            base_url=site_base_url,
            channel=channel_name,
        )

    return BuildRecord(
        channel=channel,
        source_ref=source_ref,
        source_commit=source_commit,
        package_ref=source_ref,
        package_version=package_version,
        package_source=package_source,
        docs_version=docs_version,
        output_path=f"{source_ref}/" if channel == "release" else "dev/",
        checks=("index", "static-assets", "package-provenance", "output-hygiene"),
    )


def _append_config_overrides(
    path: Path,
    *,
    version: str,
    channel_base_url: str,
    theme_options: Mapping[str, Any],
    html_context: Mapping[str, Any],
    historical: bool,
    mermaid_config: Path | None,
    mermaid_puppeteer_config: Path | None,
) -> None:
    """Append deterministic channel metadata to an isolated source config.

    Historical tags predate the versioned-site contract and cannot be edited
    in place.  The append-only overlay runs only in a detached temporary
    worktree, so it normalizes old configuration without changing release
    source or its public provenance.
    """

    original = path.read_text(encoding="utf-8")
    lines = [
        "",
        "# Generated by the gsplot documentation site orchestrator.",
        f"version = {version!r}",
        f"release = {version!r}",
        f"version_match = {('dev' if version == 'dev' else f'v{version}')!r}",
        f"html_title = {f'gsplot {version} documentation'!r}",
        f"html_baseurl = {channel_base_url!r}",
        f"ogp_site_url = {channel_base_url!r}",
        f"ogp_canonical_url = {channel_base_url!r}",
        "ogp_social_cards = {'enable': False}",
        "ogp_image = '_static/logo/logo_title_gsplot.png'",
        "ogp_image_alt = 'gsplot documentation page preview'",
        # The finalizer copies only the inventoried root source entry for
        # legacy URL compatibility, then removes channel source trees.
        "html_copy_source = True",
        "html_show_sourcelink = False",
        "intersphinx_mapping = {}",
        f"html_context = {dict(html_context)!r}",
    ]
    if "pydata_sphinx_theme" in original:
        lines.append(f"html_theme_options = {dict(theme_options)!r}")
    if historical:
        lines.extend(
            [
                f"mermaid_params = ['--configFile', {str(mermaid_config)!r}]",
                "mermaid_params += ["
                f"'--puppeteerConfigFile', {str(mermaid_puppeteer_config)!r}]",
                "tippy_js = []",
                "tippy_enable_wikitips = False",
                "tippy_enable_doitips = False",
            ]
        )
    path.write_text(
        original.rstrip() + "\n" + "\n".join(lines) + "\n",
        encoding="utf-8",
        errors="strict",
    )


def _write_puppeteer_config(path: Path, chrome_path: str | None) -> None:
    """Write a temporary Puppeteer policy for the build-only Mermaid CLI."""

    configuration: dict[str, Any] = {
        "args": ["--no-sandbox", "--disable-setuid-sandbox"],
    }
    if chrome_path:
        configuration["executablePath"] = chrome_path
    path.write_text(
        json.dumps(configuration, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class _GitWorktree:
    """Create and always remove one detached Git worktree."""

    def __init__(self, repo_root: Path, path: Path, commit: str, ref: str) -> None:
        self.repo_root = repo_root
        self.path = path
        self.commit = commit
        self.ref = ref

    def __enter__(self) -> Path:
        _run_process(
            ["git", "worktree", "add", "--detach", str(self.path), self.commit],
            cwd=self.repo_root,
            env=_git_environment(),
            version=self.ref,
            ref=self.commit,
            command="git worktree add <temporary-path> <commit>",
        )
        return self.path

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        cleanup_error: BuildError | None = None
        result = subprocess.run(
            ["git", "worktree", "remove", "--force", str(self.path)],
            cwd=self.repo_root,
            env=_git_environment(),
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            cleanup_error = BuildError(
                self.ref,
                self.commit,
                "git worktree remove <temporary-path>",
                "temporary worktree cleanup failed",
            )
        if self.path.exists():
            shutil.rmtree(self.path, ignore_errors=True)
        if self.path.exists() and cleanup_error is None:
            cleanup_error = BuildError(
                self.ref,
                self.commit,
                "remove temporary worktree",
                "temporary worktree cleanup failed",
            )
        if cleanup_error is not None and exc_type is None:
            raise cleanup_error


def _package_import_path(worktree: Path) -> tuple[Path, str]:
    """Find a historical package layout without importing current main."""

    src_package = worktree / "src" / "gsplot"
    root_package = worktree / "gsplot"
    if src_package.is_dir() and root_package.is_dir():
        raise BuildError(
            "site", "worktree", "package provenance", "ambiguous package layout"
        )
    if src_package.is_dir():
        return worktree / "src", "src/gsplot"
    if root_package.is_dir():
        return worktree, "gsplot"
    raise BuildError(
        "site", "worktree", "package provenance", "package source is missing"
    )


def _isolated_environment(
    *,
    worktree: Path,
    package_path: Path,
    environment_root: Path,
    docs_version: str,
    source_commit: str,
    site_base_url: str,
) -> dict[str, str]:
    """Build a clean subprocess environment with only the source package path."""

    environment = dict(os.environ)
    for name in list(environment):
        uppercase_name = name.upper()
        if uppercase_name in _UNTRUSTED_ENV_NAMES or any(
            marker in uppercase_name for marker in _SENSITIVE_ENV_MARKERS
        ):
            environment.pop(name, None)
    environment.pop("PYTHONPATH", None)
    home = environment_root / "home"
    environment.update(
        {
            "HOME": str(home),
            "MPLBACKEND": "Agg",
            "MPLCONFIGDIR": str(environment_root / "matplotlib"),
            "PYTHONNOUSERSITE": "1",
            "PYTHONPATH": str(package_path),
            "GSPLOT_BUILD_SOURCE_COMMIT": source_commit,
            "GSPLOT_DOCS_BASE_URL": site_base_url,
            "GSPLOT_DOCS_VERSION": docs_version,
            "XDG_CACHE_HOME": str(environment_root / "cache"),
            "XDG_CONFIG_HOME": str(environment_root / "config"),
            "XDG_DATA_HOME": str(environment_root / "data"),
        }
    )
    for directory in (home, Path(environment["MPLCONFIGDIR"])):
        directory.mkdir(parents=True, exist_ok=True)
    if not worktree.is_dir():
        raise BuildError(
            docs_version, source_commit, "prepare environment", "worktree missing"
        )
    return environment


def _probe_package(
    python_executable: str | Path,
    worktree: Path,
    environment: Mapping[str, str],
    version: str,
    ref: str,
) -> str:
    """Import the source-path package and verify its file location."""

    probe = (
        "import json, gsplot; "
        "print('GSPLOT_PROVENANCE=' + json.dumps({"
        "'file': getattr(gsplot, '__file__', None), "
        "'version': getattr(gsplot, '__version__', None)}, sort_keys=True))"
    )
    try:
        result = subprocess.run(
            [str(python_executable), "-c", probe],
            cwd=worktree,
            env=dict(environment),
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise BuildError(
            version, ref, "python package provenance probe", "probe could not start"
        ) from exc
    if result.returncode != 0:
        raise BuildError(
            version, ref, "python package provenance probe", "package import failed"
        )
    payload: dict[str, Any] | None = None
    for line in reversed(result.stdout.splitlines()):
        if line.startswith("GSPLOT_PROVENANCE="):
            try:
                candidate = json.loads(line.split("=", 1)[1])
            except json.JSONDecodeError as exc:
                raise BuildError(
                    version,
                    ref,
                    "python package provenance probe",
                    "probe returned invalid data",
                ) from exc
            if isinstance(candidate, dict):
                payload = candidate
            break
    if payload is None:
        raise BuildError(
            version, ref, "python package provenance probe", "probe returned no data"
        )
    package_file = payload.get("file")
    package_version = payload.get("version")
    if not isinstance(package_file, str) or not isinstance(package_version, str):
        raise BuildError(
            version,
            ref,
            "python package provenance probe",
            "package metadata is incomplete",
        )
    try:
        package_path = Path(package_file).resolve()
        package_path.relative_to(worktree.resolve())
    except (OSError, ValueError) as exc:
        raise BuildError(
            version,
            ref,
            "python package provenance probe",
            "package was imported outside its source worktree",
        ) from exc
    package_version = package_version.strip()
    if (
        not package_version
        or len(package_version) > 64
        or any(
            ord(character) < 32 or ord(character) > 126 for character in package_version
        )
    ):
        raise BuildError(
            version,
            ref,
            "python package provenance probe",
            "package version is not public-safe",
        )
    return package_version


def _run_process(
    args: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    version: str,
    ref: str,
    command: str,
) -> None:
    """Run one command while converting all details to a safe failure."""

    try:
        result = subprocess.run(
            list(args),
            cwd=cwd,
            env=dict(env),
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise BuildError(version, ref, command, "command could not start") from exc
    if result.returncode != 0:
        raise BuildError(version, ref, command, "command returned a non-zero status")


def _sanitize_and_validate_output(
    output: Path,
    version: str,
    ref: str,
    command: str,
    *,
    base_url: str | None = None,
    channel: str | None = None,
) -> None:
    """Remove known build caches and reject unsafe or incomplete HTML output."""

    _strip_legacy_runtime_references(output)
    _ensure_non_indexable_pages(output)
    _ensure_social_image_alt(output)
    if channel == "dev":
        _ensure_development_indexing(output)
    for candidate in sorted(output.rglob("*"), reverse=True):
        if candidate.name not in _TRANSIENT_OUTPUT_NAMES:
            continue
        if candidate.is_dir() and not candidate.is_symlink():
            shutil.rmtree(candidate)
        elif candidate.is_file() or candidate.is_symlink():
            candidate.unlink()
    directories = {
        item.name
        for item in output.iterdir()
        if item.is_dir() and not item.is_symlink()
    }
    unexpected = sorted(directories - _ALLOWED_OUTPUT_DIRECTORIES)
    if unexpected:
        raise BuildError(
            version,
            ref,
            command,
            "unexpected output directories: " + ", ".join(unexpected),
        )
    index = output / "index.html"
    static = output / "_static"
    if not index.is_file():
        raise BuildError(version, ref, command, "generated index.html is missing")
    if not static.is_dir() or not any(item.is_file() for item in static.rglob("*")):
        raise BuildError(version, ref, command, "required static assets are missing")
    for item in output.rglob("*"):
        if item.is_symlink():
            raise BuildError(version, ref, command, "symlink in generated output")
        if item.name in {".buildinfo", ".doctrees"} or "__pycache__" in item.parts:
            raise BuildError(
                version, ref, command, "transient file in generated output"
            )
    for page in output.rglob("*.html"):
        relative = page.relative_to(output)
        text = page.read_text(encoding="utf-8")
        if _EXTERNAL_RUNTIME_RESOURCE.search(text):
            raise BuildError(
                version,
                ref,
                command,
                "external runtime resource is not allowed",
            )
        if relative.parts[0].startswith("_"):
            continue
        if (
            base_url is not None
            and channel is not None
            and page.name not in _NON_INDEXABLE_PAGES
        ):
            _validate_page_metadata(
                page,
                output=output,
                version=version,
                channel=channel,
                base_url=base_url,
                text=text,
            )


def _strip_legacy_runtime_references(output: Path) -> None:
    """Remove compatibility-only extension tags from historical HTML.

    The historical source declares Tippy, Togglebutton, and Sphinx Design,
    although the audited pages do not use those features. Their generated
    assets remain available at the legacy root paths, while release pages do
    not ship broken or floating runtime resources.
    """

    for page in output.rglob("*.html"):
        text = page.read_text(encoding="utf-8")
        updated = _LEGACY_RUNTIME_TAG.sub("\n", text)
        updated = _LEGACY_RUNTIME_BODY_TAG.sub("\n", updated)
        updated = _LEGACY_RUNTIME_LINK.sub("\n", updated)
        if updated != text:
            page.write_text(updated, encoding="utf-8")


def _ensure_non_indexable_pages(output: Path) -> None:
    """Mark Sphinx utility pages as non-indexable and omit them from SEO data."""

    marker = '<meta name="robots" content="noindex, follow" />'
    existing = re.compile(
        r'<meta\s+name="robots"\s+content="[^"]*"\s*/?>', re.IGNORECASE
    )
    for page in output.rglob("*.html"):
        if page.name not in _NON_INDEXABLE_PAGES:
            continue
        text = page.read_text(encoding="utf-8")
        updated = existing.sub(marker, text, count=1)
        if updated == text and "</head>" not in text:
            raise BuildError(
                "site",
                "output",
                "validate generated HTML",
                f"utility page has no head element: {page.name}",
            )
        if updated == text:
            updated = text.replace("</head>", f"  {marker}\n</head>", 1)
        if updated != text:
            page.write_text(updated, encoding="utf-8")


def _ensure_social_image_alt(output: Path) -> None:
    """Give every generated social card a non-empty, public-safe alt value."""

    replacement = r"\1gsplot documentation page preview\2"
    for page in output.rglob("*.html"):
        text = page.read_text(encoding="utf-8")
        updated = _OG_IMAGE_ALT.sub(replacement, text)
        if updated != text:
            page.write_text(updated, encoding="utf-8")


def _ensure_development_indexing(output: Path) -> None:
    """Apply the development no-index/follow policy to every HTML page."""

    marker = '<meta name="robots" content="noindex, follow" />'
    existing = re.compile(
        r'<meta\s+name="robots"\s+content="[^"]*"\s*/?>', re.IGNORECASE
    )
    for page in output.rglob("*.html"):
        text = page.read_text(encoding="utf-8")
        updated = existing.sub(marker, text, count=1)
        if updated == text and "</head>" in text:
            updated = text.replace("</head>", f"  {marker}\n</head>", 1)
        if updated != text:
            page.write_text(updated, encoding="utf-8")


def _validate_page_metadata(
    page: Path,
    *,
    output: Path,
    version: str,
    channel: str,
    base_url: str,
    text: str,
) -> None:
    """Check canonical, OpenGraph, title, and development indexing metadata."""

    relative = page.relative_to(output).as_posix()
    expected_url = f"{base_url}/{channel}/{relative}"
    canonical_match = _CANONICAL_LINK.search(text)
    if canonical_match is None or canonical_match.group(1) != expected_url:
        raise BuildError(
            version,
            channel,
            "validate generated HTML metadata",
            f"canonical URL mismatch for {relative}",
        )
    meta_values = dict(_META_VALUE.findall(text))
    if meta_values.get("og:url") != expected_url:
        raise BuildError(
            version,
            channel,
            "validate generated HTML metadata",
            f"OpenGraph URL mismatch for {relative}",
        )
    image_url = meta_values.get("og:image", "")
    base_url_parts = urlparse(base_url)
    image_url_parts = urlparse(image_url)
    channel_path = f"{base_url_parts.path.rstrip('/')}/{channel}/"
    image_relative_path = unquote(
        image_url_parts.path[len(channel_path) :]
        if image_url_parts.path.startswith(channel_path)
        else ""
    )
    image_path = output / Path(*image_relative_path.split("/"))
    if (
        image_url_parts.scheme != base_url_parts.scheme
        or image_url_parts.netloc != base_url_parts.netloc
        or image_url_parts.query
        or image_url_parts.fragment
        or not image_url_parts.path.startswith(channel_path)
        or not image_relative_path
        or any(part in {"", ".", ".."} for part in image_relative_path.split("/"))
        or not image_path.is_file()
    ):
        raise BuildError(
            version,
            channel,
            "validate generated HTML metadata",
            f"OpenGraph image is not version-aware for {relative}",
        )
    if not meta_values.get("og:image:alt", "").strip():
        raise BuildError(
            version,
            channel,
            "validate generated HTML metadata",
            f"OpenGraph image alt text is missing for {relative}",
        )
    title_match = _TITLE.search(text)
    if title_match is None or (
        "dev" not in title_match.group(1).lower()
        and version not in title_match.group(1)
    ):
        raise BuildError(
            version,
            channel,
            "validate generated HTML metadata",
            f"version is not visible in title for {relative}",
        )
    robot_values = {
        name.lower(): content.lower()
        for name, content in _META_NAME_VALUE.findall(text)
    }
    if channel == "dev" and robot_values.get("robots") != "noindex, follow":
        raise BuildError(
            version,
            channel,
            "validate generated HTML metadata",
            f"development indexing policy is missing for {relative}",
        )


def _artifact_stats(root: Path) -> tuple[int, int, int]:
    """Return file count and deterministic uncompressed/compressed sizes.

    ``compressed_bytes`` is the sum of deterministic gzip sizes for individual
    files.  It is a stable, archive-independent budget signal for the static
    artifact and does not create another file in the published site.  The
    self-describing build manifest is excluded so its changing size cannot
    make the recorded artifact budget self-referential.
    """

    manifest_path = root / "_meta" / "build-manifest.json"
    files = [
        path for path in root.rglob("*") if path.is_file() and path != manifest_path
    ]
    compressed = sum(
        len(gzip.compress(path.read_bytes(), compresslevel=9, mtime=0))
        for path in files
    )
    return len(files), sum(path.stat().st_size for path in files), compressed


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    """Write public JSON atomically and deterministically."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        temporary.write_text(
            json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        temporary.replace(path)
    except OSError as exc:
        raise BuildError(
            "site", "manifest", "write public manifest", "manifest write failed"
        ) from exc
    finally:
        temporary.unlink(missing_ok=True)


def _promote(staging: Path, output: Path) -> None:
    """Promote a complete staging tree to the requested empty output path."""

    try:
        staging.replace(output)
    except OSError as exc:
        raise BuildError(
            "site", "staging", "promote complete site", "site promotion failed"
        ) from exc


def _validate_output_target(repo_root: Path, output: Path) -> None:
    """Reject output targets that could delete source or repository state."""

    if output == repo_root or repo_root.is_relative_to(output):
        raise BuildError(
            "site", "output", "prepare output", "output must not contain the repository"
        )
    if output.is_relative_to(repo_root):
        raise BuildError(
            "site", "output", "prepare output", "output must be outside the repository"
        )
    if output == Path(output.anchor):
        raise BuildError(
            "site", "output", "prepare output", "output must not be a filesystem root"
        )
    if output.exists() and output.is_symlink():
        raise BuildError(
            "site", "output", "prepare output", "output must not be a symlink"
        )


def _remove_output(output: Path) -> None:
    """Remove only the explicitly validated output directory."""

    if not output.exists():
        return
    if not output.is_dir() or output.is_symlink():
        raise BuildError("site", "output", "clear output", "output is not a directory")
    shutil.rmtree(output)


def _temporary_root(repo_root: Path) -> Path:
    """Return a system temporary directory that cannot be the source tree."""

    temporary_root = Path(tempfile.gettempdir()).resolve()
    if temporary_root == repo_root or temporary_root.is_relative_to(repo_root):
        raise BuildError(
            "site",
            "temporary",
            "prepare temporary root",
            "temporary root is inside repository",
        )
    temporary_root.mkdir(parents=True, exist_ok=True)
    return temporary_root


def _git_environment() -> dict[str, str]:
    """Disable Git prompts while retaining only non-secret process settings."""

    environment = dict(os.environ)
    for name in list(environment):
        uppercase_name = name.upper()
        if uppercase_name in _UNTRUSTED_ENV_NAMES or any(
            marker in uppercase_name for marker in _SENSITIVE_ENV_MARKERS
        ):
            environment.pop(name, None)
    environment["GIT_TERMINAL_PROMPT"] = "0"
    environment["GIT_CONFIG_GLOBAL"] = os.devnull
    environment["GIT_CONFIG_NOSYSTEM"] = "1"
    return environment


__all__ = [
    "BUILD_MANIFEST_SCHEMA_VERSION",
    "BuildError",
    "BuildManifest",
    "BuildRecord",
    "build_site",
]
