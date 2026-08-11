"""Print a JSON inventory of the current package-root API.

This is a read-only Phase 0 diagnostic. Importing the pre-reform package can
have the side effects documented in ``docs/project/reform-baseline.md``; run
the command only when that characterization is intentional.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
from collections.abc import Iterable
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


def collect(module_name: str = "gsplot") -> dict[str, Any]:
    """Collect root exports without writing files or intentional mutation."""

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

    return {"module": module_name, "exports": exports}


def main() -> None:
    """Parse arguments and print the inventory as deterministic JSON."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--module",
        default="gsplot",
        help="package module to inspect (default: gsplot)",
    )
    args = parser.parse_args()
    print(json.dumps(collect(args.module), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
