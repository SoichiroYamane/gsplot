"""Generate and validate the static site shell around versioned Sphinx output."""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path
from urllib.parse import quote, urlparse

from .catalog import ReleaseCatalog
from .switcher import normalize_base_url

_UNUSED_CHANNEL_DIRECTORIES = (
    "_downloads",
    "_modules",
    "_sources",
    "_sphinx_design_static",
)
_UNUSED_STATIC_DIRECTORIES = ("tippy", "tutorial")
_UNUSED_STATIC_FILES = (
    "design-tabs.js",
    "file.png",
    "minus.png",
    "plus.png",
    "sphinx-design.min.css",
    "togglebutton.css",
    "togglebutton.js",
    "webpack-macros.html",
)
_ROOT_COMPATIBILITY_ASSET_TREES = ("_images", "_static")
_ROOT_COMPATIBILITY_SINGLE_ASSETS = ("objects.inv", "searchindex.js")
_ROOT_COMPATIBILITY_SOURCE = Path("_sources/index.md.txt")
_LEGACY_TIPPY_ASSET = Path(
    "_static/tippy/index.e4541f43-c3c4-4f8e-910e-1cc2b87bf3db.js"
)
_REQUIRED_ROOT_COMPATIBILITY_ASSETS = (
    Path("searchindex.js"),
    _ROOT_COMPATIBILITY_SOURCE,
    Path("_images/SC_cal.png"),
    Path("_static/logo_gsplot.svg"),
    Path("_static/logo/logo_title_gsplot.png"),
    Path("_static/clipboard.min.js"),
    Path("_static/copybutton.css"),
    Path("_static/copybutton.js"),
    Path("_static/design-tabs.js"),
    Path("_static/doctools.js"),
    Path("_static/documentation_options.js"),
    Path("_static/language_data.js"),
    Path("_static/pygments.css"),
    Path("_static/scripts/bootstrap.js"),
    Path("_static/scripts/fontawesome.js"),
    Path("_static/scripts/pydata-sphinx-theme.js"),
    Path("_static/searchtools.js"),
    Path("_static/sphinx-design.min.css"),
    Path("_static/sphinx_highlight.js"),
    Path("_static/styles/pydata-sphinx-theme.css"),
    Path("_static/styles/theme.css"),
    _LEGACY_TIPPY_ASSET,
    Path("_static/togglebutton.css"),
    Path("_static/togglebutton.js"),
)
_TRANSIENT_NAMES = {
    ".buildinfo",
    ".doctrees",
    "__pycache__",
    "create_switcher.py",
    "tippy_doi_cache.json",
    "tippy_rtd_cache.json",
    "tippy_wiki_cache.json",
    "webpack-macros.html",
}
_NON_INDEXABLE_PAGES = {"genindex.html", "py-modindex.html", "search.html"}


class SiteError(ValueError):
    """Raised when a staged static site violates the public site contract."""


def finalize_site(staging: Path, catalog: ReleaseCatalog, *, base_url: str) -> None:
    """Create the root shell, compatibility routes, crawler files, and sitemap."""

    base = normalize_base_url(base_url)
    dev = staging / "dev"
    if not dev.is_dir():
        raise SiteError("site shell requires a development build")
    stable = staging / catalog.stable_tag
    if not stable.is_dir():
        raise SiteError("site shell requires the selected stable release")
    _copy_root_compatibility_assets(stable, staging)
    redirect_routes = _write_root_redirects(dev, staging, base)
    _remove_unneeded_channel_output(staging)
    _write_root_entry(staging / "index.html", base)
    _write_not_found(staging / "404.html", base)
    _write_robots(staging / "robots.txt", base)
    _write_sitemap(staging / "sitemap.xml", catalog, staging, base)
    _validate_site(staging, catalog, redirect_routes, base)


