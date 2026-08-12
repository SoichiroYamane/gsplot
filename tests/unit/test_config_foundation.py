"""Unit tests for strict immutable JSON configuration."""

import warnings
from dataclasses import FrozenInstanceError

import pytest

from gsplot._compat.config import discover_config_path
from gsplot._config import (
    Config,
    load_config,
    resolve_config_value,
)
from gsplot._core import MISSING, ConfigError


def test_default_config_is_immutable_and_has_only_target_sections() -> None:
    """Defaults match schema version 2 and cannot be mutated."""

    config = Config()
    assert config.schema_version == 2
    assert config.figure.size == "auto"
    assert config.figure.unit == "in"
    assert config.figure.squeeze is True
    assert config.figure.layout == "auto"
    assert config.plotting.default_color == "axes"
    assert config.plotting.default_cmap == "viridis"
    assert config.plotting.nonfinite == "raise"

    with pytest.raises(FrozenInstanceError):
        config.figure = config.figure  # type: ignore[misc]

    section = config.section("figure")
    assert section == {
        "size": "auto",
        "unit": "in",
        "squeeze": True,
        "layout": "auto",
    }
    with pytest.raises(TypeError):
        section["unit"] = "cm"  # type: ignore[index]
    with pytest.raises(TypeError):
        Config(1)  # type: ignore[call-arg]

    with pytest.warns(DeprecationWarning, match="figsize"):
        assert Config().get("figure", "figsize") is None
    assert Config().get("figure", "unit") == "in"


def test_mapping_values_are_validated_and_precedence_is_explicit() -> None:
    """Mapping input validates closed sections and explicit overrides win."""

    config = Config.from_mapping(
        {
            "schema_version": 2,
            "figure": {
                "size": [10, 5],
                "unit": "cm",
                "squeeze": False,
                "layout": "tight",
            },
            "plotting": {"default_color": [0.1, 0.2, 0.3], "default_cmap": "plasma"},
        }
    )
    assert config.figure.size == (10.0, 5.0)
    assert config.figure.unit == "cm"
    assert config.figure.squeeze is False
    assert config.figure.layout == "tight"
    assert config.plotting.default_color == (0.1, 0.2, 0.3)
    assert (
        resolve_config_value(config, "figure", "unit", explicit="pt", default="in")
        == "pt"
    )
    assert resolve_config_value(config, "figure", "unit", default="in") == "cm"
    assert resolve_config_value(Config(), "figure", "unit", default="pt") == "in"
    assert config.get("figure", "missing", None) is None
    with pytest.raises(ConfigError, match="unknown configuration key"):
        config.get("figure", "missing")


@pytest.mark.parametrize(
    "mapping",
    [
        {"unknown": {}},
        {"figure": {"unknown": True}},
        {"plotting": {"nonfinite": "ignore"}},
        {"schema_version": 3},
        {"schema_version": 2, "figure": {"size": [1]}},
        {"schema_version": 2, "figure": {"unit": []}},
        {"plotting": {"default_color": [0, 0]}},
    ],
)
def test_invalid_mapping_is_rejected(mapping: dict[str, object]) -> None:
    """Unknown keys and invalid values fail before becoming state."""

    with pytest.raises(ConfigError):
        Config.from_mapping(mapping)

    with pytest.raises(ConfigError, match="keys must be strings"):
        Config.from_mapping({1: {}})  # type: ignore[dict-item]

    with pytest.raises(ConfigError, match="schema_version"):
        Config.from_mapping({"figure": {}})


def test_json_parser_rejects_duplicates_trailing_data_and_nonfinite(tmp_path) -> None:
    """The file boundary rejects ambiguous or unsafe JSON input."""

    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"figure": {}, "figure": {}}', encoding="utf-8")
    with pytest.raises(ConfigError, match="duplicate"):
        Config.from_file(duplicate)

    trailing = tmp_path / "trailing.json"
    trailing.write_text("{} {}", encoding="utf-8")
    with pytest.raises(ConfigError, match="invalid JSON"):
        Config.from_file(trailing)

    nonfinite = tmp_path / "nonfinite.json"
    nonfinite.write_text(
        '{"schema_version": 2, "figure": {"size": [1e999, 2]}}',
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="non-finite"):
        Config.from_file(nonfinite)


