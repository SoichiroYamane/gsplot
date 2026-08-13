"""Tests for current-channel documentation redirects."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from tools.maintenance.docs_redirects import (
    REDIRECTS,
    RedirectError,
    collect_redirect_pages,
    validate_redirects,
)


def test_redirect_map_covers_every_numbered_demo_route() -> None:
    assert len(REDIRECTS) == 14
    assert {redirect.source for redirect in REDIRECTS} == {
        "guides/demo/index",
        *(
            f"guides/demo/{name}"
            for name in (
                "1_axes",
                "2_line_and_label",
                "3_config",
                "4_paper_plot",
                "5_scatter",
                "6_line_colormap",
                "7_graph_white",
                "8_graph_transparent",
                "9_compatibility",
                "10_subplots",
                "11_directory",
                "12_reproducibility",
                "13_REPL",
            )
        ),
    }


def test_redirect_pages_are_html_only_and_same_channel_relative() -> None:
    html_app = SimpleNamespace(builder=SimpleNamespace(format="html"))
    pages = list(collect_redirect_pages(html_app))

    assert pages[0] == (
        "guides/demo/index",
        {
            "redirect_destination": "guides/examples/index",
            "redirect_target": "../examples/index.html",
        },
        "redirect.html",
    )
    assert all(
        not context["redirect_target"].startswith("/") for _, context, _ in pages
    )

    latex_app = SimpleNamespace(builder=SimpleNamespace(format="latex"))
    assert list(collect_redirect_pages(latex_app)) == []


@pytest.mark.parametrize(
    "values",
    [
        (("../private", "guides/examples/index"),),
        (("guides/demo/index.html", "guides/examples/index"),),
        (("guides/demo/index", "https://example.test"),),
        (("guides/demo/index", "guides/demo/index"),),
        (
            ("guides/demo/index", "guides/examples/index"),
            ("guides/demo/index", "guides/examples/other"),
        ),
    ],
)
def test_redirect_map_rejects_unsafe_or_duplicate_entries(values: object) -> None:
    with pytest.raises(RedirectError):
        validate_redirects(values)