def _copy_root_compatibility_assets(stable: Path, root: Path) -> None:
    """Keep the inventoried root assets without copying a documentation tree."""

    for relative in _ROOT_COMPATIBILITY_ASSET_TREES:
        source = stable / relative
        if source.is_dir():
            _copy_tree(source, root / relative)
    for relative in _ROOT_COMPATIBILITY_SINGLE_ASSETS:
        source = stable / relative
        if source.is_file():
            _copy_file(source, root / relative)
    source = stable / _ROOT_COMPATIBILITY_SOURCE
    if source.is_file():
        _copy_file(source, root / _ROOT_COMPATIBILITY_SOURCE)
    _copy_legacy_tippy_asset(stable, root)
    missing = [
        relative.as_posix()
        for relative in _REQUIRED_ROOT_COMPATIBILITY_ASSETS
        if not (root / relative).is_file()
    ]
    if missing:
        raise SiteError(
            "required root compatibility assets are missing: " + ", ".join(missing)
        )


def _copy_legacy_tippy_asset(stable: Path, root: Path) -> None:
    """Preserve the observed legacy Tippy route with a deterministic name."""

    candidates = sorted((stable / "_static" / "tippy").glob("index.*.js"))
    if len(candidates) != 1:
        return
    source = candidates[0]
    destination = root / _LEGACY_TIPPY_ASSET
    _copy_file(source, destination)
    _canonicalize_tippy_asset(destination)


def _canonicalize_tippy_asset(path: Path) -> None:
    """Normalize unordered tooltip selectors for reproducible output."""

    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    prefix = "selector_to_html = "
    if not lines or not lines[0].startswith(prefix):
        raise SiteError("legacy Tippy asset has an unexpected format")
    try:
        selectors = json.loads(lines[0][len(prefix) :])
    except json.JSONDecodeError as exc:
        raise SiteError("legacy Tippy asset contains invalid JSON") from exc
    if not isinstance(selectors, dict):
        raise SiteError("legacy Tippy asset selectors are not an object")
    lines[0] = prefix + json.dumps(selectors, sort_keys=True) + "\n"
    path.write_text("".join(lines), encoding="utf-8")


def _write_root_redirects(dev: Path, root: Path, base_url: str) -> set[str]:
    """Write no-JavaScript compatibility pages for every source HTML route."""

    routes: set[str] = set()
    for source in sorted(dev.rglob("*.html")):
        relative = source.relative_to(dev)
        if relative in {Path("404.html"), Path("index.html")} or relative.parts[
            0
        ].startswith("_"):
            continue
        target_path = "/dev/" + relative.as_posix()
        destination = root / relative
        _write_text(
            destination,
            _redirect_page(
                title=f"gsplot documentation: {relative.as_posix()}",
                target=_site_path(base_url, target_path),
                canonical=f"{base_url}{target_path}",
            ),
        )
        routes.add(relative.as_posix())
    return routes


def _remove_unneeded_channel_output(root: Path) -> None:
    """Remove source copies, unused media, and build helpers from each channel."""

    channels = [root / "dev", root / "stable"] + [
        path for path in root.iterdir() if path.is_dir() and path.name.startswith("v")
    ]
    for channel in channels:
        if not channel.is_dir():
            continue
        for relative in _UNUSED_CHANNEL_DIRECTORIES:
            _remove_path(channel / relative)
        for relative in _UNUSED_STATIC_DIRECTORIES:
            _remove_path(channel / "_static" / relative)
        for relative in _UNUSED_STATIC_FILES:
            _remove_path(channel / "_static" / relative)
        for path in sorted(channel.rglob("*"), reverse=True):
            if path.name in _TRANSIENT_NAMES:
                _remove_path(path)


