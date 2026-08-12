"""Print a complete JSON inventory of the current public API boundary.

The inventory combines the root ``__all__``, lazy canonical and legacy
manifests, direct metadata attributes, and compatibility module paths recorded
in the migration guide. It is read-only and writes only JSON to standard
output.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any


def _kind(value: Any) -> str:
    """Return a stable, small category for an inspected public value."""

    if inspect.isclass(value):
        return "class"
    if inspect.isfunction(value):
        return "function"
    if inspect.ismodule(value):
        return "module"
    if callable(value):
        return "callable"
    return type(value).__name__


def _signature(value: Any) -> str | None:
    """Return a signature when Python exposes one for ``value``."""

    try:
        return str(inspect.signature(value))
    except (TypeError, ValueError):
        return None


def _manifest(value: object) -> dict[str, dict[str, str]]:
    """Normalize one finite lazy-export manifest for JSON output."""

    if not isinstance(value, dict):
        raise TypeError("lazy export manifest must be a dictionary")
    result: dict[str, dict[str, str]] = {}
    for name, target in value.items():
        if not (
            isinstance(name, str)
            and isinstance(target, tuple)
            and len(target) == 2
            and all(isinstance(part, str) for part in target)
        ):
            raise TypeError("lazy export manifest contains an invalid entry")
        result[name] = {"module": target[0], "attribute": target[1]}
    return dict(sorted(result.items()))


def _documented_compatibility_paths(path: Path) -> list[str]:
    """Read compatibility paths from first cells in the migration table."""

    paths: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if not cells:
            continue
        value = cells[0].strip("`")
        if value.startswith("gsplot.") and "(" not in value:
            paths.add(value)
    return sorted(paths)


def collect(
    module_name: str = "gsplot", migration_doc: Path | None = None
) -> dict[str, Any]:
    """Collect every reviewed root and documented compatibility surface."""

    module = importlib.import_module(module_name)
    names: Iterable[str] = getattr(module, "__all__", ())
    exports: list[dict[str, str | None]] = []

    for name in names:
        value = getattr(module, name)
        exports.append(
            {
                "name": name,
                "kind": _kind(value),
                "module": getattr(value, "__module__", None),
                "qualname": getattr(value, "__qualname__", None),
                "signature": _signature(value),
            }
        )

    boundary = importlib.import_module(f"{module_name}._compat.root")
    if migration_doc is None:
        candidate = (
            Path(__file__).resolve().parents[2] / "docs/project/api-migration.md"
        )
        migration_doc = candidate if candidate.is_file() else None
    documented_paths = (
        _documented_compatibility_paths(migration_doc)
        if migration_doc is not None
        else []
    )
    metadata = [name for name in ("__commit__", "__version__") if hasattr(module, name)]

    return {
        "canonical_manifest": _manifest(boundary._CANONICAL_EXPORTS),
        "documented_compatibility_paths": documented_paths,
        "exports": exports,
        "legacy_discoverable": list(boundary.legacy_names()),
        "legacy_manifest": _manifest(boundary._LEGACY_EXPORTS),
        "metadata_attributes": metadata,
        "module": module_name,
        "root_all": list(names),
    }


def main() -> None:
    """Parse arguments and print the inventory as deterministic JSON."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--module",
        default="gsplot",
        help="package module to inspect (default: gsplot)",
    )
    parser.add_argument(
        "--migration-doc",
        type=Path,
        help="migration matrix used to inventory documented compatibility paths",
    )
    args = parser.parse_args()
    print(
        json.dumps(
            collect(args.module, migration_doc=args.migration_doc),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
