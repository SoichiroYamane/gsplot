"""Generate validated same-channel redirects for renamed documentation pages."""

from __future__ import annotations

import posixpath
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Iterator
from urllib.parse import urlparse


class RedirectError(ValueError):
    """Raised when a documentation redirect is unsafe or ambiguous."""


@dataclass(frozen=True)
class Redirect:
    """One normalized Sphinx page-name migration."""

    source: str
    destination: str


_RAW_REDIRECTS = (
    ("guides/demo/index", "guides/examples/index"),
    ("guides/demo/1_axes", "guides/examples/layout-mosaic"),
    ("guides/demo/2_line_and_label", "guides/examples/lines-and-labels"),
    ("guides/demo/3_config", "guides/examples/configuration"),
    ("guides/demo/4_paper_plot", "guides/examples/publication"),
    ("guides/demo/5_scatter", "guides/examples/scatter"),
    ("guides/demo/6_line_colormap", "guides/examples/colored-lines"),
    ("guides/demo/7_graph_white", "guides/examples/white-theme"),
    ("guides/demo/8_graph_transparent", "guides/examples/transparent-theme"),
    ("guides/demo/9_compatibility", "guides/examples/legacy-v0"),
    ("guides/demo/10_subplots", "guides/examples/matplotlib-interoperability"),
    ("guides/demo/11_directory", "guides/examples/explicit-paths"),
    ("guides/demo/12_reproducibility", "guides/examples/reproducibility"),
    ("guides/demo/13_REPL", "guides/examples/repl"),
)


def _page_name(value: object, field: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise RedirectError(f"redirect {field} must be a normalized page name")
    selected = PurePosixPath(value)
    if (
        selected.is_absolute()
        or selected.as_posix() != value
        or selected.suffix
        or any(part in {"", ".", ".."} for part in selected.parts)
        or not selected.is_relative_to(PurePosixPath("guides"))
    ):
        raise RedirectError(f"redirect {field} must stay under guides/")
    return value


def validate_redirects(values: object) -> tuple[Redirect, ...]:
    """Validate one finite redirect map and reject duplicate page names."""

    if not isinstance(values, (tuple, list)):
        raise RedirectError("redirect map must be an ordered sequence")
    redirects: list[Redirect] = []
    sources: set[str] = set()
    for position, value in enumerate(values):
        if not isinstance(value, (tuple, list)) or len(value) != 2:
            raise RedirectError(f"redirect entry {position} must contain two names")
        source = _page_name(value[0], "source")
        destination = _page_name(value[1], "destination")
        if source in sources:
            raise RedirectError(f"redirect map repeats source {source}")
        if source == destination:
            raise RedirectError(f"redirect {source} points to itself")
        sources.add(source)
        redirects.append(Redirect(source, destination))
    return tuple(redirects)


REDIRECTS = validate_redirects(_RAW_REDIRECTS)


def collect_redirect_pages(app: Any) -> Iterator[tuple[str, dict[str, str], str]]:
    """Yield HTML-only compatibility pages for Sphinx's collection event."""

    if getattr(app.builder, "format", None) != "html":
        return
    html_baseurl = getattr(getattr(app, "config", None), "html_baseurl", None)
    if not isinstance(html_baseurl, str) or not html_baseurl:
        raise RedirectError("HTML redirects require a configured html_baseurl")
    base_parts = urlparse(html_baseurl)
    if (
        base_parts.scheme not in {"http", "https"}
        or not base_parts.netloc
        or base_parts.username is not None
        or base_parts.password is not None
        or base_parts.query
        or base_parts.fragment
    ):
        raise RedirectError("HTML redirects require an absolute safe html_baseurl")
    canonical_base = html_baseurl.rstrip("/")
    for redirect in REDIRECTS:
        source_parent = PurePosixPath(redirect.source).parent.as_posix()
        relative_target = posixpath.relpath(
            f"{redirect.destination}.html", start=source_parent
        )
        yield (
            redirect.source,
            {
                "redirect_canonical": (f"{canonical_base}/{redirect.destination}.html"),
                "redirect_destination": redirect.destination,
                "redirect_target": relative_target,
            },
            "redirect.html",
        )