def _write_root_entry(path: Path, base_url: str) -> None:
    """Write the small neutral root entry instead of a duplicate docs tree."""

    _write_text(
        path,
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow">
  <meta http-equiv="refresh" content="0; url={stable_path}">
  <link rel="canonical" href="{base}/stable/">
  <title>gsplot documentation</title>
</head>
<body>
  <main>
    <h1>gsplot documentation</h1>
    <p>Opening the stable documentation…</p>
    <p><a href="{stable_path}">Continue to the stable documentation</a></p>
    <p><a href="{dev_path}">Read the development documentation</a></p>
  </main>
</body>
</html>
""".format(
            base=html.escape(base_url, quote=True),
            stable_path=html.escape(_site_path(base_url, "/stable/"), quote=True),
            dev_path=html.escape(_site_path(base_url, "/dev/"), quote=True),
        ),
    )


def _write_not_found(path: Path, base_url: str) -> None:
    """Write an accessible, public-safe static not-found page."""

    _write_text(
        path,
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, nofollow">
  <link rel="canonical" href="{base}/404.html">
  <title>Page not found · gsplot documentation</title>
</head>
<body>
  <main>
    <h1>Page not found</h1>
    <p>The requested gsplot documentation page does not exist.</p>
    <nav aria-label="Recovery links">
      <ul>
        <li><a href="{stable_path}">Stable documentation</a></li>
        <li><a href="{dev_path}">Development documentation</a></li>
        <li><a href="{search_path}">Search documentation</a></li>
        <li><a href="https://github.com/SoichiroYamane/gsplot">Source repository</a></li>
        <li><a href="https://github.com/SoichiroYamane/gsplot/issues">Report an issue</a></li>
      </ul>
    </nav>
  </main>
</body>
</html>
""".format(
            base=html.escape(base_url, quote=True),
            stable_path=html.escape(_site_path(base_url, "/stable/"), quote=True),
            dev_path=html.escape(_site_path(base_url, "/dev/"), quote=True),
            search_path=html.escape(_site_path(base_url, "/search.html"), quote=True),
        ),
    )


def _write_robots(path: Path, base_url: str) -> None:
    """Write the deterministic crawler policy for the static site."""

    _write_text(
        path,
        """User-agent: *
Allow: /
Disallow: {dev_path}
Disallow: {meta_path}
Disallow: {modules_path}
Disallow: {sources_path}
Disallow: {downloads_path}

Sitemap: {base}/sitemap.xml
""".format(
            base=base_url,
            dev_path=_site_path(base_url, "/dev/"),
            meta_path=_site_path(base_url, "/_meta/"),
            modules_path=_site_path(base_url, "/_modules/"),
            sources_path=_site_path(base_url, "/_sources/"),
            downloads_path=_site_path(base_url, "/_downloads/"),
        ),
    )


def _write_sitemap(
    path: Path, catalog: ReleaseCatalog, root: Path, base_url: str
) -> None:
    """Write an indexable-page sitemap, excluding stable and development aliases."""

    entries: list[str] = []
    for release in catalog.releases:
        release_root = root / release.tag
        for page in sorted(release_root.rglob("*.html")):
            relative = page.relative_to(release_root)
            if (
                relative.parts[0].startswith("_")
                or relative.name in _NON_INDEXABLE_PAGES
            ):
                continue
            page_url = (
                f"{base_url}/{release.tag}/"
                f"{quote(relative.as_posix(), safe='/._-')}"
            )
            lastmod = html.escape(release.published_at, quote=True)
            entries.append(
                f"  <url><loc>{html.escape(page_url, quote=True)}</loc>"
                f"<lastmod>{lastmod}</lastmod></url>"
            )
    _write_text(
        path,
        """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries}
</urlset>
""".format(entries="\n".join(entries)),
    )


