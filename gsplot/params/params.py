from ..data.path import Path
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


class Params:
    """
    A singleton class for managing application parameters stored as key-value pairs.

    The `Params` class is designed to manage and store parameters in a dictionary. It ensures
    that only one instance of the class exists (singleton pattern), making the parameters accessible
    globally within the application.

    Attributes
    ----------
    _instance : Optional[Params]
        The singleton instance of the `Params` class.
    _params : Dict[str, Any]
        A dictionary storing the application parameters.

    Methods
    -------
    params -> Dict[str, Any]
        Gets the current parameters dictionary.
    params(params: Dict[str, Any]) -> None
        Sets the parameters dictionary.
    get_item(key: str) -> Dict[str, Any]
        Retrieves the parameters associated with the given key.
    """

    _instance: Optional["Params"] = None

    def __new__(cls) -> "Params":
        if cls._instance is None:
            cls._instance = super(Params, cls).__new__(cls)
            cls._instance._initialize_params()
        return cls._instance

    def _initialize_params(self) -> None:
        """
        Initializes the parameters dictionary.

        This method is called once during the creation of the singleton instance to set up
        the internal `_params` dictionary.
        """

        self._params: Dict[str, Any] = {}

    @property
    def params(self) -> Dict[str, Any]:
        """
        Gets the current parameters dictionary.

        Returns
        -------
        Dict[str, Any]
            The dictionary storing the application parameters.
        """

        return self._params

    @params.setter
    def params(self, params: Dict[str, Any]) -> None:
        """
        Sets the parameters dictionary.

        Parameters
        ----------
        params : Dict[str, Any]
            The dictionary to set as the application parameters.

        Raises
        ------
        TypeError
            If the provided `params` is not a dictionary.
        """

        if not isinstance(params, dict):
            raise TypeError(f"Expected type dict, got {type(params).__name__}")
        self._params = params

    def get_item(self, key: str) -> Dict[str, Any]:
        """
        Retrieves the parameters associated with the given key.

        Parameters
        ----------
        key : str
            The key for which to retrieve the associated parameters.

        Returns
        -------
        Dict[str, Any]
            A dictionary of parameters associated with the given key.

        Raises
        ------
        ValueError
            If the retrieved item is not a dictionary.
        """

        try:
            params_instance = Params()
            key_params = params_instance.params.get(key, {})
            if isinstance(key_params, dict):
                return key_params
            else:
                raise ValueError("Expected a dictionary")
        except Exception:
            return dict[str, Any]()


class LoadParams:
    """
    A class for loading and applying configuration parameters from a JSON file.

    The `LoadParams` class is responsible for loading application-specific configuration
    parameters from a JSON file (default: `~/.gsplot.json`). These parameters are used to
    configure matplotlib settings, such as `rcParams` and backends.

    Attributes
    ----------
    home : str
        The path to the user's home directory.
    config_fname : str
        The name of the configuration file.
    config_path : str
        The full path to the configuration file.

    Methods
    -------
    _init_load() -> None
        Loads parameters from the configuration file and applies them to matplotlib settings.
    load_params() -> Dict[str, Any]
        Loads the parameters from the JSON configuration file.
    """

    def __init__(self) -> None:
        self.home: str = Path().get_home()
        self.config_fname: str = ".gsplot.json"
        self.config_path: str = f"{self.home}/{self.config_fname}"

        try:
            self._init_load()
        except Exception:
            pass

    def _init_load(self) -> None:
        """
        Loads parameters from the configuration file and applies them to matplotlib settings.

        This method reads the configuration file, retrieves the `rcParams`, and applies the
        relevant settings to matplotlib, such as setting the backend and other parameters.
        """

        params: Dict[str, Any] = self.load_params()
        rcparams: Dict[str, Any] = params["rcParams"]

        if "backends" in rcparams:
            val_bes: str = rcparams["backends"]
            mpl.use(val_bes)

        for key in rcparams:
            if key != "backends":
                rcParams[key] = rcparams[key]

    # def load_params(self) -> Dict[str, Any]:
    #     """
    #     Loads the parameters from the JSON configuration file.
    #
    #     This method reads the configuration file located at `self.config_path`, parses it,
    #     and returns the parameters as a dictionary. The parameters are also stored in the
    #     `Params` singleton for global access.
    #
    #     Returns
    #     -------
    #     Dict[str, Any]
    #         A dictionary containing the loaded parameters.
    #
    #     Raises
    #     ------
    #     ValueError
    #         If there is an error reading or parsing the JSON configuration file.
    #     """
    #
    #     try:
    #         with open(self.config_path, "r") as f:
    #             params: Dict[str, Any] = json.load(f)
    #
    #         instance_Params: Params = Params()
    #         instance_Params.params = params
    #         return params
    #
    #     # get error of syntax error of json file
    #     except Exception as e:
    #         raise ValueError(f"Error in reading ~/.gsplot.json: {e}")
    def load_params(self) -> Dict[str, Any]:
        """
        Loads the parameters from the JSON configuration file.

        This method reads the configuration file located at `self.config_path`, parses it,
        and returns the parameters as a dictionary. The parameters are also stored in the
        `Params` singleton for global access.

        Returns
        -------
        Dict[str, Any]
            A dictionary containing the loaded parameters. If the configuration file does
            not exist, returns an empty dictionary or default parameters.

        Raises
        ------
        ValueError
            If there is an error reading or parsing the JSON configuration file, other than
            the file not being found.
        """

        instance_Params: Params = Params()
        try:
            with open(self.config_path, "r") as f:
                params: Dict[str, Any] = json.load(f)

            instance_Params.params = params
            return params

        except FileNotFoundError:
            # Provide default parameters or handle the situation gracefully
            default_params: Dict[str, Any] = {}
            instance_Params.params = default_params
            return default_params

        except Exception as e:
            raise ValueError(f"Error in reading ~/.gsplot.json: {e}")


def get_json_params() -> Dict[str, Any]:
    """
    Retrieves the current parameters stored in the `Params` singleton.

    This function provides access to the parameters that have been loaded and stored by the
    `LoadParams` class.

    Returns
    -------
    Dict[str, Any]
        A dictionary containing the current parameters.
    """

    instance_Params = Params()
    params = instance_Params.params
    return params
