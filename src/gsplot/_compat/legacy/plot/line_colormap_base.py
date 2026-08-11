from typing import Any

import numpy as np
from matplotlib.colors import Normalize
from numpy.typing import ArrayLike, NDArray

__all__: list[str] = []


class LineColormapBase:
    """
    A base class for creating colormaps and segments for line collections.

    This class provides utility methods to create line segments for plotting with
    individual colors and to normalize data for applying colormaps.

    Methods
    --------------------
    _create_segment(x, y)
        Creates a set of line segments for line collections, enabling individual
        segment coloring.
    _create_cmap(cmapdata)
        Creates a normalization object for mapping data points to colors.

    Examples
    --------------------
    >>> line_base = LineColormapBase()
    >>> x = np.array([0, 1, 2, 3])
    >>> y = np.array([1, 2, 3, 4])
    >>> segments = line_base._create_segment(x, y)
    >>> print(segments.shape)
    (3, 2, 2)  # Shape: (numlines, points per line, x and y)

    >>> cmapdata = np.array([0.1, 0.4, 0.6, 0.9])
    >>> norm = line_base._create_cmap(cmapdata)
    >>> print(norm(cmapdata))
    [0.   0.5  0.83333333 1.  ]  # Normalized data
    """

    def _create_segment(self, x: ArrayLike, y: ArrayLike) -> NDArray[np.float64]:
        """
        Creates a set of line segments for line collections, enabling individual segment coloring.

        The method converts the input x and y arrays into a collection of segments
        suitable for use with Matplotlib's `LineCollection`. Each segment connects two
        adjacent points from the input arrays.

        Parameters
        --------------------
        x : ArrayLike
            The x-coordinates of the points.
        y : ArrayLike
            The y-coordinates of the points.

        Returns
        --------------------
        numpy.ndarray
            An array of shape `(numlines, 2, 2)` representing the line segments,
            where each segment is defined by two points `(x, y)`.

        Examples
        --------------------
        >>> x = np.array([0, 1, 2, 3])
        >>> y = np.array([1, 2, 3, 4])
        >>> line_base = LineColormapBase()
        >>> segments = line_base._create_segment(x, y)
        >>> print(segments.shape)
        (3, 2, 2)  # Shape: (numlines, points per line, x and y)
        """

        # ╭──────────────────────────────────────────────────────────╮
        # │ Create a set of line segments so that we can color them  │
        # │ individually                                             │
        # │ This creates the points as an N x 1 x 2 array so that    │
        # │ we can stack points                                      │
        # │ together easily to get the segments. The segments array  │
        # │ for line collection                                      │
        # │ needs to be (numlines) x (points per line) x 2 (for x    │
        # │ and y)                                                   │
        # ╰──────────────────────────────────────────────────────────╯
        points = np.array([x, y], dtype=np.float64).T.reshape(-1, 1, 2)
        segments: NDArray[np.float64] = np.concatenate(
            [points[:-1], points[1:]], axis=1
        )
        return segments

    def _create_cmap(self, cmapdata: NDArray[Any]) -> Normalize:
        """
        Creates a normalization object for mapping data points to colors.

        This method generates a `Normalize` object from Matplotlib, which scales
        input data to the range `[0, 1]` for use in colormaps. If the input data has
        at least two elements, the maximum value is removed to prevent color saturation.

        Parameters
        --------------------
        cmapdata : numpy.ndarray
            The input data for normalization.

        Returns
        --------------------
        matplotlib.colors.Normalize
            A normalization object mapping `cmapdata.min()` to 0 and `cmapdata.max()` to 1.

        Examples
        --------------------
        >>> cmapdata = np.array([0.1, 0.4, 0.6, 0.9])
        >>> line_base = LineColormapBase()
        >>> norm = line_base._create_cmap(cmapdata)
        >>> print(norm(cmapdata))
        [0.   0.5  0.83333333 1.  ]  # Normalized data
        """

        # Create a continuous norm to map from data points to colors
        if len(cmapdata) >= 2:
            # delete maximun data
            cmapdata = np.delete(cmapdata, np.where(cmapdata == np.max(cmapdata)))
        norm = Normalize(cmapdata.min(), cmapdata.max())

        return norm
