import pytest
from unittest.mock import patch
import numpy as np
from gsplot.figure.figure_tool import FigureLayout


class TestFigureLayout:
    @patch("matplotlib.pyplot.gcf")
    def test_get_figure_size(self, mock_gcf):
        # Mocking gcf().get_size_inches() to return a numpy array
        mock_gcf.return_value.get_size_inches.return_value = np.array([6.0, 4.0])

        # Creating instance of FigureLayout
        figure_layout = FigureLayout()

        # Asserting that get_figure_size method works as expected
        assert np.array_equal(figure_layout.get_figure_size(), np.array([6.0, 4.0]))
