"""Tests for deterministic publication-series identities."""

import json
from pathlib import Path

import pytest

from gsplot._core import PlotError
from gsplot._plot.series import (
    SERIES_COLORS,
    SERIES_LINESTYLES,
    SERIES_MARKERS,
    line_series,
    scatter_series,
    series_index,
)


def test_series_tables_match_the_frozen_publication_profile() -> None:
    """Code constants stay byte-for-value aligned with the reviewed fixture."""

    profile_path = (
        Path(__file__).parents[1] / "fixtures/reform/publication-style-v1.json"
    )
    series = json.loads(profile_path.read_text(encoding="utf-8"))["series"]
    assert tuple(map(tuple, series["colors_rgba"])) == SERIES_COLORS
    assert (
        tuple(
            value if isinstance(value, str) else (value[0], tuple(value[1]))
            for value in series["line_styles"]
        )
        == SERIES_LINESTYLES
    )
    assert tuple(series["markers"]) == SERIES_MARKERS


def test_series_lookup_is_pure_and_uses_operation_specific_fields() -> None:
    """Repeated lookups return the same immutable identities without state."""

    for index in range(10):
        assert series_index(index) == index
        assert line_series(index) == line_series(index)
        assert line_series(index) == (SERIES_COLORS[index], SERIES_LINESTYLES[index])
        assert scatter_series(index) == scatter_series(index)
        assert scatter_series(index) == (SERIES_COLORS[index], SERIES_MARKERS[index])


def test_series_lookup_cycles_modulo_for_arbitrary_integers() -> None:
    """Integer values outside 0..9 automatically cycle modulo len(SERIES_COLORS)."""

    assert series_index(10) == 0
    assert series_index(15) == 5
    assert series_index(-1) == 9
    assert line_series(10) == line_series(0)
    assert scatter_series(15) == scatter_series(5)


@pytest.mark.parametrize("value", [True, False, 1.0, "1", None, [1]])
def test_series_lookup_rejects_non_exact_or_out_of_range_indexes(value) -> None:
    """Booleans and non-integer identities fail with explicit-style guidance."""

    with pytest.raises(PlotError, match="explicit style"):
        series_index(value)
