from typing import Any

import pytest

from gsplot.base.base import (
    CreateClassParams,
    GetPassedParams,
    ParamsGetter,
    bind_passed_params,
)
from gsplot.config.config import Config


@bind_passed_params()
def configured_function(
    first: int = 1, second: int = 2, **kwargs: Any
) -> dict[str, Any]:
    passed = ParamsGetter("passed_params").get_bound_params()
    return CreateClassParams(passed).get_class_params()


def test_get_passed_params_keeps_explicit_arguments_and_kwargs() -> None:
    def example(first: int, second: int = 2, *args: int, **kwargs: Any) -> None:
        pass

    passed = GetPassedParams(example, 1, 3, 4, label="sample").get_passed_params()

    assert passed == {
        "first": 1,
        "second": 3,
        "args": (4,),
        "kwargs": {"label": "sample"},
    }


def test_get_passed_params_does_not_treat_defaults_as_explicit() -> None:
    def example(first: int, second: int = 2, **kwargs: Any) -> None:
        pass

    passed = GetPassedParams(example, 1).get_passed_params()

    assert passed == {"first": 1, "args": [], "kwargs": {}}


def test_configuration_precedence_is_passed_then_config_then_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = Config()
    original_config = config.config_dict
    monkeypatch.setattr(
        config,
        "_config_dict",
        {
            "configured_function": {
                "second": 20,
                "from_config": "yes",
            }
        },
    )

    try:
        result = configured_function(10, from_config="overridden")
    finally:
        config._config_dict = original_config

    assert result["first"] == 10
    assert result["second"] == 20
    assert result["kwargs"] == {
        "from_config": "overridden",
    }


def test_params_getter_rejects_missing_wrapper_state() -> None:
    with pytest.raises(ValueError, match="Params is None"):
        ParamsGetter("missing").verify(None)


def test_legacy_config_discovery_is_isolated_from_developer_home(
    tmp_path: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Legacy Config discovery respects the isolated HOME environment."""

    import json
    from pathlib import Path

    home_config = Path(tmp_path) / "gsplot.json"
    home_config.write_text(
        json.dumps({"rcParams": {"figure.dpi": 142}}), encoding="utf-8"
    )
    monkeypatch.setenv("HOME", str(tmp_path))
    Config._instance = None
    config = Config()
    assert config.config_dict.get("rcParams", {}).get("figure.dpi") == 142
    Config._instance = None
