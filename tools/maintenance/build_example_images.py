"""Build every manifest-covered documentation example."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from tools.maintenance.example_runner import ExampleError, run_examples


def main(argv: Sequence[str] | None = None) -> int:
    """Run the isolated example builder and return a process status."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        examples = run_examples(args.repo_root)
    except ExampleError as exc:
        print(f"example build failed: {exc}", file=sys.stderr)
        return 1
    print(f"example build passed: {len(examples)} examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
