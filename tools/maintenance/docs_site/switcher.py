"""Version-switcher generation and semantic validation."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .catalog import ReleaseCatalog, _validate_url

DEFAULT_BASE_URL = "https://soichiroyamane.github.io/gsplot"
_SWITCHER_KEYS = {"name", "version", "url", "preferred"}


def normalize_base_url(base_url: str) -> str:
    """Validate and normalize the public site base URL."""

    if not isinstance(base_url, str) or not base_url.strip():
        raise ValueError("base URL must be a non-empty string")
    normalized = base_url.strip().rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("base URL must be an absolute HTTP(S) URL")
    if parsed.query or parsed.fragment:
        raise ValueError("base URL must not contain a query or fragment")
    _validate_url(normalized, "base URL")
    return normalized


def generate_switcher(
    catalog: ReleaseCatalog,
    *,
    base_url: str = DEFAULT_BASE_URL,
) -> list[dict[str, object]]:
    """Generate switcher entries from the same catalog used for builds."""

    base = normalize_base_url(base_url)
    entries: list[dict[str, object]] = [
        {
            "name": "dev",
            "version": "dev",
            "url": f"{base}/dev/",
            "preferred": False,
        }
    ]
    for release in catalog.releases:
        is_stable = release.tag == catalog.stable_tag
        entries.append(
            {
                "name": f"{release.tag} (stable)" if is_stable else release.tag,
                "version": release.tag,
                "url": f"{base}/stable/" if is_stable else f"{base}/{release.tag}/",
                "preferred": is_stable,
            }
        )
    validate_switcher(entries, catalog, base_url=base)
    return entries


def validate_switcher(
    value: Sequence[Mapping[str, Any]],
    catalog: ReleaseCatalog,
    *,
    base_url: str = DEFAULT_BASE_URL,
) -> None:
    """Validate switcher schema and its one-to-one catalog mapping."""

    base = normalize_base_url(base_url)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError("switcher data must be a list")
    expected = generate_switcher_without_validation(catalog, base)
    if len(value) != len(expected):
        raise ValueError("switcher entry count does not match the catalog")
    seen_versions: set[str] = set()
    seen_urls: set[str] = set()
    preferred_count = 0
    for index, entry in enumerate(value):
        if not isinstance(entry, Mapping):
            raise ValueError(f"switcher entry {index} must be an object")
        if set(entry) != _SWITCHER_KEYS:
            raise ValueError(f"switcher entry {index} has an invalid schema")
        if not isinstance(entry["name"], str) or not isinstance(entry["version"], str):
            raise ValueError(f"switcher entry {index} has invalid text fields")
        if not isinstance(entry["url"], str) or type(entry["preferred"]) is not bool:
            raise ValueError(f"switcher entry {index} has invalid URL or boolean")
        version = entry["version"]
        url = entry["url"]
        if version in seen_versions or url in seen_urls:
            raise ValueError("switcher contains duplicate versions or URLs")
        seen_versions.add(version)
        seen_urls.add(url)
        if entry["preferred"]:
            preferred_count += 1
    if preferred_count != 1:
        raise ValueError("switcher must contain exactly one preferred entry")
    if list(value) != expected:
        raise ValueError("switcher entries do not match the release catalog")


def load_switcher(path: Path) -> list[dict[str, object]]:
    """Load a switcher JSON array without weakening JSON type validation."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("switcher JSON could not be read") from exc
    if not isinstance(value, list):
        raise ValueError("switcher JSON must contain a list")
    return value


def write_switcher(entries: Sequence[Mapping[str, Any]], path: Path) -> None:
    """Write validated switcher data atomically as deterministic JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        temporary.write_text(
            json.dumps(list(entries), indent=2) + "\n", encoding="utf-8"
        )
        temporary.replace(path)
    except OSError as exc:
        raise ValueError("switcher JSON could not be written") from exc
    finally:
        temporary.unlink(missing_ok=True)


def generate_switcher_without_validation(
    catalog: ReleaseCatalog, base_url: str
) -> list[dict[str, object]]:
    """Build expected entries for the validator without recursive validation."""

    entries: list[dict[str, object]] = [
        {
            "name": "dev",
            "version": "dev",
            "url": f"{base_url}/dev/",
            "preferred": False,
        }
    ]
    entries.extend(
        {
            "name": (
                f"{release.tag} (stable)"
                if release.tag == catalog.stable_tag
                else release.tag
            ),
            "version": release.tag,
            "url": (
                f"{base_url}/stable/"
                if release.tag == catalog.stable_tag
                else f"{base_url}/{release.tag}/"
            ),
            "preferred": release.tag == catalog.stable_tag,
        }
        for release in catalog.releases
    )
    return entries
