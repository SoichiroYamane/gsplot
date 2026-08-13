"""Check the reviewed public API contract against the current package.

The tracked JSON fixture is intentionally complete: it records canonical and
compatibility exports, signatures, defaults, annotations, lazy targets, and
docstring fingerprints.  Updating it is an explicit API-review action rather
than an incidental test rewrite.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

if __package__:
    from .collect_public_api import collect
else:
    from collect_public_api import collect

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = PROJECT_ROOT / "tests/fixtures/reform/public-api-v1.json"
MIGRATION_PATH = PROJECT_ROOT / "docs/project/api-migration.md"


def render_contract() -> str:
    """Return the current complete contract as deterministic JSON."""

    return (
        json.dumps(
            collect(migration_doc=MIGRATION_PATH),
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def contract_is_current(path: Path = CONTRACT_PATH) -> bool:
    """Return whether ``path`` exactly matches the current API boundary."""

    try:
        expected = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    return expected == render_contract()


def update_contract(path: Path = CONTRACT_PATH) -> None:
    """Atomically replace ``path`` with the current reviewed contract."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        text=True,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(render_contract())
        temporary_path.replace(path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def main() -> int:
    """Check the contract or intentionally update the tracked fixture."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update",
        action="store_true",
        help="replace the tracked fixture after an intentional API review",
    )
    args = parser.parse_args()

    if args.update:
        update_contract()
        print("Updated the tracked public API contract.")
        return 0
    if contract_is_current():
        print("The tracked public API contract is current.")
        return 0
    print(
        "The tracked public API contract is stale; review the API change, then "
        "run this command with --update."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