def test_discovery_order_and_missing_explicit_file(tmp_path) -> None:
    """Discovery is cwd, user config directory, then home."""

    cwd = tmp_path / "cwd"
    home = tmp_path / "home"
    user_config = home / ".config" / "gsplot"
    cwd.mkdir()
    user_config.mkdir(parents=True)
    (home / "gsplot.json").write_text(
        '{"schema_version": 2, "figure": {"size": [1, 1], "unit": "pt"}}',
        encoding="utf-8",
    )
    (user_config / "gsplot.json").write_text(
        '{"schema_version": 2, "figure": {"size": [1, 1], "unit": "cm"}}',
        encoding="utf-8",
    )
    assert discover_config_path(cwd=cwd, home=home) == user_config / "gsplot.json"
    assert load_config(user_config / "gsplot.json").figure.unit == "cm"

    (cwd / "gsplot.json").write_text(
        '{"schema_version": 2, "figure": {"size": [1, 1], "unit": "mm"}}',
        encoding="utf-8",
    )
    assert discover_config_path(cwd=cwd, home=home) == cwd / "gsplot.json"
    assert load_config(cwd / "gsplot.json").figure.unit == "mm"

    with pytest.raises(ConfigError, match="cannot stat"):
        load_config(tmp_path / "missing.json")


def test_schema_one_translates_once_and_deprecated_views_are_lossy(tmp_path) -> None:
    """Schema 1 remains readable through one warning and immutable schema-2 views."""

    mapping = {
        "schema_version": 1,
        "figure": {
            "figsize": [2.54, 5.08],
            "unit": "cm",
            "squeeze": False,
            "tight_layout": True,
        },
    }
    with pytest.warns(DeprecationWarning, match="schema 1") as caught:
        config = Config.from_mapping(mapping)
    assert len(caught) == 1
    assert config.schema_version == 2
    assert config.figure.size == (2.54, 5.08)
    assert config.figure.layout == "tight"
    with pytest.warns(DeprecationWarning, match="figsize"):
        assert config.figure.figsize == (2.54, 5.08)
    with pytest.warns(DeprecationWarning, match="tight_layout"):
        assert config.figure.tight_layout is True
    with pytest.warns(DeprecationWarning, match="constrained_layout"):
        assert config.get("figure", "constrained_layout") is False

    path = tmp_path / "schema-one.json"
    path.write_text('{"schema_version": 1}', encoding="utf-8")
    with pytest.warns(DeprecationWarning, match="schema 1") as caught_file:
        translated = Config.from_file(path)
    assert len(caught_file) == 1
    assert translated.schema_version == 2

    named = Config()
    with pytest.warns(DeprecationWarning, match="figsize"):
        assert named.figure.figsize is None


@pytest.mark.parametrize(
    ("legacy", "expected_size", "expected_layout"),
    [
        ({}, None, "none"),
        ({"constrained_layout": True}, None, "constrained"),
        ({"tight_layout": True}, None, "tight"),
        ({"figsize": [1, 2]}, (1.0, 2.0), "none"),
    ],
)
def test_schema_one_translation_matrix_is_deterministic(
    legacy, expected_size, expected_layout
) -> None:
    """Every supported schema-1 layout and size form has one schema-2 result."""

    with pytest.warns(DeprecationWarning, match="schema 1") as caught:
        config = Config.from_mapping({"schema_version": 1, "figure": legacy})
    assert len(caught) == 1
    assert config.figure.size == expected_size
    assert config.figure.layout == expected_layout


def test_invalid_configurations_do_not_emit_migration_warnings() -> None:
    """Rejected schema-1 input never claims that migration succeeded."""

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with pytest.raises(ConfigError, match="cannot both be true"):
            Config.from_mapping(
                {
                    "schema_version": 1,
                    "figure": {
                        "tight_layout": True,
                        "constrained_layout": True,
                    },
                }
            )
    assert not caught

    for size in ("auto", "single", "double", None):
        with pytest.raises(ConfigError, match="unit must be 'in'"):
            Config.from_mapping(
                {
                    "schema_version": 2,
                    "figure": {"size": size, "unit": "cm"},
                }
            )

    with pytest.raises(ConfigError, match=r"figure\.size\[0\]"):
        Config.from_mapping({"schema_version": 2, "figure": {"size": [0, 1]}})


def test_config_file_size_is_bounded(tmp_path) -> None:
    """Oversized input is rejected before JSON parsing."""

    path = tmp_path / "large.json"
    path.write_text("{" + "a" * (1_048_576 + 1) + "}", encoding="utf-8")
    with pytest.raises(ConfigError, match="limit"):
        Config.from_file(path)
