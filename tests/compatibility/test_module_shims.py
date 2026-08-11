"""Tests for forwarding-only historical module paths."""

import os
import subprocess
import sys
from pathlib import Path


def test_historical_module_path_forwards_with_a_warning() -> None:
    """The old import path remains usable without becoming canonical code."""

    repository_root = Path(__file__).resolve().parents[2]
    environment = os.environ.copy()
    source_path = str(repository_root / "src")
    existing = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        source_path if not existing else f"{source_path}{os.pathsep}{existing}"
    )
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            """
import importlib
import warnings

with warnings.catch_warnings(record=True) as captured:
    warnings.simplefilter('always')
    module = importlib.import_module('gsplot.plot.line')

    assert callable(module.line)
    assert any(item.category is DeprecationWarning for item in captured)
    assert module.__name__ == 'gsplot.plot.line'
""",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert probe.returncode == 0, probe.stderr
