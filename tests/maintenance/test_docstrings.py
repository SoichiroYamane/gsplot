"""Tests for the canonical NumPy-style docstring audit."""

from __future__ import annotations

import doctest
import inspect
import os
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pytest

import gsplot
from gsplot._compat.root import _CANONICAL_EXPORTS
from gsplot._core.types import _PUBLIC_TYPE_ALIAS_DOCS
from tools.maintenance import check_docstrings


def _documented(alpha: int = 1, beta: str | None = None) -> int:
    """Return one documented value.

    Parameters
    ----------
    alpha, beta
        Example inputs.

    Returns
    -------
    int
        The selected value.

    Raises
    ------
    ValueError
        If the example is invalid.

    Examples
    --------
    >>> _documented()
    1
    """

    return alpha


def test_callable_audit_accepts_grouped_parameter_names() -> None:
    """Grouped NumPy declarations satisfy both signature parameters."""

    assert check_docstrings._check_callable("example", _documented) == []


def test_callable_audit_rejects_missing_and_stale_parameter_names() -> None:
    """A section heading cannot hide parameter-name drift."""

    def changed(alpha: int = 1) -> int:
        """Return one value.

        Parameters
        ----------
        stale
            An obsolete name.

        Returns
        -------
        int
            The selected value.

        Raises
        ------
        ValueError
            If invalid.

        Examples
        --------
        >>> changed()
        1
        """

        return alpha

    errors = check_docstrings._check_callable("changed", changed)

    assert "changed: undocumented parameters: alpha" in errors
    assert "changed: stale documented parameters: stale" in errors


def test_callable_audit_rejects_empty_returns_section() -> None:
    """A Returns heading requires an actual type/value contract."""

    def empty() -> int:
        """Return one value.

        Returns
        -------

        Raises
        ------
        ValueError
            If invalid.

        Examples
        --------
        >>> empty()
        1
        """

        return 1

    assert (
        "example: Returns section must document the returned value"
        in check_docstrings._check_callable("example", empty)
    )


def test_reviewed_default_audit_detects_runtime_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Known concise defaults are independent of docstring prose."""

    monkeypatch.setitem(
        check_docstrings._REVIEWED_DEFAULTS, "example", {"alpha": 2, "beta": None}
    )

    assert (
        "example: alpha default must be 2, got 1"
        in check_docstrings._check_callable("example", _documented)
    )


def test_public_type_alias_docs_cover_the_canonical_root() -> None:
    """Every non-callable canonical export has one finite alias description."""

    repository_root = check_docstrings.Path(__file__).resolve().parents[2]

    assert check_docstrings._check_root(repository_root) == []


def test_type_alias_audit_precedes_runtime_class_introspection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Explicit aliases stay aliases when an older Python reports them as classes."""

    repository_root = check_docstrings.Path(__file__).resolve().parents[2]
    alias_ids = {id(getattr(gsplot, name)) for name in _PUBLIC_TYPE_ALIAS_DOCS}
    runtime_isclass = check_docstrings.inspect.isclass
    monkeypatch.setattr(
        check_docstrings.inspect,
        "isclass",
        lambda value: id(value) in alias_ids or runtime_isclass(value),
    )

    assert check_docstrings._check_root(repository_root) == []


def test_public_exception_requires_an_example() -> None:
    """Exception classes cannot bypass the executable-example contract."""

    class UndocumentedError(Exception):
        """One exception without an example."""

    assert check_docstrings._check_class("UndocumentedError", UndocumentedError) == [
        "UndocumentedError: public exception requires an Examples section"
    ]


def _doctest_result(name: str, doc: str) -> doctest.TestResults:
    """Execute one public example block with stable repr matching."""

    test = doctest.DocTestParser().get_doctest(inspect.cleandoc(doc), {}, name, None, 0)
    runner = doctest.DocTestRunner(
        optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE
    )
    return runner.run(test, clear_globs=False)


def test_canonical_and_type_alias_examples_execute(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Public examples run in a disposable directory without shared Figures."""

    monkeypatch.chdir(tmp_path)
    for name in _CANONICAL_EXPORTS:
        value = getattr(gsplot, name)
        module_name, attribute_name = _CANONICAL_EXPORTS[name]
        module = __import__(module_name, fromlist=[attribute_name])
        if check_docstrings._is_explicit_type_alias(module, attribute_name):
            continue
        if name == "use_backend" or not (
            inspect.isfunction(value) or inspect.isclass(value)
        ):
            continue
        result = _doctest_result(name, inspect.getdoc(value) or "")
        plt.close("all")
        assert result.failed == 0, name
        assert result.attempted > 0, name
    for name, doc in _PUBLIC_TYPE_ALIAS_DOCS.items():
        result = _doctest_result(name, doc)
        plt.close("all")
        assert result.failed == 0, name
        assert result.attempted > 0, name


def test_backend_example_executes_before_pyplot_import(tmp_path: Path) -> None:
    """The process-global backend example runs at its required lifecycle point."""

    script = """
import doctest
import inspect
import gsplot

doc = inspect.getdoc(gsplot.use_backend) or ""
test = doctest.DocTestParser().get_doctest(doc, {}, "use_backend", None, 0)
result = doctest.DocTestRunner().run(test, clear_globs=False)
raise SystemExit(result.failed)
"""
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
