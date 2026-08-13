"""Tests for version-aware Sphinx configuration metadata."""

from __future__ import annotations

import runpy
from pathlib import Path

import pytest

CONF_PATH = Path(__file__).parents[2] / "docs" / "conf.py"


def _load_conf(
    monkeypatch: pytest.MonkeyPatch,
    *,
    version: str | None = None,
    base_url: str | None = None,
) -> dict:
    monkeypatch.delenv("GSPLOT_DOCS_VERSION", raising=False)
    monkeypatch.delenv("GSPLOT_DOCS_BASE_URL", raising=False)
    if version is not None:
        monkeypatch.setenv("GSPLOT_DOCS_VERSION", version)
    if base_url is not None:
        monkeypatch.setenv("GSPLOT_DOCS_BASE_URL", base_url)
    return runpy.run_path(str(CONF_PATH))


def test_conf_defaults_to_non_indexable_main_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = _load_conf(monkeypatch)

    assert values["version"] == "dev"
    assert values["release"] == "dev"
    assert values["version_match"] == "dev"
    assert values["html_context"]["github_version"] == "main"
    assert values["html_context"]["gsplot_is_development"] is True
    assert values["ogp_canonical_url"] == (
        "https://soichiroyamane.github.io/gsplot/dev/"
    )
    assert values["ogp_social_cards"] == {"enable": False}
    assert values["ogp_image"] == "_static/logo/logo_title_gsplot.png"
    assert values["ogp_image_alt"]
    assert values["html_theme_options"]["switcher"]["json_url"].endswith(
        "/_meta/switcher.json"
    )


def test_conf_normalizes_release_metadata_and_custom_base_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = _load_conf(
        monkeypatch,
        version="v0.3.0",
        base_url="https://docs.example.test/project/",
    )

    assert values["version"] == "0.3.0"
    assert values["release"] == "0.3.0"
    assert values["version_match"] == "v0.3.0"
    assert values["html_context"]["github_version"] == "v0.3.0"
    assert values["html_context"]["gsplot_is_development"] is False
    assert values["ogp_canonical_url"] == ("https://docs.example.test/project/v0.3.0/")
    assert values["html_theme_options"]["announcement"] == (
        "You are reading release v0.3.0."
    )


@pytest.mark.parametrize(
    "version",
    ["", "latest", "0.3", "v0.03.0", "0.3.0.dev1", "0+unknown"],
)
def test_conf_rejects_ambiguous_version_metadata(
    monkeypatch: pytest.MonkeyPatch, version: str
) -> None:
    with pytest.raises(RuntimeError, match="GSPLOT_DOCS_VERSION"):
        _load_conf(monkeypatch, version=version)


@pytest.mark.parametrize(
    "base_url",
    [
        "",
        "docs.example.test/project",
        "https://user:password@example.test/docs",
        "https://example.test/docs?x=1",
    ],
)
def test_conf_rejects_unsafe_site_base_url(
    monkeypatch: pytest.MonkeyPatch, base_url: str
) -> None:
    with pytest.raises(RuntimeError, match="GSPLOT_DOCS_BASE_URL"):
        _load_conf(monkeypatch, base_url=base_url)


def test_setup_validates_examples_and_registers_redirects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sphinx setup uses the shared runner even when generation is skipped."""

    values = _load_conf(monkeypatch)
    monkeypatch.setenv("GSPLOT_SKIP_EXAMPLE_IMAGES", "1")

    class App:
        def __init__(self) -> None:
            self.events: list[str] = []

        def connect(self, event: str, callback: object) -> None:
            self.events.append(event)

    app = App()
    values["setup"](app)

    assert app.events == [
        "autodoc-skip-member",
        "autodoc-process-docstring",
        "html-collect-pages",
    ]


def test_type_alias_pages_use_the_gsplot_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Autodoc must not expose an implementation type's generic prose."""

    values = _load_conf(monkeypatch)
    process = values["document_type_alias"]
    lines = ["Represent a PEP 604 union type"]

    process(None, "data", "gsplot.AxesTarget", object(), None, lines)

    assert lines[0] == "One Axes or a deterministic finite collection of Axes."
    assert "Examples" in lines
    assert ">>> target: gs.AxesTarget = axes" in lines

    unchanged = ["ordinary function documentation"]
    process(None, "function", "gsplot.line", object(), None, unchanged)
    assert unchanged == ["ordinary function documentation"]
