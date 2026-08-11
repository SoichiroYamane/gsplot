import json

import matplotlib as mpl

from gsplot.config.config import Config, ConfigLoad


def test_apply_rc_params_does_not_mutate_the_input() -> None:
    rc_params = {"backend": "Agg", "figure.dpi": 123}
    original = rc_params.copy()

    ConfigLoad.apply_rc_params(rc_params)

    assert rc_params == original
    assert mpl.rcParams["figure.dpi"] == 123


def test_apply_rc_params_accepts_the_legacy_backend_key() -> None:
    rc_params = {"backends": "Agg", "axes.xmargin": 0.15}

    ConfigLoad.apply_rc_params(rc_params)

    assert rc_params == {"backends": "Agg", "axes.xmargin": 0.15}
    assert mpl.rcParams["axes.xmargin"] == 0.15


def test_config_load_without_a_path_discovers_the_working_directory_config(
    monkeypatch, tmp_path
) -> None:
    config_file = tmp_path / "gsplot.json"
    config_file.write_text(
        json.dumps({"rcParams": {"figure.dpi": 111}, "metadata": False}),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    config = Config()
    original_config = config.config_dict
    try:
        loaded = config.load()
    finally:
        config._config_dict = original_config

    assert loaded["rcParams"]["figure.dpi"] == 111
    assert mpl.rcParams["figure.dpi"] == 111
