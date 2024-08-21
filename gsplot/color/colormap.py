import numpy as np
import matplotlib as mpl
from typing import Optional


class Colormap:
    """
    A class to handle the creation and manipulation of colormaps using matplotlib.

    Attributes
    ----------
    DEFAULT_N : int
        The default number of colors in the colormap if `N` is not provided.
    cmap : str
        The name of the colormap to be used.
    cmap_ndarray : np.ndarray
        The array representing the colormap data.
    normalize : bool
        Whether to normalize the colormap data.

    Methods
    -------
    _initialize_cmap_ndarray(N: Optional[int], ndarray: Optional[np.ndarray]) -> np.ndarray
        Initializes the colormap data based on the number of colors or a provided array.
    get_split_cmap() -> np.ndarray
        Returns the colormap array, optionally normalized, split into RGB or RGBA values.
    _normalize(ndarray: np.ndarray) -> np.ndarray
        Normalizes the input array to the range [0, 1].
    """

    DEFAULT_N: int = 10

    def __init__(
        self,
        cmap: str = "viridis",
        N: Optional[int] = None,
        ndarray: Optional[np.ndarray] = None,
        normalize: bool = True,
    ) -> None:
        """
        Initializes the Colormap instance with the provided colormap name, number of colors,
        colormap data array, and normalization option.

        Parameters
        ----------
        cmap : str, optional
            The name of the colormap to be used (default is "viridis").
        N : Optional[int], optional
            The number of colors to generate in the colormap (default is None).
            If specified, `ndarray` must be None.
        ndarray : Optional[np.ndarray], optional
            An array representing colormap data (default is None).
            If specified, `N` must be None.
        normalize : bool, optional
            Whether to normalize the colormap data (default is True).
        """

        self.cmap: str = cmap
        self.cmap_ndarray: np.ndarray = self._initialize_cmap_ndarray(N, ndarray)
        self.normalize: bool = normalize

    def _initialize_cmap_ndarray(
        self, N: Optional[int], ndarray: Optional[np.ndarray]
    ) -> np.ndarray:
        """
        Initializes the colormap data based on the number of colors or a provided array.

        Parameters
        ----------
        N : Optional[int], optional
            The number of colors to generate in the colormap (default is None).
        ndarray : Optional[np.ndarray], optional
            An array representing colormap data (default is None).

        Returns
        -------
        np.ndarray
            An array representing the colormap data.

        Raises
        ------
        ValueError
            If both `N` and `ndarray` are provided.
        """

        if N is not None and ndarray is not None:
            raise ValueError("Only one of N and ndarray can be specified.")
        if N is not None:
            return np.linspace(0, 1, N)
        if ndarray is not None:
            return ndarray
        return np.linspace(0, 1, self.DEFAULT_N)

    def get_split_cmap(self) -> np.ndarray:
        """
        Returns the colormap array, optionally normalized, split into RGB or RGBA values.

        Returns
        -------
        np.ndarray
            An array of RGB or RGBA values representing the colormap.
        """

        if self.normalize:
            cmap_data = self._normalize(self.cmap_ndarray)
        else:
            cmap_data = self.cmap_ndarray
        return np.array(mpl.colormaps.get_cmap(self.cmap)(cmap_data))

    @staticmethod
    def _normalize(ndarray: np.ndarray) -> np.ndarray:
        """
        Normalizes the input array to the range [0, 1].

        Parameters
        ----------
        ndarray : np.ndarray
            The array to be normalized.

        Returns
        -------
        np.ndarray
            The normalized array.
        """

        return np.array(
            (ndarray - np.min(ndarray)) / (np.max(ndarray) - np.min(ndarray))
        )


def get_cmap(
    cmap: str = "viridis",
    N: int = 10,
    ndarray: Optional[np.ndarray] = None,
    normalize: bool = True,
) -> np.ndarray:
    """
    Returns a colormap array based on the provided colormap name, number of colors,
    colormap data array, and normalization option.

    Parameters
    ----------
    cmap : str, optional
        The name of the colormap to be used (default is "viridis").
    N : int, optional
        The number of colors to generate in the colormap (default is 10).
        Ignored if `ndarray` is provided.
    ndarray : Optional[np.ndarray], optional
        An array representing colormap data (default is None).
        If provided, `N` is ignored.
    normalize : bool, optional
        Whether to normalize the colormap data (default is True).

    Returns
    -------
    np.ndarray
        An array of RGB or RGBA values representing the colormap.
    """

    return Colormap(cmap, N, ndarray, normalize).get_split_cmap()
