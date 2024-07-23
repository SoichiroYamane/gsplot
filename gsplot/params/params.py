from ..data.path import Path
import os
import json

from typing import List, Any, Optional, Dict

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
    _instance: Optional["Params"] = None

    def __new__(cls) -> "Params":
        if cls._instance is None:
            cls._instance = super(Params, cls).__new__(cls)
            cls._instance._initialize_params()
        return cls._instance

    def _initialize_params(self) -> None:
        self._params: Dict[str, Any] = {}

    @property
    def params(self) -> Dict[str, Any]:
        return self._params

    @params.setter
    def params(self, params: Dict[str, Any]) -> None:
        if not isinstance(params, dict):
            raise TypeError(f"Expected type dict, got {type(params).__name__}")
        self._params = params

    def get_item(self, key: str) -> Dict[str, Any]:
        try:
            params_instance = Params()
            key_params = params_instance.params.get(key, {})
            if isinstance(key_params, dict):
                return key_params
            else:
                raise ValueError("Expected a dictionary")
        except Exception:
            return dict[str, Any]()


# class LoadParams:
#     def __init__(self) -> None:
#         self.home = Path().get_home()
#         self.config_fname = ".gsplot.json"
#         self.config_path = f"{self.home}/{self.config_fname}"
#
#         try:
#             self._init_load()
#         except Exception:
#             pass
#
#     def _init_load(self):
#         params = self.load_params()
#
#         rcparams = params["rcParams"]
#
#         if "backends" in rcparams:
#             val_bes = rcparams["backends"]
#             mpl.use(val_bes)
#
#         for key in rcparams:
#             if key != "backends":
#                 rcParams[key] = rcparams[key]
#
#     def load_params(self):
#         try:
#             try:
#                 with open(self.config_path, "r") as f:
#                     params = json.load(f)
#
#                 instance_Params = Params()
#                 instance_Params.params = params
#                 return params
#
#             # get error of syntax error of json file
#             except Exception as e:
#                 raise ValueError(f"Error in reading ~/.gsplot.json: {e}")
#         except:
#             pass
#


class LoadParams:
    def __init__(self) -> None:
        self.home: str = Path().get_home()
        self.config_fname: str = ".gsplot.json"
        self.config_path: str = f"{self.home}/{self.config_fname}"

        try:
            self._init_load()
        except Exception:
            pass

    def _init_load(self) -> None:
        params: Dict[str, Any] = self.load_params()

        rcparams: Dict[str, Any] = params["rcParams"]

        if "backends" in rcparams:
            val_bes: str = rcparams["backends"]
            mpl.use(val_bes)

        for key in rcparams:
            if key != "backends":
                rcParams[key] = rcparams[key]

    def load_params(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, "r") as f:
                params: Dict[str, Any] = json.load(f)

            instance_Params: Params = Params()
            instance_Params.params = params
            return params

        # get error of syntax error of json file
        except Exception as e:
            raise ValueError(f"Error in reading ~/.gsplot.json: {e}")


def get_json_params() -> Dict[str, Any]:
    instance_Params = Params()
    params = instance_Params.params
    return params
