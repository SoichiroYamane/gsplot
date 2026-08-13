"""Run bounded, read-only smoke checks against the deployed documentation site."""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from tools.maintenance.docs_site.catalog import CatalogError, ReleaseCatalog
from tools.maintenance.docs_site.switcher import (
    DEFAULT_BASE_URL,
    normalize_base_url,
    validate_switcher,
)


class SmokeError(ValueError):
    """Raised when a deployed documentation endpoint violates the contract."""


Fetch = Callable[[str], tuple[int, bytes]]


def _load_json(path: Path, description: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SmokeError(f"{description} could not be read") from exc
    if not isinstance(value, Mapping):
        raise SmokeError(f"{description} must contain an object")
    return value


def _fetch_url(url: str, *, timeout: float) -> tuple[int, bytes]:
    request = Request(
        url,
        headers={
            "Accept": "text/html,application/json,text/plain,*/*",
            "User-Agent": "gsplot-docs-smoke",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return int(getattr(response, "status", 200)), response.read(
                16 * 1024 * 1024
            )
    except HTTPError as exc:
        return exc.code, exc.read(16 * 1024 * 1024)
    except (OSError, URLError) as exc:
        raise SmokeError("HTTP request could not be completed") from exc


def _url(base_url: str, route: str) -> str:
    return urljoin(base_url + "/", route.lstrip("/"))


def _require_status(
    fetch: Fetch, base_url: str, route: str, expected: int = 200
) -> bytes:
    try:
        status, body = fetch(_url(base_url, route))
    except SmokeError:
        raise
    if status != expected:
        raise SmokeError(f"{route} returned HTTP {status}, expected {expected}")
    return body


def _manifest_release_tags(value: Mapping[str, Any]) -> frozenset[str]:
    builds = value.get("builds")
    if not isinstance(builds, list):
        raise SmokeError("deployed manifest has no build list")
    tags: set[str] = set()
    for item in builds:
        if not isinstance(item, Mapping) or item.get("channel") != "release":
            continue
        tag = item.get("source_ref")
        if not isinstance(tag, str):
            raise SmokeError("deployed manifest has an invalid release record")
        tags.add(tag)
    if not tags:
        raise SmokeError("deployed manifest has no immutable release records")
    return frozenset(tags)


def check_site(
    catalog: ReleaseCatalog,
    manifest: Mapping[str, Any],
    base_url: str,
    *,
    fetch: Fetch,
    unknown_route: str = "/_gsplot-smoke-not-found-7e4f2c.html",
) -> None:
    """Validate the deployed site using only public HTTP GET requests."""

    base = normalize_base_url(base_url)
    local_builds = manifest.get("builds")
    if not isinstance(local_builds, list):
        raise SmokeError("local manifest has no build list")
    local_release_tags = _manifest_release_tags(manifest)
    expected_release_tags = frozenset(item.tag for item in catalog.releases)
    if local_release_tags != expected_release_tags:
        raise SmokeError("local manifest does not match the catalog")
    if manifest.get("stable_tag") != catalog.stable_tag:
        raise SmokeError("local manifest stable tag does not match the catalog")

    root = _require_status(fetch, base, "/")
    root_text = root.decode("utf-8", errors="replace")
    if 'http-equiv="refresh"' not in root_text or "/stable/" not in root_text:
        raise SmokeError("root entry does not provide the stable redirect")

    stable = _require_status(fetch, base, "/stable/")
    stable_text = stable.decode("utf-8", errors="replace")
    try:
        stable_record = next(
            item
            for item in local_builds
            if isinstance(item, Mapping) and item.get("channel") == "stable"
        )
    except StopIteration as exc:
        raise SmokeError("local manifest has no stable record") from exc
    stable_version = stable_record.get("docs_version")
    if not isinstance(stable_version, str) or catalog.stable_tag not in stable_text:
        raise SmokeError("stable page does not identify the selected release")
    if stable_version not in stable_text:
        raise SmokeError("stable page does not identify its documented version")

    dev = _require_status(fetch, base, "/dev/")
    dev_text = dev.decode("utf-8", errors="replace").lower()
    if 'name="robots" content="noindex, follow"' not in dev_text:
        raise SmokeError("development page is missing its noindex policy")
    if "development" not in dev_text:
        raise SmokeError("development page is not visibly marked")
    examples = _require_status(fetch, base, "/dev/guides/examples/index.html")
    if "examples" not in examples.decode("utf-8", errors="replace").lower():
        raise SmokeError("development examples index is not identifiable")
    legacy_examples = _require_status(fetch, base, "/dev/guides/demo/index.html")
    legacy_text = legacy_examples.decode("utf-8", errors="replace")
    if (
        'http-equiv="refresh"' not in legacy_text
        or "../examples/index.html" not in legacy_text
    ):
        raise SmokeError("development demonstrations redirect is invalid")

    for release in catalog.releases:
        page = _require_status(fetch, base, f"/{release.tag}/")
        if release.tag not in page.decode("utf-8", errors="replace"):
            raise SmokeError(f"immutable page does not identify {release.tag}")

    switcher_body = _require_status(fetch, base, "/_meta/switcher.json")
    try:
        switcher = json.loads(switcher_body)
    except json.JSONDecodeError as exc:
        raise SmokeError("deployed switcher is invalid JSON") from exc
    try:
        validate_switcher(switcher, catalog, base_url=base)
    except (TypeError, ValueError) as exc:
        raise SmokeError("deployed switcher does not match the catalog") from exc

    deployed_catalog_body = _require_status(fetch, base, "/_meta/catalog.json")
    try:
        deployed_catalog = ReleaseCatalog.from_mapping(
            json.loads(deployed_catalog_body)
        )
    except (CatalogError, json.JSONDecodeError, TypeError) as exc:
        raise SmokeError("deployed catalog is invalid") from exc
    if deployed_catalog != catalog:
        raise SmokeError("deployed catalog does not match the build catalog")

    deployed_manifest_body = _require_status(fetch, base, "/_meta/build-manifest.json")
    try:
        deployed_manifest = json.loads(deployed_manifest_body)
    except json.JSONDecodeError as exc:
        raise SmokeError("deployed build manifest is invalid JSON") from exc
    if deployed_manifest != dict(manifest):
        raise SmokeError("deployed build manifest does not match the build artifact")

    representative_routes = (
        f"/stable/api_reference/index.html",
        f"/stable/guides/index.html",
        f"/stable/_static/logo/logo_title_gsplot.png",
        f"/stable/_static/styles/theme.css",
        f"/stable/_static/scripts/pydata-sphinx-theme.js",
    )
    for route in representative_routes:
        _require_status(fetch, base, route)

    robots = _require_status(fetch, base, "/robots.txt").decode(
        "utf-8", errors="replace"
    )
    if "Sitemap:" not in robots or "/dev/" not in robots:
        raise SmokeError("robots.txt does not identify the sitemap and dev policy")
    sitemap = _require_status(fetch, base, "/sitemap.xml").decode(
        "utf-8", errors="replace"
    )
    if catalog.stable_tag not in sitemap or "/stable/" in sitemap or "/dev/" in sitemap:
        raise SmokeError("sitemap does not contain the immutable release policy")

    not_found = _require_status(fetch, base, unknown_route, expected=404)
    if "Page not found" not in not_found.decode("utf-8", errors="replace"):
        raise SmokeError("custom 404 page was not served")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke-test a deployed gsplot docs site."
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--attempts", type=int, default=12)
    parser.add_argument("--delay", type=float, default=10.0)
    parser.add_argument("--timeout", type=float, default=15.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run bounded smoke attempts and return a process status."""

    args = _parser().parse_args(argv)
    if args.attempts < 1 or args.delay < 0 or args.timeout <= 0:
        print("documentation smoke failed: invalid retry settings", file=sys.stderr)
        return 1
    try:
        catalog_value = json.loads(args.catalog.read_text(encoding="utf-8"))
        if not isinstance(catalog_value, Mapping):
            raise SmokeError("local catalog must contain an object")
        catalog = ReleaseCatalog.from_mapping(catalog_value)
        manifest = _load_json(args.manifest, "local build manifest")
        base = normalize_base_url(args.base_url)
    except (CatalogError, OSError, json.JSONDecodeError, SmokeError) as exc:
        print(f"documentation smoke failed: {exc}", file=sys.stderr)
        return 1

    def fetch(url: str) -> tuple[int, bytes]:
        return _fetch_url(url, timeout=args.timeout)

    last_error: SmokeError | None = None
    for attempt in range(1, args.attempts + 1):
        try:
            check_site(catalog, manifest, base, fetch=fetch)
        except SmokeError as exc:
            last_error = exc
            if attempt == args.attempts:
                break
            time.sleep(args.delay)
        else:
            print(f"documentation smoke passed on attempt {attempt}")
            return 0
    print(f"documentation smoke failed: {last_error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
