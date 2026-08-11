"""Tests for source-level package boundary enforcement."""

import subprocess
import sys
from pathlib import Path


def test_static_architecture_check_passes_without_importing_gsplot() -> None:
    """The repository checker is executable before package installation."""

    repository_root = Path(__file__).resolve().parents[2]
    checker = repository_root / "tools" / "maintenance" / "check_architecture.py"
    result = subprocess.run(
        [sys.executable, str(checker)],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
