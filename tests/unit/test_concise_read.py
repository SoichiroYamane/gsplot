"""Tests for concise CSV reading and native NumPy result preservation."""

from pathlib import Path
from typing import Any

import numpy as np
import pytest

import gsplot as gs
from gsplot._io.arrays import read_array


def test_read_defaults_to_csv_and_unpacked_columns(tmp_path: Path) -> None:
    """The common path reads comma-delimited columns ready for plotting."""

    source = tmp_path / "values.csv"
    source.write_text("x,y,z\n0,1,2\n3,4,5\n6,7,8\n", encoding="utf-8")
    before = Path.cwd()

    loaded = gs.read(source, skip_header=1, usecols=(0, 2))

    assert isinstance(loaded, np.ndarray)
    assert loaded.shape == (2, 3)
    assert np.array_equal(loaded, [[0, 3, 6], [2, 5, 8]])
    assert Path.cwd() == before


def test_read_supports_whitespace_and_loadtxt_skip_translation(tmp_path: Path) -> None:
    """Whitespace remains explicit and skip_header maps across both loaders."""

    source = tmp_path / "values.txt"
    source.write_text("header\n1 2\n3 4\n", encoding="utf-8")

    loaded = gs.read(
        source,
        loader="loadtxt",
        delimiter=None,
        skip_header=1,
        unpack=False,
    )

    assert isinstance(loaded, np.ndarray)
    assert np.array_equal(loaded, [[1, 2], [3, 4]])


def test_read_and_read_array_preserve_structured_unpacked_fields(
    tmp_path: Path,
) -> None:
    """Structured field arrays keep NumPy's heterogeneous list result."""

    source = tmp_path / "mixed.csv"
    source.write_text("alpha,1.5\nbeta,2.5\n", encoding="utf-8")
    dtype = np.dtype([("name", "U8"), ("value", "f8")])

    concise = gs.read(source, dtype=dtype)
    advanced = read_array(
        source,
        options={"delimiter": ",", "dtype": dtype, "unpack": True},
    )
    with pytest.deprecated_call():
        legacy = gs.load_file(source, dtype=dtype)

    for loaded in (concise, advanced, legacy):
        assert isinstance(loaded, list)
        assert len(loaded) == 2
        assert loaded[0].dtype.kind == "U"
        assert loaded[1].dtype == np.dtype("float64")
        assert loaded[0].tolist() == ["alpha", "beta"]
        assert loaded[1].tolist() == [1.5, 2.5]


@pytest.mark.parametrize(
    "options",
    (
        {"loader": "unknown"},
        {"delimiter": ""},
        {"comments": ""},
        {"skip_header": True},
        {"skip_header": -1},
        {"usecols": []},
        {"usecols": {0, 1}},
        {"usecols": [0, True]},
        {"unpack": 1},
        {"ndmin": True},
        {"ndmin": 3},
        {"dtype": "not-a-dtype"},
        {"loader": "loadtxt", "delimiter": "::"},
    ),
)
def test_read_rejects_invalid_controls_before_opening(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    options: dict[str, Any],
) -> None:
    """Closed concise controls fail before either NumPy loader is called."""

    def unexpected(*args: Any, **kwargs: Any) -> np.ndarray:
        raise AssertionError("loader must not be called")

    monkeypatch.setattr(np, "genfromtxt", unexpected)
    monkeypatch.setattr(np, "loadtxt", unexpected)

    with pytest.raises(gs.DataError, match="read"):
        gs.read(tmp_path / "missing.csv", **options)


def test_read_reports_loader_failures_without_disclosing_the_path(
    tmp_path: Path,
) -> None:
    """Typed errors do not echo a potentially private local path."""

    source = tmp_path / "private-name.csv"
    with pytest.raises(gs.DataError) as error:
        gs.read(source)
    assert str(source) not in str(error.value)
