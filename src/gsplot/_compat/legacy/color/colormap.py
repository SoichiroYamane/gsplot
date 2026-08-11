from typing import Any

import matplotlib as mpl
import numpy as np
from numpy.typing import ArrayLike, NDArray

from ..base.base import CreateClassParams, ParamsGetter, bind_passed_params

__all__: list[str] = ["get_cmap"]


class Colormap:
    """
    A utility class for managing and generating colormap data for visualization.

    This class allows for the creation of normalized and reversed colormap arrays
    using Matplotlib colormaps.

    Attributes
    --------------------
    DEFAULT_N : int
        The default number of evenly spaced values to generate when no colormap data
        or number of points (N) is provided.
    cmap : str
        The name of the Matplotlib colormap to use.
    cmap_data : numpy.ndarray
        The array of colormap data, either generated or provided.
    normalize : bool
        Whether to normalize the colormap data.
    reverse : bool
        Whether to reverse the colormap data.

    Parameters
    --------------------
    cmap : str, optional
        The name of the Matplotlib colormap to use (default is "viridis").
    N : int, optional
        The number of evenly spaced values to generate for the colormap data.
        If specified, `cmap_data` must be `None`.
    cmap_data : array-like, optional
        Custom colormap data to use. If specified, `N` must be `None`.
    normalize : bool, optional
        Whether to normalize the colormap data (default is True).
    reverse : bool, optional
        Whether to reverse the colormap data (default is False).

    Methods
    --------------------
    get_split_cmap()
        Generates the final colormap array, applying normalization and reversal if specified.
    _initialize_cmap_data(N, cmap_data)
        Initializes the colormap data based on the number of points or a custom array.
    _normalize(ndarray)
        Normalizes an array to the range [0, 1].

    Examples
    --------------------
    >>> colormap = Colormap(cmap="plasma", N=5, normalize=True, reverse=True)
    >>> print(colormap.get_split_cmap())
    [[0.940015  0.975158  0.131326  1.      ]
     [0.647257  0.107541  0.508936  1.      ]
     [0.20803   0.05997   0.481219  1.      ]
     [0.069447  0.037392  0.283268  1.      ]
     [0.050383  0.029803  0.527975  1.      ]]
    """

    DEFAULT_N: int = 10

    def __init__(
        self,
        cmap: str = "viridis",
        N: int | None = None,
        cmap_data: ArrayLike | None = None,
        normalize: bool = True,
        reverse: bool = False,
    ) -> None:

        self.cmap: str = cmap
        self.cmap_data: NDArray[Any] = self._initialize_cmap_data(N, cmap_data)
        self.normalize: bool = normalize
        self.reverse: bool = reverse

    def _initialize_cmap_data(
        self, N: int | None, cmap_data: ArrayLike | None
    ) -> NDArray[Any]:
        """
        Initializes the colormap data based on the provided number of points or custom array.

        Parameters
        ----------
        N : int, optional
            The number of evenly spaced values to generate. If specified, `cmap_data` must be `None`.
        cmap_data : array-like, optional
            Custom colormap data to use. If specified, `N` must be `None`.

        Returns
        -------
        numpy.ndarray
            The initialized colormap data.

        Raises
        --------------------
        ValueError
            If both `N` and `cmap_data` are provided.
        """
        if N is not None and cmap_data is not None:
            raise ValueError("Only one of N and ndarray can be specified.")
        if N is not None:
            return np.linspace(0, 1, N)
        if cmap_data is not None:
            return np.array(cmap_data)
        return np.linspace(0, 1, self.DEFAULT_N)

    def get_split_cmap(self) -> NDArray[Any]:
        """
        Generates the final colormap array, applying normalization and reversal if specified.

        Returns
        --------------------
        numpy.ndarray
            The final colormap array with RGBA values.
        """
        if self.normalize:
            cmap_data = self._normalize(self.cmap_data)
        else:
            cmap_data = self.cmap_data
        if self.reverse:
            cmap_data = cmap_data[::-1]
        return np.array(mpl.colormaps.get_cmap(self.cmap)(cmap_data))

    @staticmethod
    def _normalize(ndarray: NDArray[Any]) -> NDArray[Any]:
        """
        Normalizes an array to the range [0, 1].

        Parameters
        --------------------
        ndarray : numpy.ndarray
            The array to normalize.

        Returns
        --------------------
        numpy.ndarray
            The normalized array.
        """
        return np.array(
            (ndarray - np.min(ndarray)) / (np.max(ndarray) - np.min(ndarray))
        )


@bind_passed_params()
def get_cmap(
    cmap: str = "viridis",
    N: int | None = 10,
    cmap_data: ArrayLike | None = None,
    normalize: bool = True,
    reverse: bool = False,
) -> NDArray[Any]:
    """
    Generates a colormap array using the specified parameters.

    This function provides a convenient interface to create and customize
    colormaps using Matplotlib's colormap utilities. Parameters can be passed
    directly or via a `Colormap` class.

    Parameters
    --------------------
    cmap : str, optional
        The name of the Matplotlib colormap to use (default is "viridis").
    N : int or None, optional
        The number of evenly spaced values to generate for the colormap data.
        If `None`, `cmap_data` must be provided (default is 10).
    cmap_data : array-like or None, optional
        Custom colormap data to use. If specified, `N` must be `None` (default is None).
    normalize : bool, optional
        Whether to normalize the colormap data to the range [0, 1] (default is True).
    reverse : bool, optional
        Whether to reverse the colormap data (default is False).

    Notes
    --------------------
    This function utilizes the `ParamsGetter` to retrieve bound parameters and
    the `CreateClassParams` class to handle the merging of default, configuration,
    and passed parameters.

    Returns
    --------------------
    numpy.ndarray
        The generated colormap array as an RGBA numpy array.

    Raises
    --------------------
    ValueError
        If both `N` and `cmap_data` are provided simultaneously.

    Examples
    --------------------
    >>> import gsplot as gs
    >>> colormap_array = gs.get_cmap(cmap="plasma", N=5, normalize=True, reverse=True)
    >>> print(colormap_array)
    [[0.940015  0.975158  0.131326  1.      ]
     [0.647257  0.107541  0.508936  1.      ]
     [0.20803   0.05997   0.481219  1.      ]
     [0.069447  0.037392  0.283268  1.      ]
     [0.050383  0.029803  0.527975  1.      ]]
    """
    passed_params: dict[str, Any] = ParamsGetter("passed_params").get_bound_params()
    class_params = CreateClassParams(passed_params).get_class_params()

    _colormap: Colormap = Colormap(
        class_params["cmap"],
        class_params["N"],
        class_params["cmap_data"],
        class_params["normalize"],
        class_params["reverse"],
    )

    return _colormap.get_split_cmap()
