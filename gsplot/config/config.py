from ..data.path import Path

from termcolor import colored
import traceback
import os
import json

from typing import Any, Optional, Dict

from matplotlib import rcParams
import matplotlib as mpl


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

home = os.path.expanduser("~")


# class Config:
#
#     _instance: Optional["Config"] = None
#
#     def __new__(cls) -> "Config":
#         if cls._instance is None:
#             cls._instance = super(Config, cls).__new__(cls)
#             cls._instance._initialize_config_dict()
#         return cls._instance
#
#     def _initialize_config_dict(self) -> None:
#
#         self._config_dict: dict[str, Any] = {}
#
#     @property
#     def config_dict(self) -> dict[str, Any]:
#         return self._config_dict
#
#     @config_dict.setter
#     def config_dict(self, config_dict: dict[str, Any]) -> None:
#         # if not isinstance(config_dict, dict):
#         #     raise TypeError(f"Expected type dict, got {type(config_dict).__name__}")
#         self._config_dict = config_dict
#
#     def get_config_entry_option(self, key: str) -> dict[str, Any]:
#         try:
#             config_instance = Config()
#             entry_option = config_instance.config_dict.get(key, {})
#             if isinstance(entry_option, dict):
#                 return entry_option
#             else:
#                 raise ValueError("Expected a dictionary")
#         except Exception:
#             return dict[str, Any]()


class Config:

    _instance: Optional["Config"] = None

    def __new__(cls) -> "Config":
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialize_config_dict()
        return cls._instance

    def _initialize_config_dict(self) -> None:

        self._config_dict: dict[str, Any] = ConfigLoad().get_config()

    @property
    def config_dict(self) -> dict[str, Any]:
        return self._config_dict

    @config_dict.setter
    def config_dict(self, config_dict: dict[str, Any]) -> None:
        # if not isinstance(config_dict, dict):
        #     raise TypeError(f"Expected type dict, got {type(config_dict).__name__}")
        self._config_dict = config_dict

    def get_config_entry_option(self, key: str) -> dict[str, Any]:
        try:
            config_instance = Config()
            entry_option = config_instance.config_dict.get(key, {})
            if isinstance(entry_option, dict):
                return entry_option
            else:
                raise ValueError("Expected a dictionary")
        except Exception:
            return dict[str, Any]()


# class LoadConfig:
#     def __init__(self) -> None:
#         self.home: str = Path().get_home()
#         self.config_fname: str = ".gsplot.json"
#         self.config_path: str = f"{self.home}/{self.config_fname}"
#
#         try:
#             self._init_load()
#         except Exception:
#             pass
#
#     def _init_load(self) -> None:
#         """
#         Loads parameters from the configuration file and applies them to matplotlib settings.
#
#         This method reads the configuration file, retrieves the `rcParams`, and applies the
#         relevant settings to matplotlib, such as setting the backend and other parameters.
#         """
#
#         config_dict: dict[str, Any] = self.load_config()
#         config_rcParams: dict[str, Any] = config_dict["rcParams"]
#
#         # if "backends" in config_rcParams:
#         #     backend = config_rcParams["backends"]
#         #     mpl.use(backend)
#         #
#         # for key in config_rcParams:
#         #     if key != "backends":
#         #         rcParams[key] = config_rcParams[key]
#         #
#         backend = config_rcParams.pop("backends", None)
#         if backend:
#             mpl.use(backend)
#
#         rcParams.update(config_rcParams)
#
#     def load_config(self) -> dict[str, Any]:
#         config_instance: Config = Config()
#         try:
#             with open(self.config_path, "r") as f:
#                 config_dict: dict[str, Any] = json.load(f)
#
#             config_instance.config_dict = config_dict
#             return config_dict
#
#         except FileNotFoundError:
#             config_default: dict[str, Any] = {}
#             config_instance.config_dict = config_default
#             return config_default
#
#         except Exception as e:
#             raise ValueError(f"Error in reading ~/.gsplot.json: {e}")


class ConfigLoad:
    def __init__(self) -> None:
        self.home: str = Path().get_home()
        self.config_fname: str = ".gsplot.json"
        self.config_path: str = f"{self.home}/{self.config_fname}"

        try:
            self._init_load()
        except Exception:

            border_top = colored(
                "╭──────────────────────────────────────────────╮", "red"
            )
            border_bottom = colored(
                "╰──────────────────────────────────────────────╯", "red"
            )

            # Max width for the content inside the borders
            max_width = 46

            # Colored lines with proper padding
            error_header = (
                colored("│", "red")
                + colored(
                    f" ERROR: Failed to load a configuration file".ljust(max_width),
                    "red",
                    attrs=["bold"],
                )
                + colored("│", "red")
            )
            error_file = (
                colored("│", "red")
                + colored(
                    f" File : the configuration file ~/.gsplot.json".ljust(max_width),
                    "yellow",
                )
                + colored("│", "red")
            )
            error_hint = (
                colored("│", "red")
                + colored(
                    f" Hint : Please check the file for errors".ljust(max_width), "cyan"
                )
                + colored("│", "red")
            )

            # Print the styled error message
            print(
                f"{border_top}\n{error_header}\n{error_file}\n{error_hint}\n{border_bottom}"
            )

            # Print the actual traceback details
            print(colored("Details:", "yellow"))
            traceback.print_exc()  # Print the full traceback of the exception

    def _init_load(self) -> None:
        """
        Loads parameters from the configuration file and applies them to matplotlib settings.

        This method reads the configuration file, retrieves the `rcParams`, and applies the
        relevant settings to matplotlib, such as setting the backend and other parameters.
        """

        config_dict: dict[str, Any] = self.get_config()

        if "rcParams" in config_dict:
            config_rcParams: dict[str, Any] = config_dict["rcParams"]
            backend = config_rcParams.pop("backends", None)
            if backend:
                mpl.use(backend)
            rcParams.update(config_rcParams)

        # if "backends" in config_rcParams:
        #     backend = config_rcParams["backends"]
        #     mpl.use(backend)
        #
        # for key in config_rcParams:
        #     if key != "backends":
        #         rcParams[key] = config_rcParams[key]
        #

    def get_config(self) -> dict[str, Any]:
        try:
            with open(self.config_path, "r") as f:
                config_dict: dict[str, Any] = json.load(f)

            return config_dict

        except FileNotFoundError:
            config_default: dict[str, Any] = {}
            return config_default

        except Exception as e:
            raise ValueError(f"Error in reading ~/.gsplot.json: {e}")


def get_config_dict() -> dict[str, Any]:
    config_instance: Config = Config()
    config_dict: dict[str, Any] = config_instance.config_dict
    return config_dict
