"""Contract coverage for the pure canonical validation and value layer."""

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

import gsplot as gs
from gsplot._config.schema import (
    parse_color,
    parse_default_color,
    parse_figsize,
    parse_schema_version,
    parse_unit,
    validate_section,
)
from gsplot._core import (
    MISSING,
    ConfigError,
    DataError,
    LayoutError,
    MetadataError,
    PlotError,
    as_float_array,
    ensure_finite_real,
    ensure_iterable,
    ensure_nonnegative,
    ensure_pair,
    resolve_option,
    segment_points,
    validate_color_values,
    validate_xy,
)


def test_numerical_foundations_copy_and_validate_shapes() -> None:
    """Numerical helpers preserve inputs and reject ambiguous arrays."""

    source = [1, 2]
    copied = as_float_array(source, "values", ndim=1)
    source[0] = 99
    assert np.array_equal(copied, [1, 2])
    assert as_float_array([], "values", allow_empty=True).size == 0
    assert np.array_equal(validate_color_values([0, 1]), [0, 1])
    assert np.array_equal(validate_xy([0, 1], [2, 3])[0], [0, 1])
    assert np.array_equal(
        segment_points([0, 1, 2], [3, 4, 5]),
        [[[0, 3], [1, 4]], [[1, 4], [2, 5]]],
    )

    with pytest.raises(DataError):
        as_float_array(["not numeric"], "values")
    with pytest.raises(DataError):
        as_float_array([[1]], "values", ndim=1)
    with pytest.raises(DataError):
        as_float_array([], "values")
    with pytest.raises(DataError):
        as_float_array([np.inf], "values")
    with pytest.raises(DataError):
        validate_xy([0], [0, 1])
    with pytest.raises(DataError):
        validate_xy([0], [1], colored=True)


def test_validation_precedence_and_pairs_cover_boundary_types() -> None:
    """Shared validators handle defaults, custom errors, and iterable edges."""

    assert resolve_option("explicit", "configured", "default") == "explicit"
    assert resolve_option(object(), "configured", "default") != "default"
    assert resolve_option(MISSING, "configured", "default") == "configured"
    assert resolve_option(MISSING, MISSING, "default") == "default"
    assert ensure_finite_real(np.float64(1.5), "value") == 1.5
    assert ensure_nonnegative(0, "value") == 0.0
    assert list(ensure_iterable((1, 2), "values")) == [1, 2]
    assert ensure_pair((1, 2), "pair") == (1.0, 2.0)
    assert ensure_pair((1, 2), "pair", positive=True) == (1.0, 2.0)

    for value in (True, "1", float("inf")):
        with pytest.raises(DataError):
            ensure_finite_real(value, "value")
    for value in ("12", 1, (1,), (1, 2, 3), (0, 1)):
        with pytest.raises(LayoutError):
            ensure_pair(value, "pair", positive=True)


