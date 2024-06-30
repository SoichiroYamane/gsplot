import pytest
import numpy as np
from gsplot.color.colormap import Colormap


class TestColormap:
    def test_initialize_cmap_ndarray(self):
        colormap = Colormap(N=5)
        assert np.array_equal(colormap.cmap_ndarray, np.linspace(0, 1, 5))

        colormap = Colormap(ndarray=np.array([0, 0.5, 1]))
        assert np.array_equal(colormap.cmap_ndarray, np.array([0, 0.5, 1]))

        with pytest.raises(ValueError):
            Colormap(N=5, ndarray=np.array([0, 0.5, 1]))

    def test_get_split_cmap(self):
        colormap = Colormap(N=5)
        assert colormap.get_split_cmap().shape == (5, 4)

        colormap = Colormap(ndarray=np.array([0, 0.5, 1]))
        assert colormap.get_split_cmap().shape == (3, 4)

    def test_normalize(self):
        assert np.array_equal(
            Colormap._normalize(np.array([1, 2, 3])), np.array([0, 0.5, 1])
        )
