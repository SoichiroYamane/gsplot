"""Run the repository demos used as executable documentation."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    demo_files = sorted((PROJECT_ROOT / "demo").rglob("*.py"))
    if not demo_files:
        raise SystemExit("No demo scripts were found.")

    environment = os.environ.copy()
    environment.setdefault("MPLBACKEND", "Agg")
    pythonpath = [str(PROJECT_ROOT)]
    if environment.get("PYTHONPATH"):
        pythonpath.append(environment["PYTHONPATH"])
    environment["PYTHONPATH"] = os.pathsep.join(pythonpath)

    for demo_file in demo_files:
        print(f"Running demo: {demo_file.relative_to(PROJECT_ROOT)}")
        subprocess.run(
            [sys.executable, str(demo_file)],
            cwd=demo_file.parent,
            env=environment,
            check=True,
        )


if __name__ == "__main__":
    main()