def test_axis_inset_theme_and_metadata_values_are_fully_immutable() -> None:
    """Public value objects normalize valid inputs and reject all bad fields."""

    axis = gs.AxisSpec(
        xlabel="x",
        ylabel="y",
        xlim=[0, 1],
        ylim=[1, 2],
        xscale="log",
        yscale="symlog",
        xticks=[0, 1],
        yticks=[1, 2],
        xminor=True,
        yminor=False,
        xlabelpad=2,
        ylabelpad=3,
    )
    assert axis.xlim == (0.0, 1.0)
    assert axis.xticks == (0.0, 1.0)
    with pytest.raises(LayoutError):
        gs.AxisSpec(xlim="bad")  # type: ignore[arg-type]
    with pytest.raises(LayoutError):
        gs.AxisSpec(xlim=1)  # type: ignore[arg-type]
    with pytest.raises(LayoutError):
        gs.AxisSpec(xlim=(0, 1, 2))  # type: ignore[arg-type]
    with pytest.raises(LayoutError):
        gs.AxisSpec(xscale=[])  # type: ignore[arg-type]
    with pytest.raises(LayoutError):
        gs.AxisSpec(yscale=None)  # type: ignore[arg-type]
    with pytest.raises(LayoutError):
        gs.AxisSpec(xticks=1)  # type: ignore[arg-type]
    with pytest.raises(LayoutError):
        gs.AxisSpec(xminor=1)  # type: ignore[arg-type]
    with pytest.raises(LayoutError):
        gs.AxisSpec(yminor=1)  # type: ignore[arg-type]

    bounded = gs.InsetSpec(bounds=[0, 0, 1, 1])
    sized = gs.InsetSpec(width="25%", height="50%", loc=2, bbox_to_anchor=(0, 0))
    assert bounded.bounds == (0.0, 0.0, 1.0, 1.0)
    assert sized.loc == 2
    for kwargs in (
        {"bounds": "bad"},
        {"bounds": object()},
        {"bounds": (0, 0, 1)},
        {"bounds": (0, 0, 1, 1), "width": 1, "height": 1},
        {"width": "101%", "height": 1},
        {"width": 1, "height": None},
        {"width": 0, "height": 1},
        {"width": 1, "height": 1, "bbox_to_anchor": "bad"},
        {"width": 1, "height": 1, "loc": 11},
    ):
        with pytest.raises(LayoutError):
            gs.InsetSpec(**kwargs)  # type: ignore[arg-type]

    assert gs.Theme.default().grid is None
    assert gs.Theme.white().text_color == "white"
    assert gs.Theme.transparent().figure_facecolor == (0.0, 0.0, 0.0, 0.0)
    with pytest.raises(PlotError):
        gs.Theme(grid_alpha=2)
    with pytest.raises(PlotError):
        gs.Theme(grid_alpha=True)  # type: ignore[arg-type]
    with pytest.raises(PlotError):
        gs.Theme(grid_alpha="bad")  # type: ignore[arg-type]
    with pytest.raises(PlotError):
        gs.Theme(axes_facecolor=1)  # type: ignore[arg-type]
    with pytest.raises(PlotError):
        gs.Theme(axes_facecolor=(1, 0))  # type: ignore[arg-type]
    with pytest.raises(PlotError):
        gs.Theme(axes_facecolor=(2, 0, 0))  # type: ignore[arg-type]
    assert gs.Theme(axes_facecolor=(1, 0, 0)).axes_facecolor == (1.0, 0.0, 0.0)

    labels = {"kind": "example"}
    snapshot = gs.MetadataSnapshot("1.0", commit="abc", labels=labels)
    labels["kind"] = "changed"
    assert snapshot.labels == {"kind": "example"}
    with pytest.raises(TypeError):
        snapshot.labels["new"] = "value"  # type: ignore[index]
    with pytest.raises(MetadataError):
        gs.MetadataSnapshot("x" * 129)
    with pytest.raises(MetadataError):
        gs.MetadataSnapshot("1", schema_version=2)  # type: ignore[arg-type]
    assert gs.BuildInfo("1", commit="abc").commit == "abc"
    with pytest.raises(FrozenInstanceError):
        axis.xlabel = "changed"  # type: ignore[misc]


def test_strict_config_schema_helpers_cover_all_scalar_forms() -> None:
    """Schema helpers accept documented forms and reject unsafe values."""

    assert parse_schema_version(1) == 1
    assert parse_schema_version(2) == 2
    assert parse_unit("cm") == "cm"
    assert parse_figsize([1, 2]) == (1.0, 2.0)
    assert parse_figsize(None) is None
    assert parse_color("white", "color") == "white"
    assert parse_color([0, 0.5, 1], "color") == (0.0, 0.5, 1.0)
    assert parse_default_color("axes") == "axes"
    assert validate_section({}, "figure", set()) == {}

    for value in (True, 3, "1"):
        with pytest.raises(ConfigError):
            parse_schema_version(value)
    with pytest.raises(ConfigError):
        parse_unit("pixels")
    for value in ("bad", [1], [1, 2, 3], [0, 1]):
        with pytest.raises(ConfigError):
            parse_figsize(value)
    for value in (1, [0, 1], [0, 1, 2], [0, 2, 0]):
        with pytest.raises(ConfigError):
            parse_color(value, "color")
    with pytest.raises(ConfigError):
        validate_section({"unexpected": True}, "figure", set())
