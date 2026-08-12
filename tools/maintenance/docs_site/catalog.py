"""Release catalog models and validation for the documentation site.

The catalog is deliberately implemented with the standard library only. The
catalog job is allowed to fetch public GitHub release metadata, while local and
pull-request checks can use the same typed model with a fixture.
"""

from __future__ import annotations

import json
import os
import re
import ssl
import subprocess
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

CATALOG_SCHEMA_VERSION = 1
DEFAULT_DOCUMENTATION_FLOOR = (0, 1, 1)
_TAG_PATTERN = re.compile(r"^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")
_POLICY_SCHEMA_VERSION = 1
_RELEASE_KEYS = {"tag", "version", "commit", "published_at", "url"}
_POLICY_DOCUMENT_KEYS = {"schema_version", "exclusions"}
_POLICY_KEYS = {
    "tag",
    "reason",
    "approved_at",
    "issue_url",
    "pull_request_url",
    "replacement_url",
}
_EXCLUSION_KEYS = {
    "tag",
    "reason",
    "url",
    "approved_at",
    "issue_url",
    "pull_request_url",
    "replacement_url",
}
_CATALOG_KEYS = {
    "schema_version",
    "main_commit",
    "stable_tag",
    "releases",
    "exclusions",
}


class CatalogError(ValueError):
    """Raised when release metadata cannot produce a safe catalog."""


@dataclass(frozen=True, slots=True)
class ExclusionPolicy:
    """A reviewed, public-safe policy for excluding one release."""

    tag: str
    reason: str
    approved_at: str
    issue_url: str | None = None
    pull_request_url: str | None = None
    replacement_url: str | None = None

    def to_mapping(self) -> dict[str, str | None]:
        """Return the tracked policy representation."""

        return {
            "tag": self.tag,
            "reason": self.reason,
            "approved_at": self.approved_at,
            "issue_url": self.issue_url,
            "pull_request_url": self.pull_request_url,
            "replacement_url": self.replacement_url,
        }


@dataclass(frozen=True, slots=True)
class ReleaseRecord:
    """One immutable documentation release and its source commit."""

    tag: str
    version: str
    commit: str
    published_at: str
    url: str

    def to_mapping(self) -> dict[str, str]:
        """Return the stable JSON representation of this release."""

        return {
            "tag": self.tag,
            "version": self.version,
            "commit": self.commit,
            "published_at": self.published_at,
            "url": self.url,
        }


@dataclass(frozen=True, slots=True)
class ExcludedRelease:
    """Public-safe reason why a fetched release is not in the build matrix."""

    tag: str
    reason: str
    url: str | None = None
    approved_at: str | None = None
    issue_url: str | None = None
    pull_request_url: str | None = None
    replacement_url: str | None = None

    def to_mapping(self) -> dict[str, str | None]:
        """Return the stable JSON representation of this exclusion."""

        return {
            "tag": self.tag,
            "reason": self.reason,
            "url": self.url,
            "approved_at": self.approved_at,
            "issue_url": self.issue_url,
            "pull_request_url": self.pull_request_url,
            "replacement_url": self.replacement_url,
        }


