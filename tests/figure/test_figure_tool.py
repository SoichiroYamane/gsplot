from unittest.mock import patch

import numpy as np

from gsplot.figure.figure_tools import FigureLayout


def test_get_figure_size_reads_the_current_figure() -> None:
    with patch("matplotlib.pyplot.gcf") as mock_gcf:
        mock_gcf.return_value.get_size_inches.return_value = np.array([6.0, 4.0])

        figure_layout = FigureLayout()

        np.testing.assert_array_equal(
            figure_layout.get_figure_size(), np.array([6.0, 4.0])
        )
