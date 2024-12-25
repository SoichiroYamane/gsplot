from __future__ import annotations

import json
import os
from threading import Lock
from typing import Any, cast

import matplotlib as mpl
from matplotlib import rcParams
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

__all__: list[str] = ["config_load", "config_dict", "config_entry_option"]


class Config:
    """
    A thread-safe singleton class for managing configuration data.

    This class provides a centralized mechanism to load, retrieve, and manage
    configuration settings. It ensures thread safety through a locking mechanism.

    Attributes
    --------------------
    _instance : Config or None
        The singleton instance of the `Config` class.
    _lock : threading.Lock
        A lock to ensure thread safety during singleton initialization.
    _config_dict : dict of str, Any
        The loaded configuration data.

    Methods
    --------------------
    load(config_path=None)
        Loads configuration data from a specified path or reloads the default configuration.
    get_config_entry_option(key)
        Retrieves a specific entry from the configuration dictionary based on the provided key.

    Examples
    --------------------
    >>> config = Config()
    >>> config_data = config.load("path/to/config.json")
    >>> print(config_data)
    {'setting1': 'value1', 'setting2': 'value2', 'setting3': {'setting4': 'value4'}}

    >>> entry_option = config.get_config_entry_option("setting1")
    >>> print(entry_option)
    {'setting3': 'value3'}
    """

    _instance: Config | None = None
    _lock: Lock = Lock()

    def __new__(cls) -> "Config":
        """
        Ensures a single instance of the Config class (singleton pattern).

        Returns
        --------------------
        Config
            The singleton instance of the Config class.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Config, cls).__new__(cls)
                cls._instance._initialize_config_dict()
        return cls._instance

    def _initialize_config_dict(self) -> None:
        """
        Initializes the configuration dictionary by loading default configuration data.
        """
        self._config_dict: dict[str, Any] = ConfigLoad().init_load()

    @property
    def config_dict(self) -> dict[str, Any]:
        """
        The configuration dictionary containing all loaded settings.

        Returns
        --------------------
        dict of str, Any
            The current configuration dictionary.
        """
        return self._config_dict

    @config_dict.setter
    def config_dict(self, config_dict: dict[str, Any]) -> None:
        """
        Sets a new configuration dictionary.

        Parameters
        --------------------
        config_dict : dict of str, Any
            The new configuration dictionary to set.
        """
        self._config_dict = config_dict

    def load(self, config_path: str | None = None) -> dict[str, Any]:
        """
        Loads configuration data from a file or reloads the current configuration.

        Parameters
        --------------------
        config_path : str or None, optional
            The path to the configuration file. If `None`, reloads the existing configuration (default is None).

        Returns
        --------------------
        dict of str, Any
            The loaded configuration dictionary.

        Examples
        --------------------
        >>> config = Config()
        >>> config_data = config.load("path/to/config.json")
        >>> print(config_data)
        {'setting1': 'value1', 'setting2': 'value2'}
        """
        loader: ConfigLoad = ConfigLoad(config_path)
        config_dict: dict[str, Any] = (
            loader.init_load() if config_path else loader.get_config()
        )
        self.config_dict = config_dict
        return config_dict

    def get_config_entry_option(self, key: str) -> Any | dict[str, Any]:
        """
        Retrieves a specific entry from the configuration dictionary.

        Parameters
        --------------------
        key : str
            The key for the configuration entry to retrieve.

        Returns
        --------------------
        Any and dict of str, Any
            The configuration entry corresponding to the provided key.

        Examples
        --------------------
        >>> config = Config()
        >>> entry_option = config.get_config_entry_option("setting3")
        >>> print(entry_option)
        {'setting4': 'value4'}
        """
        entry_option: dict[str, Any] = self.config_dict.get(key, {})
        return entry_option


class ConfigLoad:
    """
    A utility class for loading and applying configuration files.

    This class handles the discovery of configuration file paths, loading configuration
    data, and applying specific settings such as Matplotlib parameters (`rcParams`) and
    rich traceback settings.

    Attributes
    --------------------
    DEFAULT_CONFIG_NAME : str
        The default name of the configuration file ("gsplot.json").
    config_path : str or None
        The resolved path to the configuration file, if found.

    Parameters
    --------------------
    config_path : str or None, optional
        The explicit path to the configuration file. If not provided, default
        locations will be searched (default is None).

    Methods
    --------------------
    find_config_path(config_path)
        Resolves the configuration file path based on the provided path or default locations.
    init_load()
        Loads the configuration file and applies specific settings if present.
    apply_rc_params(rc_params)
        Applies Matplotlib `rcParams` settings from the configuration file.
    get_config()
        Reads and returns the configuration file as a dictionary.

    Examples
    --------------------
    >>> loader = ConfigLoad()
    >>> config = loader.init_load()
    >>> print(config)
    {'rcParams': {'figure.dpi': 100}, 'rich': {'traceback': {}}}
    """

    DEFAULT_CONFIG_NAME: str = "gsplot.json"

    def __init__(self, config_path: str | None = None) -> None:
        self.config_path: str | None = self.find_config_path(config_path)

    def find_config_path(self, config_path: str | None) -> str | None:
        """
        Determines the configuration file path.

        If a path is provided, it checks its existence. If no path is provided,
        searches default locations for the configuration file.

        Parameters
        --------------------
        config_path : str or None
            The explicit path to the configuration file.

        Returns
        --------------------
        str or None
            The resolved configuration file path, or None if no file is found.

        Raises
        --------------------
        FileNotFoundError
            If the provided path does not exist.

        Examples
        --------------------
        >>> loader = ConfigLoad(config_path="path/to/config.json")
        >>> print(loader.config_path)
        'path/to/config.json'
        """
        if config_path:
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            return config_path

        # Search in default locations
        search_paths = [
            os.getcwd(),  # Current directory
            os.path.join(
                os.path.expanduser("~"), ".config", "gsplot"
            ),  # User config directory
            os.path.expanduser("~"),  # Home directory
        ]

        for path in search_paths:
            potential_path = os.path.join(path, ConfigLoad.DEFAULT_CONFIG_NAME)
            if os.path.exists(potential_path):
                return potential_path
        return None

    def init_load(self) -> dict[str, Any]:
        """
        Loads the configuration file and applies specific settings if present.

        This method reads the configuration file and applies Matplotlib `rcParams`
        and rich traceback settings if they are defined in the configuration.

        Returns
        --------------------
        dict of str, Any
            The loaded configuration dictionary.

        Examples
        --------------------
        >>> loader = ConfigLoad()
        >>> config = loader.init_load()
        >>> print(config)
        {'rcParams': {'figure.dpi': 100}, 'rich': {'traceback': {}}}
        """
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
        """
        Applies Matplotlib `rcParams` settings from the configuration file.

        Parameters
        --------------------
        rc_params : dict of str, Any
            A dictionary of Matplotlib `rcParams` settings.

        Examples
        --------------------
        >>> rc_params = {"figure.dpi": 100, "backend": "TkAgg"}
        >>> ConfigLoad.apply_rc_params(rc_params)
        """
        backend = rc_params.pop("backends", None)
        if backend:
            mpl.use(backend)
        rcParams.update(rc_params)

    def get_config(self) -> dict[str, Any]:
        """
        Reads and returns the configuration file as a dictionary.

        Returns
        --------------------
        dict of str, Any
            The loaded configuration dictionary. Returns an empty dictionary if
            no configuration file is found.

        Examples
        --------------------
        >>> loader = ConfigLoad("path/to/config.json")
        >>> config = loader.get_config()
        >>> print(config)
        {'rcParams': {'figure.dpi': 100}, 'rich': {'traceback': {}}}
        """
        if not self.config_path:
            return {}
        with open(self.config_path, "r") as f:
            return cast(dict[str, Any], json.load(f))


def config_load(config_path: str | None = None) -> dict[str, Any]:
    """
    Loads the configuration data from a specified file or reloads the existing configuration.

    This function initializes the `Config` singleton, loads the configuration file,
    and returns the loaded configuration dictionary.

    Parameters
    --------------------
    config_path : str or None, optional
        The path to the configuration file. If `None`, the existing configuration is reloaded (default is None).

    Returns
    --------------------
    dict of str, Any
        The loaded configuration dictionary.

    Examples
    --------------------
    >>> import gsplot as gs
    >>> config_data = gs.config_load("path/to/config.json")
    >>> print(config_data)
    {'rcParams': {'figure.dpi': 100}, 'rich': {'traceback': {}}}
    """
    _config: Config = Config()
    config_dict: dict[str, Any] = _config.load(config_path)
    return config_dict


def config_dict() -> dict[str, Any]:
    """
    Retrieves the current configuration dictionary.

    This function accesses the `Config` singleton and returns the configuration
    dictionary currently in memory.

    Returns
    --------------------
    dict of str, Any
        The current configuration dictionary.

    Examples
    --------------------
    >>> import gsplot as gs
    >>> config_data = gs.config_dict()
    >>> print(config_data)
    {'rcParams': {'figure.dpi': 100}, 'rich': {'traceback': {}}}
    """
    _config: Config = Config()
    config_dict: dict[str, Any] = _config.config_dict
    return config_dict


def config_entry_option(key: str) -> dict[str, Any]:
    """
    Retrieves a specific entry from the configuration dictionary based on the provided key.

    This function accesses the `Config` singleton and retrieves the configuration
    entry associated with the given key.

    Parameters
    --------------------
    key : str
        The key for the configuration entry to retrieve.

    Returns
    --------------------
    dict of str, Any
        The configuration entry corresponding to the provided key.

    Examples
    --------------------
    >>> import gsplot as gs
    >>> entry_option = gs.config_entry_option("rcParams")
    >>> print(entry_option)
    {'figure.dpi': 100, 'backend': 'TkAgg'}
    """
    _config: Config = Config()
    entry_option: dict[str, Any] = _config.get_config_entry_option(key)
    return entry_option