def _validate_site(
    root: Path, catalog: ReleaseCatalog, redirects: set[str], base_url: str
) -> None:
    """Validate the final site shape and compatibility route semantics."""

    expected_channels = {
        "dev",
        "stable",
        *(release.tag for release in catalog.releases),
    }
    expected_root_entries = {
        "404.html",
        "_images",
        "_meta",
        "_sources",
        "_static",
        "dev",
        "index.html",
        "objects.inv",
        "robots.txt",
        "searchindex.js",
        "sitemap.xml",
        "stable",
        *[release.tag for release in catalog.releases],
    }
    expected_root_entries.update(Path(route).parts[0] for route in redirects)
    actual_root_entries = {path.name for path in root.iterdir()}
    unexpected = actual_root_entries - expected_root_entries
    if unexpected:
        raise SiteError(
            "unexpected site root entries: " + ", ".join(sorted(unexpected))
        )
    missing_root_entries = expected_root_entries - actual_root_entries
    if missing_root_entries:
        raise SiteError(
            "required site root entries are missing: "
            + ", ".join(sorted(missing_root_entries))
        )
    if {
        path.name for path in root.iterdir() if path.is_dir()
    } & expected_channels == set():
        raise SiteError("site has no documentation channels")
    for channel in expected_channels:
        channel_root = root / channel
        if not channel_root.is_dir() or not (channel_root / "index.html").is_file():
            raise SiteError(f"site channel is incomplete: {channel}")
    for route in redirects:
        page = root / route
        text = page.read_text(encoding="utf-8")
        if 'http-equiv="refresh"' not in text or "/dev/" not in text:
            raise SiteError(f"compatibility route is not a redirect: {route}")
        target = root / "dev" / route
        if not target.is_file():
            raise SiteError(f"compatibility redirect target is missing: {route}")
    for path in root.rglob("*"):
        if path.is_symlink() or path.name in _TRANSIENT_NAMES:
            raise SiteError("unsafe generated site entry")
        if "__pycache__" in path.parts:
            raise SiteError("Python cache in generated site")
    for forbidden in _UNUSED_CHANNEL_DIRECTORIES:
        if any(
            path.is_dir() and path.name == forbidden and path != root / "_sources"
            for path in root.rglob("*")
        ):
            raise SiteError(f"unneeded generated directory remains: {forbidden}")
    if len((root / "index.html").read_text(encoding="utf-8")) > 16_384:
        raise SiteError("root entry must remain a small neutral page")
    for required in ("404.html", "robots.txt", "sitemap.xml"):
        if not (root / required).is_file():
            raise SiteError(f"required site file is missing: {required}")
    sitemap = (root / "sitemap.xml").read_text(encoding="utf-8")
    if f"{base_url}/stable/" in sitemap or f"{base_url}/dev/" in sitemap:
        raise SiteError("sitemap contains an alias channel")


def _copy_tree(source: Path, destination: Path) -> None:
    """Copy a tree while excluding transient and build-helper files."""

    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if any(part in _TRANSIENT_NAMES for part in relative.parts):
            continue
        if relative.parts and relative.parts[0] == "tutorial":
            continue
        if relative.parts and relative.parts[0] == "tippy":
            continue
        target = destination / relative
        if path.is_symlink():
            raise SiteError("symlink in documentation asset tree")
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            _copy_file(path, target)


def _site_path(base_url: str, route: str) -> str:
    """Return a site-root path that also works for GitHub project Pages."""

    prefix = urlparse(base_url).path.rstrip("/")
    return f"{prefix}{route}" if prefix else route


def _copy_file(source: Path, destination: Path) -> None:
    if source.is_symlink() or not source.is_file():
        raise SiteError("invalid documentation asset")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _redirect_page(*, title: str, target: str, canonical: str) -> str:
    escaped_title = html.escape(title)
    escaped_target = html.escape(target, quote=True)
    escaped_canonical = html.escape(canonical, quote=True)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="0; url={escaped_target}">
  <link rel="canonical" href="{escaped_canonical}">
  <title>{escaped_title}</title>
</head>
<body>
  <main>
    <h1>{escaped_title}</h1>
    <p>This documentation page moved.</p>
    <p><a href="{escaped_target}">Continue to the development documentation</a></p>
  </main>
</body>
</html>
"""


__all__ = ["SiteError", "finalize_site"]
