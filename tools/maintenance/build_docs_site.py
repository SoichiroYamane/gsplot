"""Command-line entry point for the isolated documentation site builder."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.maintenance.docs_site.orchestrator import BuildError, build_site
from tools.maintenance.docs_site.switcher import DEFAULT_BASE_URL


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build the gsplot versioned documentation site from a catalog."
    )
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--python", dest="python_executable", default=sys.executable)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Build the site and report a public-safe summary."""

    args = _parser().parse_args(argv)
    try:
        manifest = build_site(
            args.catalog,
            args.output,
            repo_root=args.repo_root,
            python_executable=args.python_executable,
            base_url=args.base_url,
        )
    except BuildError as exc:
        print(f"{exc}", file=sys.stderr)
        return 1
    print(
        "documentation site generated: "
        f"stable={manifest.stable_tag}, "
        f"builds={len(manifest.builds)}, "
        f"files={manifest.file_count}, "
        f"bytes={manifest.uncompressed_bytes}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
