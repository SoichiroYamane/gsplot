"""Tests for forwarding-only historical module paths."""

import os
import subprocess
import sys
from pathlib import Path

from tools.maintenance.collect_public_api import HISTORICAL_DOCUMENTED_MODULES


def test_historical_module_paths_forward_with_warnings_without_app_files(
    tmp_path,
) -> None:
    """Every reviewed old import warns and avoids the removed application log."""

    repository_root = Path(__file__).resolve().parents[2]
    environment = os.environ.copy()
    source_path = str(repository_root / "src")
    existing = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        source_path if not existing else f"{source_path}{os.pathsep}{existing}"
    )
    home = tmp_path / "home"
    mpl_cache = tmp_path / "mpl-cache"
    work = tmp_path / "work"
    home.mkdir()
    mpl_cache.mkdir()
    work.mkdir()
    environment["HOME"] = str(home)
    environment["MPLCONFIGDIR"] = str(mpl_cache)
    modules = repr(tuple(HISTORICAL_DOCUMENTED_MODULES))
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            f"""
import importlib
import warnings
from pathlib import Path

modules = {modules}
for module_name in modules:
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always')
        module = importlib.import_module(module_name)
    assert any(
        item.category is DeprecationWarning and module_name in str(item.message)
        for item in captured
    ), module_name
    assert module.__name__ == module_name

with warnings.catch_warnings(record=True) as captured:
    warnings.simplefilter('always')
    logger_module = importlib.import_module('gsplot.logger')
    assert logger_module.logger() is None
assert any('gsplot.logger' in str(item.message) for item in captured)
assert not (Path.home() / '.config' / 'gsplot').exists()
""",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
        cwd=work,
    )
    assert probe.returncode == 0, probe.stderr
    assert not tuple(work.iterdir())
