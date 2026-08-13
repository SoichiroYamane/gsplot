"""Tests for the canonical NumPy-style docstring audit."""

from __future__ import annotations

import pytest

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
