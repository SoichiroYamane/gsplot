import numpy as np
import matplotlib as mpl


class Colormap:
    DEFAULT_N = 10

    def __init__(self, cmap="viridis", N=None, ndarray=None, normalize=True):
        self.cmap = cmap
        self.cmap_ndarray = self._initialize_cmap_ndarray(N, ndarray)
        self.normalize = normalize

    def _initialize_cmap_ndarray(self, N, ndarray):
        if N is not None and ndarray is not None:
            raise ValueError("Only one of N and ndarray can be specified.")
        if N is not None:
            return np.linspace(0, 1, N)
        if ndarray is not None:
            return ndarray
        return np.linspace(0, 1, self.DEFAULT_N)

    def get_split_cmap(self) -> np.ndarray:
        if self.normalize:
            cmap_data = self._normalize(self.cmap_ndarray)
        else:
            cmap_data = self.cmap_ndarray
        return mpl.colormaps.get_cmap(self.cmap)(cmap_data)

    @staticmethod
    def _normalize(ndarray):
        return (ndarray - np.min(ndarray)) / (np.max(ndarray) - np.min(ndarray))