@dataclass(frozen=True, slots=True)
class ReleaseCatalog:
    """Schema-versioned release catalog consumed by docs build tooling."""

    main_commit: str
    stable_tag: str
    releases: tuple[ReleaseRecord, ...]
    exclusions: tuple[ExcludedRelease, ...] = ()
    schema_version: int = CATALOG_SCHEMA_VERSION

    def __post_init__(self) -> None:
        """Validate invariants even when a catalog is constructed directly."""

        _validate_sha(self.main_commit, "main_commit")
        if self.schema_version != CATALOG_SCHEMA_VERSION:
            raise CatalogError(
                f"unsupported catalog schema version: {self.schema_version}"
            )
        if not self.releases:
            raise CatalogError("catalog must contain at least one release")
        tags: set[str] = set()
        versions: set[str] = set()
        for release in self.releases:
            _validate_release_record(release)
            if release.tag in tags or release.version in versions:
                raise CatalogError("catalog contains duplicate release versions")
            tags.add(release.tag)
            versions.add(release.version)
        if (
            tuple(
                sorted(
                    self.releases,
                    key=lambda item: parse_release_tag(item.tag),
                    reverse=True,
                )
            )
            != self.releases
        ):
            raise CatalogError("catalog releases must be sorted newest first")
        if self.stable_tag != self.releases[0].tag:
            raise CatalogError("stable_tag must identify the highest release")
        if any(item.tag in tags for item in self.exclusions):
            raise CatalogError("a release cannot be both included and excluded")
        excluded_tags: set[str] = set()
        for item in self.exclusions:
            _validate_exclusion(item)
            if item.tag in excluded_tags:
                raise CatalogError("catalog contains duplicate exclusions")
            excluded_tags.add(item.tag)

    def to_mapping(self) -> dict[str, Any]:
        """Return a JSON-compatible, schema-validated mapping."""

        return {
            "schema_version": self.schema_version,
            "main_commit": self.main_commit,
            "stable_tag": self.stable_tag,
            "releases": [item.to_mapping() for item in self.releases],
            "exclusions": [item.to_mapping() for item in self.exclusions],
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ReleaseCatalog":
        """Validate and load a catalog mapping from JSON."""

        _require_exact_keys(value, _CATALOG_KEYS, "catalog")
        schema_version = value["schema_version"]
        if type(schema_version) is not int:
            raise CatalogError("catalog.schema_version must be an integer")
        releases_value = value["releases"]
        exclusions_value = value["exclusions"]
        if not isinstance(releases_value, list):
            raise CatalogError("catalog.releases must be a list")
        if not isinstance(exclusions_value, list):
            raise CatalogError("catalog.exclusions must be a list")
        releases = tuple(_release_from_mapping(item) for item in releases_value)
        exclusions = tuple(_exclusion_from_mapping(item) for item in exclusions_value)
        return cls(
            main_commit=_required_string(value, "main_commit", "catalog"),
            stable_tag=_required_string(value, "stable_tag", "catalog"),
            releases=releases,
            exclusions=exclusions,
            schema_version=schema_version,
        )


def parse_release_tag(tag: str) -> tuple[int, int, int]:
    """Parse a strict public release tag such as ``v0.3.0``."""

    if not isinstance(tag, str):
        raise CatalogError("release tag must be a string")
    match = _TAG_PATTERN.fullmatch(tag)
    if match is None:
        raise CatalogError(f"release tag is not strict SemVer: {tag!r}")
    components = tuple(int(component) for component in match.groups())
    return components[0], components[1], components[2]


def build_catalog(
    releases: Iterable[Mapping[str, Any]],
    *,
    main_commit: str,
    resolve_commit: Callable[[str], str],
    has_docs: Callable[[str], bool],
    documentation_floor: tuple[int, int, int] = DEFAULT_DOCUMENTATION_FLOOR,
    policy_exclusions: Mapping[str, ExclusionPolicy] | None = None,
    previous_release_tags: Iterable[str] | None = None,
) -> ReleaseCatalog:
    """Build a catalog from GitHub-like release payloads.

    Drafts, prereleases, malformed version tags, below-floor releases, and
    explicit policy exclusions are recorded as public-safe exclusions. A valid
    release at or above the floor with a missing ref or documentation tree
    fails closed because silently selecting an older stable release is unsafe.
    When a previous public manifest is supplied, every previously included
    immutable release must remain included or have an explicit retirement
    policy.
    """

    _validate_sha(main_commit, "main_commit")
    if len(documentation_floor) != 3 or any(
        type(component) is not int or component < 0 for component in documentation_floor
    ):
        raise CatalogError(
            "documentation_floor must contain three non-negative integers"
        )
    policy = dict(policy_exclusions or {})
    _validate_policy_mapping(policy, documentation_floor)
    previous_tags = set(previous_release_tags or ())
    for tag in previous_tags:
        version_tuple = parse_release_tag(tag)
        if version_tuple < documentation_floor:
            raise CatalogError(
                f"previous manifest release is below the documentation floor: {tag}"
            )
    exclusions: list[ExcludedRelease] = []
    included: list[ReleaseRecord] = []
    seen_input_tags: set[str] = set()
    seen_tags: set[str] = set()
    seen_versions: set[str] = set()
    applied_policy_tags: set[str] = set()

    for payload in releases:
        if not isinstance(payload, Mapping):
            raise CatalogError("GitHub release payload must be an object")
        tag = _required_string(payload, "tag_name", "release")
        if tag in seen_input_tags:
            raise CatalogError(f"duplicate release tag in API response: {tag}")
        seen_input_tags.add(tag)
        url = _optional_url(payload.get("html_url"), "release.html_url")
        draft = _required_bool(payload, "draft", "release")
        prerelease = _required_bool(payload, "prerelease", "release")
        if draft:
            exclusions.append(ExcludedRelease(tag=tag, reason="draft", url=url))
            continue
        if prerelease:
            exclusions.append(ExcludedRelease(tag=tag, reason="prerelease", url=url))
            continue
        try:
            version_tuple = parse_release_tag(tag)
        except CatalogError:
            exclusions.append(ExcludedRelease(tag=tag, reason="invalid-tag", url=url))
            continue
        version = ".".join(str(component) for component in version_tuple)
        if version_tuple < documentation_floor:
            exclusions.append(
                ExcludedRelease(tag=tag, reason="below-documentation-floor", url=url)
            )
            continue
        if tag in policy:
            exclusion = policy[tag]
            applied_policy_tags.add(tag)
            exclusions.append(
                ExcludedRelease(
                    tag=tag,
                    reason=exclusion.reason,
                    url=url,
                    approved_at=exclusion.approved_at,
                    issue_url=exclusion.issue_url,
                    pull_request_url=exclusion.pull_request_url,
                    replacement_url=exclusion.replacement_url,
                )
            )
            continue
        if tag in seen_tags or version in seen_versions:
            raise CatalogError(f"duplicate normalized release version: {tag}")
        if url is None:
            raise CatalogError(f"release {tag} has no public URL")
        published_at = _required_string(payload, "published_at", "release")
        _validate_timestamp(published_at, f"release {tag}.published_at")
        try:
            commit = resolve_commit(tag)
        except Exception as exc:  # noqa: BLE001 - convert unsafe detail to safe error
            raise CatalogError(f"release {tag} tag ref could not be resolved") from exc
        _validate_sha(commit, f"release {tag}.commit")
        try:
            docs_available = has_docs(commit)
        except Exception as exc:  # noqa: BLE001 - convert unsafe detail to safe error
            raise CatalogError(
                f"release {tag} documentation tree could not be checked"
            ) from exc
        if not docs_available:
            raise CatalogError(f"release {tag} has no required documentation tree")
        seen_tags.add(tag)
        seen_versions.add(version)
        included.append(
            ReleaseRecord(
                tag=tag,
                version=version,
                commit=commit.lower(),
                published_at=published_at,
                url=url,
            )
        )

    included_tags = {item.tag for item in included}
    missing_previous_tags = previous_tags - included_tags
    unreviewed_previous_tags = missing_previous_tags - set(policy)
    if unreviewed_previous_tags:
        raise CatalogError(
            "previous immutable release is missing without retirement policy: "
            + ", ".join(sorted(unreviewed_previous_tags, key=parse_release_tag))
        )

    unused_policy_tags = set(policy) - applied_policy_tags
    retired_policy_tags = unused_policy_tags & previous_tags
    for tag in sorted(retired_policy_tags, key=parse_release_tag, reverse=True):
        exclusion = policy[tag]
        exclusions.append(
            ExcludedRelease(
                tag=tag,
                reason=exclusion.reason,
                approved_at=exclusion.approved_at,
                issue_url=exclusion.issue_url,
                pull_request_url=exclusion.pull_request_url,
                replacement_url=exclusion.replacement_url,
            )
        )
    unresolved_policy_tags = unused_policy_tags - retired_policy_tags
    if unresolved_policy_tags:
        raise CatalogError(
            "release exclusion policy refers to unpublished or ineligible tags: "
            + ", ".join(sorted(unresolved_policy_tags))
        )

    included.sort(key=lambda item: parse_release_tag(item.tag), reverse=True)
    if not included:
        raise CatalogError("no eligible release remains at the documentation floor")
    return ReleaseCatalog(
        main_commit=main_commit.lower(),
        stable_tag=included[0].tag,
        releases=tuple(included),
        exclusions=tuple(exclusions),
    )


def resolve_git_tag(repo_root: Path, tag: str) -> str:
    """Resolve a validated tag to its commit without shell interpolation."""

    parse_release_tag(tag)
    result = subprocess.run(
        ["git", "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise CatalogError(f"tag ref is unavailable: {tag}")
    commit = result.stdout.strip()
    _validate_sha(commit, f"tag {tag}")
    return commit.lower()


def resolve_git_ref(repo_root: Path, ref: str = "HEAD") -> str:
    """Resolve a local Git ref to a full commit SHA."""

    if not ref or ref.startswith("-") or "\x00" in ref:
        raise CatalogError("invalid Git ref")
    result = subprocess.run(
        ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise CatalogError("Git ref could not be resolved")
    commit = result.stdout.strip()
    _validate_sha(commit, f"Git ref {ref}")
    return commit.lower()


def source_has_docs(repo_root: Path, commit: str) -> bool:
    """Return whether a commit contains the required Sphinx source files."""

    _validate_sha(commit, "commit")
    for relative_path in ("docs/conf.py", "docs/index.md"):
        result = subprocess.run(
            ["git", "cat-file", "-e", f"{commit}:{relative_path}"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return False
    return True


def fetch_github_releases(
    repository: str,
    *,
    token: str | None = None,
    opener: Callable[..., Any] = urlopen,
) -> list[Mapping[str, Any]]:
    """Fetch all public GitHub Releases with bounded, paginated requests."""

    if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is None:
        raise CatalogError("repository must use the OWNER/NAME form")
    owner, name = repository.split("/", maxsplit=1)
    releases: list[Mapping[str, Any]] = []
    for page in range(1, 1001):
        url = (
            f"https://api.github.com/repos/{owner}/{name}/releases"
            f"?per_page=100&page={page}"
        )
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "gsplot-docs-catalog",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = Request(url, headers=headers, method="GET")
        try:
            with opener(request, timeout=30, context=_ssl_context()) as response:
                status = getattr(response, "status", 200)
                raw = response.read()
        except (HTTPError, URLError, OSError) as exc:
            raise CatalogError(
                f"GitHub Releases API request failed on page {page}"
            ) from exc
        if status != 200:
            raise CatalogError(f"GitHub Releases API returned HTTP {status}")
        try:
            value = json.loads(raw)
        except (TypeError, json.JSONDecodeError) as exc:
            raise CatalogError(
                f"GitHub Releases API returned invalid JSON on page {page}"
            ) from exc
        if not isinstance(value, list):
            raise CatalogError("GitHub Releases API response must be a list")
        for item in value:
            if not isinstance(item, Mapping):
                raise CatalogError("GitHub Releases API returned a non-object release")
            releases.append(item)
        if len(value) < 100:
            return releases
    raise CatalogError("GitHub Releases API pagination exceeded the safe limit")


def fetch_public_manifest_release_tags(
    manifest_url: str,
    *,
    opener: Callable[..., Any] = urlopen,
) -> frozenset[str] | None:
    """Fetch immutable release tags from the previously published manifest.

    A missing manifest is expected on the first deployment. Any other network,
    HTTP, schema, or tag-validation failure is fatal so a catalog job cannot
    silently deploy a version that was removed from the public site.
    """

    _validate_url(manifest_url, "previous manifest URL")
    request = Request(
        manifest_url,
        headers={
            "Accept": "application/json",
            "User-Agent": "gsplot-docs-catalog",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=30, context=_ssl_context()) as response:
            status = getattr(response, "status", 200)
            if status in {404, 410}:
                return None
            if status != 200:
                raise CatalogError(
                    f"previous documentation manifest returned HTTP {status}"
                )
            raw = response.read()
    except HTTPError as exc:
        if exc.code in {404, 410}:
            return None
        raise CatalogError("previous documentation manifest request failed") from exc
    except (URLError, OSError) as exc:
        raise CatalogError("previous documentation manifest request failed") from exc
    try:
        value = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise CatalogError("previous documentation manifest is invalid JSON") from exc
    if not isinstance(value, Mapping):
        raise CatalogError("previous documentation manifest must be an object")
    builds = value.get("builds")
    if not isinstance(builds, list):
        raise CatalogError("previous documentation manifest has no build list")
    release_tags: set[str] = set()
    for item in builds:
        if not isinstance(item, Mapping) or item.get("channel") != "release":
            continue
        tag = item.get("source_ref")
        if not isinstance(tag, str):
            raise CatalogError("previous documentation manifest has an invalid release")
        parse_release_tag(tag)
        release_tags.add(tag)
    if not release_tags:
        raise CatalogError("previous documentation manifest has no immutable releases")
    return frozenset(release_tags)


def _ssl_context() -> ssl.SSLContext:
    """Return a verifying TLS context with a portable public CA bundle."""

    try:
        import certifi
    except ImportError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


def load_catalog(path: Path) -> ReleaseCatalog:
    """Load and validate a catalog JSON file."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError("catalog JSON could not be read") from exc
    if not isinstance(value, Mapping):
        raise CatalogError("catalog JSON must contain an object")
    return ReleaseCatalog.from_mapping(value)


def write_catalog(catalog: ReleaseCatalog, path: Path) -> None:
    """Write a catalog atomically as deterministic UTF-8 JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        temporary.write_text(
            json.dumps(catalog.to_mapping(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
    except OSError as exc:
        raise CatalogError("catalog JSON could not be written") from exc
    finally:
        temporary.unlink(missing_ok=True)


def _release_from_mapping(value: Any) -> ReleaseRecord:
    if not isinstance(value, Mapping):
        raise CatalogError("catalog release must be an object")
    _require_exact_keys(value, _RELEASE_KEYS, "catalog release")
    tag = _required_string(value, "tag", "catalog release")
    version_tuple = parse_release_tag(tag)
    version = _required_string(value, "version", "catalog release")
    expected_version = ".".join(str(component) for component in version_tuple)
    if version != expected_version:
        raise CatalogError(f"catalog release version disagrees with tag: {tag}")
    commit = _required_string(value, "commit", "catalog release")
    _validate_sha(commit, f"catalog release {tag}.commit")
    published_at = _required_string(value, "published_at", "catalog release")
    _validate_timestamp(published_at, f"catalog release {tag}.published_at")
    url = _required_string(value, "url", "catalog release")
    _validate_url(url, f"catalog release {tag}.url")
    return ReleaseRecord(
        tag=tag,
        version=version,
        commit=commit.lower(),
        published_at=published_at,
        url=url,
    )


def _exclusion_from_mapping(value: Any) -> ExcludedRelease:
    if not isinstance(value, Mapping):
        raise CatalogError("catalog exclusion must be an object")
    _require_exact_keys(value, _EXCLUSION_KEYS, "catalog exclusion")
    tag = _required_string(value, "tag", "catalog exclusion")
    reason = _required_string(value, "reason", "catalog exclusion")
    url = _optional_url(value.get("url"), "catalog exclusion.url")
    approved_at = _optional_string(value.get("approved_at"), "catalog exclusion")
    issue_url = _optional_url(value.get("issue_url"), "catalog exclusion.issue_url")
    pull_request_url = _optional_url(
        value.get("pull_request_url"), "catalog exclusion.pull_request_url"
    )
    replacement_url = _optional_url(
        value.get("replacement_url"), "catalog exclusion.replacement_url"
    )
    exclusion = ExcludedRelease(
        tag=tag,
        reason=reason,
        url=url,
        approved_at=approved_at,
        issue_url=issue_url,
        pull_request_url=pull_request_url,
        replacement_url=replacement_url,
    )
    _validate_exclusion(exclusion)
    return exclusion


def _validate_release_record(release: ReleaseRecord) -> None:
    version_tuple = parse_release_tag(release.tag)
    if release.version != ".".join(str(component) for component in version_tuple):
        raise CatalogError(f"release version disagrees with tag: {release.tag}")
    _validate_sha(release.commit, f"release {release.tag}.commit")
    _validate_timestamp(release.published_at, f"release {release.tag}.published_at")
    _validate_url(release.url, f"release {release.tag}.url")


def _validate_exclusion(item: ExcludedRelease) -> None:
    if not item.tag or not item.reason.strip():
        raise CatalogError("catalog exclusions require a tag and reason")
    if item.url is not None:
        _validate_url(item.url, f"catalog exclusion {item.tag}.url")
    metadata_present = any(
        value is not None
        for value in (
            item.approved_at,
            item.issue_url,
            item.pull_request_url,
            item.replacement_url,
        )
    )
    if not metadata_present:
        return
    if item.approved_at is None:
        raise CatalogError(f"catalog exclusion {item.tag} is missing its approval date")
    try:
        date.fromisoformat(item.approved_at)
    except ValueError as exc:
        raise CatalogError(
            f"catalog exclusion {item.tag}.approved_at must be an ISO date"
        ) from exc
    if item.issue_url is None and item.pull_request_url is None:
        raise CatalogError(
            f"catalog exclusion {item.tag} needs an Issue or pull request URL"
        )
    for field_name, value in (
        ("issue_url", item.issue_url),
        ("pull_request_url", item.pull_request_url),
        ("replacement_url", item.replacement_url),
    ):
        if value is not None:
            _validate_url(value, f"catalog exclusion {item.tag}.{field_name}")


def load_policy(path: Path) -> dict[str, ExclusionPolicy]:
    """Load and validate a tracked release-exclusion policy document."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError("release exclusion policy could not be read") from exc
    if not isinstance(value, Mapping):
        raise CatalogError("release exclusion policy must contain an object")
    _require_exact_keys(value, _POLICY_DOCUMENT_KEYS, "release exclusion policy")
    schema_version = value["schema_version"]
    if type(schema_version) is not int or schema_version != _POLICY_SCHEMA_VERSION:
        raise CatalogError("unsupported release exclusion policy schema version")
    exclusions = value["exclusions"]
    if not isinstance(exclusions, list):
        raise CatalogError("release exclusion policy exclusions must be a list")
    result: dict[str, ExclusionPolicy] = {}
    for item in exclusions:
        if not isinstance(item, Mapping):
            raise CatalogError("release exclusion policy entry must be an object")
        _require_exact_keys(item, _POLICY_KEYS, "release exclusion policy entry")
        policy = ExclusionPolicy(
            tag=_required_string(item, "tag", "release exclusion policy entry"),
            reason=_required_string(item, "reason", "release exclusion policy entry"),
            approved_at=_required_string(
                item, "approved_at", "release exclusion policy entry"
            ),
            issue_url=_optional_url(
                item.get("issue_url"), "release exclusion policy issue_url"
            ),
            pull_request_url=_optional_url(
                item.get("pull_request_url"),
                "release exclusion policy pull_request_url",
            ),
            replacement_url=_optional_url(
                item.get("replacement_url"),
                "release exclusion policy replacement_url",
            ),
        )
        _validate_policy(policy)
        if policy.tag in result:
            raise CatalogError(f"duplicate policy exclusion: {policy.tag}")
        result[policy.tag] = policy
    return result


def _required_string(value: Mapping[str, Any], key: str, context: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result.strip():
        raise CatalogError(f"{context}.{key} must be a non-empty string")
    return result.strip()


def _required_bool(value: Mapping[str, Any], key: str, context: str) -> bool:
    result = value.get(key)
    if type(result) is not bool:
        raise CatalogError(f"{context}.{key} must be a boolean")
    return result


def _optional_url(value: Any, context: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(f"{context} must be a URL or null")
    url = value.strip()
    _validate_url(url, context)
    return url


def _optional_string(value: Any, context: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(f"{context} must be a non-empty string or null")
    return value.strip()


def _validate_url(value: str, context: str) -> None:
    parsed = urlparse(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise CatalogError(f"{context} must be an absolute HTTP(S) URL")


def _validate_timestamp(value: str, context: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CatalogError(f"{context} must be an ISO-8601 timestamp") from exc


def _validate_sha(value: str, context: str) -> None:
    if not isinstance(value, str) or _SHA_PATTERN.fullmatch(value) is None:
        raise CatalogError(f"{context} must be a full commit SHA")


def _validate_policy(policy: ExclusionPolicy) -> None:
    parse_release_tag(policy.tag)
    if not policy.reason.strip():
        raise CatalogError(f"empty policy exclusion reason for {policy.tag}")
    try:
        date.fromisoformat(policy.approved_at)
    except ValueError as exc:
        raise CatalogError(
            f"policy exclusion {policy.tag}.approved_at must be an ISO date"
        ) from exc
    if policy.issue_url is None and policy.pull_request_url is None:
        raise CatalogError(
            f"policy exclusion {policy.tag} needs an Issue or pull request URL"
        )
    for field_name, value in (
        ("issue_url", policy.issue_url),
        ("pull_request_url", policy.pull_request_url),
        ("replacement_url", policy.replacement_url),
    ):
        if value is not None:
            _validate_url(value, f"policy exclusion {policy.tag}.{field_name}")


def _validate_policy_mapping(
    policy: Mapping[str, ExclusionPolicy],
    documentation_floor: tuple[int, int, int],
) -> None:
    for key, value in policy.items():
        if not isinstance(key, str) or not isinstance(value, ExclusionPolicy):
            raise CatalogError("release exclusion policy has an invalid entry")
        _validate_policy(value)
        if key != value.tag:
            raise CatalogError("release exclusion policy key disagrees with its tag")
        if parse_release_tag(value.tag) < documentation_floor:
            raise CatalogError(
                f"policy exclusion is below the documentation floor: {value.tag}"
            )


def _require_exact_keys(
    value: Mapping[str, Any], expected: set[str], context: str
) -> None:
    keys = set(value)
    if keys != expected:
        missing = sorted(expected - keys)
        extra = sorted(keys - expected)
        details = []
        if missing:
            details.append(f"missing={missing}")
        if extra:
            details.append(f"unexpected={extra}")
        raise CatalogError(f"{context} schema mismatch ({', '.join(details)})")
