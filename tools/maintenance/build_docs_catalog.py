"""Build the public documentation release catalog and version switcher."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.maintenance.docs_site.catalog import (
    CatalogError,
    build_catalog,
    fetch_github_releases,
    fetch_public_manifest_release_tags,
    load_policy,
    parse_release_tag,
    resolve_git_ref,
    resolve_git_tag,
    source_has_docs,
    write_catalog,
)
from tools.maintenance.docs_site.switcher import (
    DEFAULT_BASE_URL,
    generate_switcher,
    write_switcher,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a validated gsplot documentation release catalog."
    )
    parser.add_argument(
        "--repository",
        default="SoichiroYamane/gsplot",
        help="GitHub OWNER/NAME repository used by the live catalog job.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Checkout containing the release tags and documentation trees.",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        help="Local GitHub Releases JSON fixture; disables network access.",
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=Path("docs/project/website-release-policy.json"),
        help="Tracked JSON release-exclusion policy document.",
    )
    parser.add_argument(
        "--main-commit",
        help="Full main commit SHA; defaults to HEAD in --repo-root.",
    )
    parser.add_argument(
        "--floor",
        default="v0.1.1",
        help="Minimum immutable documentation tag (default: v0.1.1).",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Public site base URL used by switcher entries.",
    )
    parser.add_argument(
        "--previous-manifest-url",
        help=(
            "Public manifest URL used to prevent silent immutable-release "
            "removal. A 404 is treated as a first deployment."
        ),
    )
    parser.add_argument(
        "--candidate-tag",
        help=(
            "Explicit unpublished tag to validate as a release candidate. "
            "The candidate is never deployed by the Pages workflow."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Catalog JSON output path.",
    )
    parser.add_argument(
        "--switcher-output",
        type=Path,
        required=True,
        help="Version switcher JSON output path.",
    )
    parser.add_argument(
        "--token-env",
        default="GITHUB_TOKEN",
        help="Environment variable for the read-only catalog API token.",
    )
    return parser


def _load_fixture(path: Path) -> list[dict[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError("release fixture could not be read") from exc
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise CatalogError("release fixture must contain a list of objects")
    return value


def main(argv: list[str] | None = None) -> int:
    """Build and write the catalog and switcher, returning a process status."""

    args = _parser().parse_args(argv)
    try:
        repo_root = args.repo_root.resolve()
        floor = parse_release_tag(args.floor)
        main_commit = args.main_commit or resolve_git_ref(repo_root)
        policy_path = args.policy
        if not policy_path.is_absolute():
            policy_path = repo_root / policy_path
        policy = load_policy(policy_path)
        releases: Iterable[Mapping[str, Any]]
        if args.fixture is not None:
            if args.candidate_tag:
                raise CatalogError("--candidate-tag cannot be combined with --fixture")
            releases = _load_fixture(args.fixture)
        else:
            fetched_releases = list(
                fetch_github_releases(
                    args.repository,
                    token=os.environ.get(args.token_env),
                )
            )
            if args.candidate_tag:
                parse_release_tag(args.candidate_tag)
                if any(
                    item.get("tag_name") == args.candidate_tag
                    for item in fetched_releases
                    if isinstance(item, Mapping)
                ):
                    raise CatalogError(
                        "--candidate-tag is already a published release; "
                        "omit it for a normal catalog build"
                    )
                fetched_releases.append(
                    {
                        "tag_name": args.candidate_tag,
                        "draft": False,
                        "prerelease": False,
                        "published_at": datetime.now(timezone.utc)
                        .replace(microsecond=0)
                        .isoformat()
                        .replace("+00:00", "Z"),
                        "html_url": (
                            f"https://github.com/{args.repository}/releases/tag/"
                            f"{args.candidate_tag}"
                        ),
                    }
                )
            releases = fetched_releases
        previous_release_tags = None
        if args.previous_manifest_url and not args.candidate_tag:
            previous_release_tags = fetch_public_manifest_release_tags(
                args.previous_manifest_url
            )
        catalog = build_catalog(
            releases,
            main_commit=main_commit,
            resolve_commit=lambda tag: resolve_git_tag(repo_root, tag),
            has_docs=lambda commit: source_has_docs(repo_root, commit),
            documentation_floor=floor,
            policy_exclusions=policy,
            previous_release_tags=previous_release_tags,
        )
        write_catalog(catalog, args.output)
        write_switcher(
            generate_switcher(catalog, base_url=args.base_url), args.switcher_output
        )
    except (CatalogError, ValueError, OSError) as exc:
        print(f"documentation catalog failed: {exc}", file=sys.stderr)
        return 1

    print(
        "documentation catalog generated: "
        f"stable={catalog.stable_tag}, "
        f"releases={len(catalog.releases)}, "
        f"exclusions={len(catalog.exclusions)}"
    )
    for exclusion in catalog.exclusions:
        print(f"documentation catalog exclusion: {exclusion.tag} ({exclusion.reason})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
