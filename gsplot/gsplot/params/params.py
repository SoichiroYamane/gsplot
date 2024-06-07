import os
import json


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
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Params, cls).__new__(cls)
            cls._instance.params = {}
        return cls._instance

    @property
    def params(self):
        return self._instance.params

    @params.setter
    def params(self, params):
        if not isinstance(params, dict):
            raise TypeError(f"Expected type dict, got {type(params).__name__}")
        self._instance.params = params

    def getitem(self, key):
        try:
            key_params = Params.params[key]
            return key_params
        except:
            return {}


try:
    try:
        with open(f"{home}/.gsplot.json", "r") as f:
            params = json.load(f)
            Params.params = params
            rcparams = params["rcParams"]

            if "backends" in rcparams:
                val_bes = rcparams["backends"]
                mpl.use(val_bes)

            for key in rcparams:
                if key != "backends":
                    rcParams[key] = rcparams[key]

            test = Params.params

    # get error of syntax error of json file
    except Exception as e:
        raise ValueError(f"Error in reading ~/.gsplot.json: {e}")
except:
    pass
