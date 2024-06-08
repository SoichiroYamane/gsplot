import numpy as np


class LoadFile:
    def __init__(self, f):
        self.f = f
        pass

    def load_txt(self, *args, **kwargs):
        return np.genfromtxt(self.f, *args, **kwargs)
