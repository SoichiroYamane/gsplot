"""Tests for the read-only deployed documentation smoke checks."""

from __future__ import annotations

import json

from tools.maintenance.docs_site.catalog import ReleaseCatalog, ReleaseRecord
from tools.maintenance.docs_site.switcher import generate_switcher
from tools.maintenance.smoke_docs_site import check_site


def test_smoke_check_validates_the_public_site_contract() -> None:
    catalog = ReleaseCatalog(
        main_commit="a" * 40,
        stable_tag="v0.3.0",
        releases=(
            ReleaseRecord(
                tag="v0.3.0",
                version="0.3.0",
                commit="b" * 40,
                published_at="2026-08-11T00:00:00Z",
                url="https://github.com/SoichiroYamane/gsplot/releases/tag/v0.3.0",
            ),
        ),
    )
    manifest = {
        "schema_version": 2,
        "status": "success",
        "main_commit": catalog.main_commit,
        "stable_tag": catalog.stable_tag,
        "builds": [
            {"channel": "dev", "source_ref": "main", "docs_version": "dev"},
            {"channel": "release", "source_ref": "v0.3.0", "docs_version": "0.3.0"},
            {"channel": "stable", "source_ref": "v0.3.0", "docs_version": "0.3.0"},
        ],
        "exclusions": [],
        "warnings": [],
        "artifact": {
            "file_count": 10,
            "uncompressed_bytes": 100,
            "compressed_bytes": 50,
        },
    }
    base = "https://example.test/gsplot"
    switcher = generate_switcher(catalog, base_url=base)
    responses = {
        "/": '<meta http-equiv="refresh" content="0; url=/gsplot/stable/">',
        "/stable/": "gsplot v0.3.0 documentation 0.3.0",
        "/dev/": '<meta name="robots" content="noindex, follow"> Development documentation',
        "/v0.3.0/": "v0.3.0 documentation",
        "/_meta/switcher.json": json.dumps(switcher),
        "/_meta/catalog.json": json.dumps(catalog.to_mapping()),
        "/_meta/build-manifest.json": json.dumps(manifest),
        "/stable/api_reference/index.html": "api",
        "/stable/guides/index.html": "guides",
        "/stable/_static/logo/logo_title_gsplot.png": "image",
        "/stable/_static/styles/theme.css": "css",
        "/stable/_static/scripts/pydata-sphinx-theme.js": "js",
        "/robots.txt": "Sitemap: https://example.test/gsplot/sitemap.xml\nDisallow: /gsplot/dev/",
        "/sitemap.xml": "<loc>https://example.test/gsplot/v0.3.0/index.html</loc>",
    }

    def fetch(url: str) -> tuple[int, bytes]:
        route = url.removeprefix(base)
        if route == "/_gsplot-smoke-not-found-7e4f2c.html":
            return 404, b"<h1>Page not found</h1>"
        body = responses[route]
        return 200, body.encode("utf-8")

    check_site(catalog, manifest, base, fetch=fetch)
