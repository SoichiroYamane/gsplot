"""Subprocess tests for import-time side-effect boundaries."""

import os
import subprocess
import sys
from pathlib import Path


def _run_probe(source: str) -> subprocess.CompletedProcess[str]:
    """Run a probe with the source package available without importing it here."""

    repository_root = Path(__file__).resolve().parents[2]
    environment = os.environ.copy()
    environment["MPLBACKEND"] = "Agg"
    source_path = str(repository_root / "src")
    existing = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        source_path if not existing else f"{source_path}{os.pathsep}{existing}"
    )
    return subprocess.run(
        [sys.executable, "-c", source],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )


def test_plain_import_does_not_initialize_matplotlib_or_files() -> None:
    """A plain package import loads only metadata and compatibility lookup code."""

    result = _run_probe("""
import sys
import gsplot
assert 'matplotlib' not in sys.modules
assert 'matplotlib.pyplot' not in sys.modules
assert gsplot.__commit__ is None
""")
    assert result.returncode == 0, result.stderr


def test_legacy_attribute_loads_only_when_requested() -> None:
    """Legacy use remains available while its imports are deferred."""

    result = _run_probe("""
import sys
import gsplot
assert 'matplotlib.pyplot' not in sys.modules
assert callable(gsplot.line)
assert 'matplotlib.pyplot' in sys.modules
""")
    assert result.returncode == 0, result.stderr
