"""Tests for the typed documentation release catalog."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.maintenance.docs_site.catalog import (
    CatalogError,
    ExclusionPolicy,
    ReleaseCatalog,
    build_catalog,
    fetch_github_releases,
    load_catalog,
    load_policy,
    parse_release_tag,
    write_catalog,
)

MAIN_SHA = "a" * 40
COMMITS = {
    "v0.3.0": "b" * 40,
    "v0.2.0": "c" * 40,
}


def _release(
    tag: str,
    *,
    draft: bool = False,
    prerelease: bool = False,
    url: str | None = None,
) -> dict[str, object]:
    return {
        "tag_name": tag,
        "draft": draft,
        "prerelease": prerelease,
        "published_at": "2026-08-11T00:00:00Z",
        "html_url": url
        or f"https://github.com/SoichiroYamane/gsplot/releases/tag/{tag}",
    }


def _build(payloads: list[dict[str, object]]) -> ReleaseCatalog:
    return build_catalog(
        payloads,
        main_commit=MAIN_SHA,
        resolve_commit=lambda tag: COMMITS[tag],
        has_docs=lambda commit: commit in COMMITS.values(),
    )


def test_parse_release_tag_rejects_non_strict_versions() -> None:
    assert parse_release_tag("v0.3.0") == (0, 3, 0)
    with pytest.raises(CatalogError):
        parse_release_tag("0.3.0")
    with pytest.raises(CatalogError):
        parse_release_tag("v01.3.0")
    with pytest.raises(CatalogError):
        parse_release_tag("v0.3.0-rc1")


def test_build_catalog_filters_and_sorts_release_payloads() -> None:
    catalog = _build(
        [
            _release("v0.2.0"),
            _release("v0.3.1", draft=True),
            _release("v0.3.0"),
            _release("v0.4.0-rc1", prerelease=True),
            _release("v0.1.0"),
            _release("not-a-version"),
        ]
    )

    assert catalog.stable_tag == "v0.3.0"
    assert [item.tag for item in catalog.releases] == ["v0.3.0", "v0.2.0"]
    assert [item.reason for item in catalog.exclusions] == [
        "draft",
        "prerelease",
        "below-documentation-floor",
        "invalid-tag",
    ]
    assert catalog.main_commit == MAIN_SHA
    assert all(exclusion.approved_at is None for exclusion in catalog.exclusions)


def test_build_catalog_records_reviewed_policy_metadata() -> None:
    policy = ExclusionPolicy(
        tag="v0.2.0",
        reason="Historical source cannot be built by the supported toolchain.",
        approved_at="2026-08-12",
        issue_url="https://github.com/SoichiroYamane/gsplot/issues/174",
        pull_request_url="https://github.com/SoichiroYamane/gsplot/pull/175",
        replacement_url="https://soichiroyamane.github.io/gsplot/stable/",
    )

    catalog = build_catalog(
        [_release("v0.2.0"), _release("v0.3.0")],
        main_commit=MAIN_SHA,
        resolve_commit=lambda tag: COMMITS[tag],
        has_docs=lambda commit: commit in COMMITS.values(),
        policy_exclusions={policy.tag: policy},
    )

    exclusion = next(item for item in catalog.exclusions if item.tag == "v0.2.0")
    assert exclusion.reason == policy.reason
    assert exclusion.approved_at == policy.approved_at
    assert exclusion.issue_url == policy.issue_url
    assert exclusion.pull_request_url == policy.pull_request_url
    assert exclusion.replacement_url == policy.replacement_url
    assert [item.tag for item in catalog.releases] == ["v0.3.0"]


def test_policy_loader_requires_public_approval_metadata(tmp_path: Path) -> None:
    output = tmp_path / "policy.json"
    output.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "exclusions": [
                    {
                        "tag": "v0.2.0",
                        "reason": "reason",
                        "approved_at": "2026-08-12",
                        "issue_url": None,
                        "pull_request_url": None,
                        "replacement_url": None,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(CatalogError, match="Issue or pull request"):
        load_policy(output)


def test_policy_loader_round_trip(tmp_path: Path) -> None:
    output = tmp_path / "policy.json"
    output.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "exclusions": [
                    {
                        "tag": "v0.2.0",
                        "reason": "reason",
                        "approved_at": "2026-08-12",
                        "issue_url": "https://github.com/SoichiroYamane/gsplot/issues/174",
                        "pull_request_url": None,
                        "replacement_url": None,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    policy = load_policy(output)

    assert policy["v0.2.0"].approved_at == "2026-08-12"


def test_policy_must_match_a_published_eligible_release() -> None:
    policy = ExclusionPolicy(
        tag="v0.2.0",
        reason="reason",
        approved_at="2026-08-12",
        issue_url="https://github.com/SoichiroYamane/gsplot/issues/174",
    )

    with pytest.raises(CatalogError, match="unpublished or ineligible"):
        build_catalog(
            [_release("v0.3.0")],
            main_commit=MAIN_SHA,
            resolve_commit=lambda tag: COMMITS[tag],
            has_docs=lambda commit: commit in COMMITS.values(),
            policy_exclusions={policy.tag: policy},
        )


def test_catalog_round_trip_is_schema_valid(tmp_path: Path) -> None:
    catalog = _build([_release("v0.3.0")])
    output = tmp_path / "catalog.json"

    write_catalog(catalog, output)

    assert load_catalog(output) == catalog
    assert json.loads(output.read_text(encoding="utf-8"))["schema_version"] == 1


def test_catalog_rejects_duplicate_versions() -> None:
    with pytest.raises(CatalogError, match="duplicate"):
        _build([_release("v0.3.0"), _release("v0.3.0")])


def test_catalog_fails_closed_when_release_ref_is_missing() -> None:
    with pytest.raises(CatalogError, match="tag ref"):
        build_catalog(
            [_release("v0.3.0")],
            main_commit=MAIN_SHA,
            resolve_commit=lambda tag: (_ for _ in ()).throw(KeyError(tag)),
            has_docs=lambda commit: True,
        )


def test_catalog_fails_closed_when_docs_are_missing() -> None:
    with pytest.raises(CatalogError, match="documentation tree"):
        build_catalog(
            [_release("v0.3.0")],
            main_commit=MAIN_SHA,
            resolve_commit=lambda tag: COMMITS["v0.3.0"],
            has_docs=lambda commit: False,
        )


def test_catalog_rejects_schema_mutation(tmp_path: Path) -> None:
    catalog = _build([_release("v0.3.0")])
    output = tmp_path / "catalog.json"
    write_catalog(catalog, output)
    value = json.loads(output.read_text(encoding="utf-8"))
    value["unexpected"] = True
    output.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(CatalogError, match="schema mismatch"):
        load_catalog(output)


def test_catalog_rejects_url_with_embedded_credentials() -> None:
    with pytest.raises(CatalogError, match="absolute HTTP"):
        _build([_release("v0.3.0", url="https://user:password@example.test/release")])


class _Response:
    status = 200

    def __init__(self, value: object) -> None:
        self._value = value

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._value).encode("utf-8")


def test_fetch_github_releases_paginates_without_exposing_authentication() -> None:
    requests: list[tuple[str, dict[str, str]]] = []

    def opener(request, *, timeout, context):
        requests.append((request.full_url, dict(request.header_items())))
        if "page=1" in request.full_url:
            return _Response([_release("v0.3.0")])
        return _Response([])

    releases = fetch_github_releases(
        "SoichiroYamane/gsplot", token="public-test-token", opener=opener
    )

    assert len(releases) == 1
    assert requests[0][0].endswith("per_page=100&page=1")
    assert "Authorization" in requests[0][1]
