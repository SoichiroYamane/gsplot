from __future__ import annotations
import os
import json

from typing import Any, cast
from threading import Lock


from matplotlib import rcParams
import matplotlib as mpl
from rich.traceback import install


rcParams["pdf.fonttype"] = 42
rcParams["ps.fonttype"] = 42

# Legend with normal box (as V1)
rcParams["legend.fancybox"] = False
rcParams["legend.framealpha"] = None
rcParams["legend.edgecolor"] = "inherit"
rcParams["legend.frameon"] = False

# Nice round numbers on axis and 'tight' axis limits to data (as V1)
rcParams["axes.autolimit_mode"] = "round_numbers"
rcParams["axes.xmargin"] = 0
rcParams["axes.ymargin"] = 0

# Ticks as in mpl V1 (everywhere and inside)
rcParams["xtick.direction"] = "in"
rcParams["ytick.direction"] = "in"
rcParams["xtick.top"] = True
rcParams["ytick.right"] = True
rcParams["legend.labelspacing"] = 0.3

rcParams["font.family"] = "sans-serif"
rcParams["font.sans-serif"] = ["DejaVu Sans"]

rcParams["xtick.major.pad"] = 6
rcParams["ytick.major.pad"] = 6


class Config:

    _instance: Config | None = None
    _lock: Lock = Lock()

    def __new__(cls) -> "Config":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Config, cls).__new__(cls)
                cls._instance._initialize_config_dict()
        return cls._instance

    def _initialize_config_dict(self) -> None:
        self._config_dict: dict[str, Any] = ConfigLoad().init_load()

    @property
    def config_dict(self) -> dict[str, Any]:
        return self._config_dict

    @config_dict.setter
    def config_dict(self, config_dict: dict[str, Any]) -> None:
        self._config_dict = config_dict

    def load(self, config_path: str | None = None) -> dict[str, Any]:
        loader: ConfigLoad = ConfigLoad(config_path)
        config_dict: dict[str, Any] = (
            loader.init_load() if config_path else loader.get_config()
        )
        self.config_dict = config_dict
        return config_dict

    def get_config_entry_option(self, key: str) -> dict[str, Any]:
        entry_option: dict[str, Any] = self.config_dict.get(key, {})
        return entry_option


class ConfigLoad:
    DEFAULT_CONFIG_NAME: str = "gsplot.json"

    def __init__(self, config_path: str | None = None) -> None:
        self.config_path: str | None = self.find_config_path(config_path)

    def find_config_path(self, config_path: str | None) -> str | None:
        """Determine the configuration file path."""
        if config_path:
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            return config_path

        # Search in default locations
        search_paths = [
            os.getcwd(),  # Current directory
            os.path.expanduser("~"),  # Home directory
        ]

        for path in search_paths:
            potential_path = os.path.join(path, ConfigLoad.DEFAULT_CONFIG_NAME)
            if os.path.exists(potential_path):
                return potential_path
        return None

    def init_load(self) -> dict[str, Any]:

        config_dict: dict[str, Any] = self.get_config()
        if "rcParams" in config_dict:
            rc_params = config_dict["rcParams"]
            self.apply_rc_params(rc_params)
        if "rich" in config_dict:
            if "traceback" in config_dict["rich"]:
                traceback_params = config_dict["rich"]["traceback"]
                install(**traceback_params)
        return config_dict

    @staticmethod
    def apply_rc_params(rc_params: dict[str, Any]) -> None:
        backend = rc_params.pop("backends", None)
        if backend:
            mpl.use(backend)
        rcParams.update(rc_params)

    def get_config(self) -> dict[str, Any]:
        if not self.config_path:
            return {}
        with open(self.config_path, "r") as f:
            return cast(dict[str, Any], json.load(f))


#!TODO: Add docstring
def config_load(config_path: str | None = None) -> dict[str, Any]:
    _config: Config = Config()
    config_dict: dict[str, Any] = _config.load(config_path)
    return config_dict


def config_dict() -> dict[str, Any]:
    _config: Config = Config()
    config_dict: dict[str, Any] = _config.config_dict
    return config_dict


def config_entry_option(key: str) -> dict[str, Any]:
    _config: Config = Config()
    entry_option: dict[str, Any] = _config.get_config_entry_option(key)
    return entry_option
