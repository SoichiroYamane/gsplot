from typing import Any

import numpy as np
from matplotlib.colors import Normalize
from numpy.typing import ArrayLike, NDArray

__all__: list[str] = []


class LineColormapBase:
    """
    A base class for creating line segments and color maps for line plotting.

    The `LineColormapBase` class provides utility functions for creating line segments
    and generating color maps that can be used for line plots with varying colors along the line.

    Methods
    -------
    _create_segment(xdata: NDArray[Any], ydata: NDArray[Any]) -> NDArray[np.float64]
        Creates line segments from x and y data points for plotting.
    _create_cmap(cmapdata: NDArray[Any]) -> Normalize
        Creates a normalization object for mapping data points to colors.
    """

    def _create_segment(self, x: ArrayLike, y: ArrayLike) -> NDArray[np.float64]:
        """
        Creates line segments from x and y data points for plotting.

        Parameters
        ----------
        xdata : NDArray[Any]
            The x-axis data points.
        ydata : NDArray[Any]
            The y-axis data points.

        Returns
        -------
        NDArray[np.float64]
            An array of line segments, each represented as a pair of points (x, y).
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

        # Create a continuous norm to map from data points to colors
        if len(cmapdata) >= 2:
            # delete maximun data
            cmapdata = np.delete(cmapdata, np.where(cmapdata == np.max(cmapdata)))
        norm = Normalize(cmapdata.min(), cmapdata.max())

        return norm
