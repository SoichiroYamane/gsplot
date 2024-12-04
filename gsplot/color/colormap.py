from typing import Any

import matplotlib as mpl
import numpy as np
from numpy.typing import ArrayLike, NDArray

from ..base.base import CreateClassParams, ParamsGetter, bind_passed_params

__all__: list[str] = ["get_cmap"]


class Colormap:

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

        if N is not None and cmap_data is not None:
            raise ValueError("Only one of N and ndarray can be specified.")
        if N is not None:
            return np.linspace(0, 1, N)
        if cmap_data is not None:
            return np.array(cmap_data)
        return np.linspace(0, 1, self.DEFAULT_N)

    def get_split_cmap(self) -> NDArray[Any]:

        if self.normalize:
            cmap_data = self._normalize(self.cmap_data)
        else:
            cmap_data = self.cmap_data
        if self.reverse:
            cmap_data = cmap_data[::-1]
        return np.array(mpl.colormaps.get_cmap(self.cmap)(cmap_data))

    @staticmethod
    def _normalize(ndarray: NDArray[Any]) -> NDArray[Any]:

        return np.array(
            (ndarray - np.min(ndarray)) / (np.max(ndarray) - np.min(ndarray))
        )


# !TODO: Modify docstring
@bind_passed_params()
def get_cmap(
    cmap: str = "viridis",
    N: int | None = 10,
    cmap_data: ArrayLike | None = None,
    normalize: bool = True,
    reverse: bool = False,
) -> NDArray[Any]:
    """
    Generate a customized colormap based on the specified parameters.

    This function creates a colormap object with the specified configuration and
    returns a segmented colormap as a NumPy array. It allows for customization of
    the colormap's resolution, data normalization, and reversal.

    Parameters
    ----------
    cmap : str, optional
        The name of the colormap to use. Default is "viridis".
    N : int or None, optional
        The number of discrete levels in the colormap. If None, it uses the default
        number of levels for the specified colormap. Default is 10.
    cmap_data : ArrayLike or None, optional
        Custom colormap data as an array-like structure. If None, the colormap is
        generated based on the `cmap` parameter. Default is None.
    normalize : bool, optional
        Whether to normalize the colormap data. If True, values will be scaled to
        fit within the range [0, 1]. Default is True.
    reverse : bool, optional
        Whether to reverse the colormap. If True, the colormap's colors are inverted.
        Default is False.

    Returns
    -------
    NDArray[Any]
        A NumPy array representing the segmented colormap.

    Notes
    -----
    - The colormap is generated using a `Colormap` class, which takes the input
      parameters and applies additional processing.
    - The function uses the `ParamsGetter` class to capture the passed arguments
      and generate parameters for the `Colormap` object.

    Examples
    --------
    Create a default colormap:

    >>> get_cmap()
    array([...])  # Output depends on the colormap resolution and settings.

    Create a reversed colormap with 20 levels:

    >>> get_cmap(cmap="plasma", N=20, reverse=True)
    array([...])  # Output with inverted "plasma" colormap.

    Use custom colormap data:

    >>> cmap_data = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]  # RGB values
    >>> get_cmap(cmap_data=cmap_data, normalize=False)
    array([...])
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
