"""Smoke-test an installed gsplot wheel outside its source checkout."""

from __future__ import annotations

import argparse
import sys
import tempfile
from importlib import metadata
from pathlib import Path


def main() -> int:
    """Exercise the installed package with no development-only dependencies."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--forbid-source-root", type=Path)
    args = parser.parse_args()

    before = set(Path.cwd().iterdir())
    if "matplotlib" in sys.modules or "gsplot" in sys.modules:
        raise RuntimeError("smoke process must start before package imports")
    import gsplot as gs

    if "matplotlib" in sys.modules:
        raise RuntimeError("plain installed-package import loaded Matplotlib")
    package_path = Path(gs.__file__).resolve()
    if args.forbid_source_root is not None:
        try:
            package_path.relative_to(args.forbid_source_root.resolve())
        except ValueError:
            pass
        else:
            raise RuntimeError("smoke import resolved to the source checkout")
    if gs.__version__ != metadata.version("gsplot"):
        raise RuntimeError("runtime and installed distribution versions differ")
    installed = {
        (item.metadata.get("Name") or "").lower() for item in metadata.distributions()
    }
    forbidden = {
        "black",
        "mypy",
        "poetry",
        "pyright",
        "pytest",
        "pyyaml",
        "rich",
        "sphinx",
        "types-pyyaml",
    }
    if installed & forbidden:
        raise RuntimeError("clean smoke environment contains development tooling")

    gs.use_backend("Agg")
    import matplotlib.pyplot as plt

    with tempfile.TemporaryDirectory(prefix="gsplot-installed-smoke-") as directory:
        output = Path(directory) / "figure"
        figure, axis = gs.subplots()
        gs.line(axis, [0, 1, 2], [0, 1, 4], label="sample")
        gs.label(axis, "x", "y", square=True, index="in")
        gs.legend(axis)
        written = gs.save(figure, output, show=False, close=True)
        if {path.suffix for path in written} != {".pdf", ".png"}:
            raise RuntimeError("installed package did not write the expected formats")
        if not all(path.is_file() and path.stat().st_size > 0 for path in written):
            raise RuntimeError("installed package wrote an empty output")
    if plt.get_fignums():
        raise RuntimeError("installed-package smoke test retained a Figure")
    if set(Path.cwd().iterdir()) != before:
        raise RuntimeError("installed-package smoke test changed its working directory")
    print("Installed wheel smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
