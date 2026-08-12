"""Typed helpers for the versioned documentation site."""

from .catalog import (
    CatalogError,
    ExcludedRelease,
    ExclusionPolicy,
    ReleaseCatalog,
    ReleaseRecord,
    build_catalog,
    fetch_github_releases,
    load_policy,
    parse_release_tag,
    resolve_git_ref,
    resolve_git_tag,
    source_has_docs,
)
from .switcher import (
    DEFAULT_BASE_URL,
    generate_switcher,
    load_switcher,
    normalize_base_url,
    validate_switcher,
    write_switcher,
)

__all__ = [
    "CatalogError",
    "ExclusionPolicy",
    "ExcludedRelease",
    "ReleaseCatalog",
    "ReleaseRecord",
    "build_catalog",
    "fetch_github_releases",
    "load_policy",
    "parse_release_tag",
    "resolve_git_ref",
    "resolve_git_tag",
    "source_has_docs",
    "DEFAULT_BASE_URL",
    "generate_switcher",
    "load_switcher",
    "normalize_base_url",
    "validate_switcher",
    "write_switcher",
]
