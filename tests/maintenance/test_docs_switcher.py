"""Tests for documentation version-switcher generation."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.maintenance.docs_site.catalog import ReleaseCatalog, ReleaseRecord
from tools.maintenance.docs_site.switcher import (
    generate_switcher,
    load_switcher,
    normalize_base_url,
    validate_switcher,
    write_switcher,
)


def _catalog() -> ReleaseCatalog:
    return ReleaseCatalog(
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
            ReleaseRecord(
                tag="v0.2.0",
                version="0.2.0",
                commit="c" * 40,
                published_at="2025-01-01T00:00:00Z",
                url="https://github.com/SoichiroYamane/gsplot/releases/tag/v0.2.0",
            ),
        ),
    )


def test_switcher_has_dev_and_one_preferred_stable_entry() -> None:
    entries = generate_switcher(_catalog(), base_url="https://example.test/gsplot/")

    assert entries == [
        {
            "name": "dev",
            "version": "dev",
            "url": "https://example.test/gsplot/dev/",
            "preferred": False,
        },
        {
            "name": "v0.3.0 (stable)",
            "version": "v0.3.0",
            "url": "https://example.test/gsplot/stable/",
            "preferred": True,
        },
        {
            "name": "v0.2.0",
            "version": "v0.2.0",
            "url": "https://example.test/gsplot/v0.2.0/",
            "preferred": False,
        },
    ]
    validate_switcher(entries, _catalog(), base_url="https://example.test/gsplot")


def test_switcher_round_trip(tmp_path: Path) -> None:
    entries = generate_switcher(_catalog())
    output = tmp_path / "switcher.json"

    write_switcher(entries, output)

    assert load_switcher(output) == entries


def test_switcher_rejects_mutated_preferred_entry() -> None:
    entries = generate_switcher(_catalog())
    entries[2]["preferred"] = True

    with pytest.raises(ValueError, match="preferred"):
        validate_switcher(entries, _catalog())


def test_switcher_rejects_string_boolean() -> None:
    entries = generate_switcher(_catalog())
    entries[1]["preferred"] = "true"

    with pytest.raises(ValueError, match="boolean"):
        validate_switcher(entries, _catalog())


def test_base_url_is_normalized_and_validated() -> None:
    assert normalize_base_url("https://example.test/gsplot/") == (
        "https://example.test/gsplot"
    )
    with pytest.raises(ValueError, match="HTTP"):
        normalize_base_url("/local/site")
    with pytest.raises(ValueError, match="query"):
        normalize_base_url("https://example.test/?version=dev")
