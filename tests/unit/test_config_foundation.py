"""Unit tests for strict immutable JSON configuration."""

from dataclasses import FrozenInstanceError

import pytest

from gsplot._config import (
    Config,
    discover_config_path,
    load_config,
    resolve_config_value,
)
from gsplot._core import MISSING, ConfigError


def test_default_config_is_immutable_and_has_only_target_sections() -> None:
    """Defaults match schema version 1 and cannot be mutated."""

    config = Config()
    assert config.schema_version == 1
    assert config.figure.unit == "in"
    assert config.figure.squeeze is True
    assert config.plotting.default_color == "axes"
    assert config.plotting.default_cmap == "viridis"
    assert config.plotting.nonfinite == "raise"

    with pytest.raises(FrozenInstanceError):
        config.figure = config.figure  # type: ignore[misc]

    section = config.section("figure")
    with pytest.raises(TypeError):
        section["unit"] = "cm"  # type: ignore[index]
    with pytest.raises(TypeError):
        Config(1)  # type: ignore[call-arg]


def test_mapping_values_are_validated_and_precedence_is_explicit() -> None:
    """Mapping input validates closed sections and explicit overrides win."""

    config = Config.from_mapping(
        {
            "schema_version": 1,
            "figure": {"figsize": [10, 5], "unit": "cm", "squeeze": False},
            "plotting": {"default_color": [0.1, 0.2, 0.3], "default_cmap": "plasma"},
        }
    )
    assert config.figure.figsize == (10.0, 5.0)
    assert config.figure.unit == "cm"
    assert config.figure.squeeze is False
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
        {"schema_version": 2},
        {"figure": {"figsize": [1]}},
        {"figure": {"unit": []}},
        {"plotting": {"default_color": [0, 0]}},
    ],
)
def test_invalid_mapping_is_rejected(mapping: dict[str, object]) -> None:
    """Unknown keys and invalid values fail before becoming state."""

    with pytest.raises(ConfigError):
        Config.from_mapping(mapping)

    with pytest.raises(ConfigError, match="keys must be strings"):
        Config.from_mapping({1: {}})  # type: ignore[dict-item]


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
    nonfinite.write_text('{"figure": {"figsize": [1e999, 2]}}', encoding="utf-8")
    with pytest.raises(ConfigError, match="non-finite"):
        Config.from_file(nonfinite)


def test_discovery_order_and_missing_explicit_file(tmp_path) -> None:
    """Discovery is cwd, user config directory, then home."""

    cwd = tmp_path / "cwd"
    home = tmp_path / "home"
    user_config = home / ".config" / "gsplot"
    cwd.mkdir()
    user_config.mkdir(parents=True)
    (home / "gsplot.json").write_text('{"figure": {"unit": "pt"}}', encoding="utf-8")
    (user_config / "gsplot.json").write_text(
        '{"figure": {"unit": "cm"}}', encoding="utf-8"
    )
    assert discover_config_path(cwd=cwd, home=home) == user_config / "gsplot.json"
    assert load_config(cwd=cwd, home=home).figure.unit == "cm"

    (cwd / "gsplot.json").write_text('{"figure": {"unit": "mm"}}', encoding="utf-8")
    assert discover_config_path(cwd=cwd, home=home) == cwd / "gsplot.json"
    assert load_config(cwd=cwd, home=home).figure.unit == "mm"

    with pytest.raises(ConfigError, match="cannot stat"):
        load_config(tmp_path / "missing.json")


def test_config_file_size_is_bounded(tmp_path) -> None:
    """Oversized input is rejected before JSON parsing."""

    path = tmp_path / "large.json"
    path.write_text("{" + "a" * (1_048_576 + 1) + "}", encoding="utf-8")
    with pytest.raises(ConfigError, match="limit"):
        Config.from_file(path)
