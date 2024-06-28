import pytest
from unittest.mock import MagicMock, patch
from matplotlib.axes import Axes
from gsplot.figure.axes import UnitConv, Unit, AxesHandler


class TestUnitConv:
    def setup_method(self):
        # Creating instance of UnitConv
        self.unit_conv = UnitConv()

    def test_convert(self):
        # Asserting that convert method works as expected
        assert self.unit_conv.convert(1, Unit.MM) == pytest.approx(1 / 25.4)
        assert self.unit_conv.convert(1, Unit.CM) == pytest.approx(1 / 2.54)
        assert self.unit_conv.convert(1, Unit.IN) == pytest.approx(1)
        assert self.unit_conv.convert(1, Unit.PT) == pytest.approx(1 / 72)

        # Asserting that convert method raises a ValueError when the unit is invalid
        with pytest.raises(ValueError):
            self.unit_conv.convert(1, Unit.INVALID)


class TestAxesHandler:
    def setup_method(self):
        # Creating instance of AxesHandler
        self.axes_handler = AxesHandler(mosaic="AB")

    @patch("matplotlib.pyplot.gcf")
    @patch("matplotlib.pyplot.ion")
    def test_init_ion(self, mock_ion, mock_gcf):
        # Mocking Axes class
        mock_axes1 = MagicMock(spec=Axes)
        mock_axes2 = MagicMock(spec=Axes)

        # Mocking gcf().subplot_mosaic() to return a dictionary of mock Axes
        mock_gcf.return_value.subplot_mosaic.return_value = {
            "A": mock_axes1,
            "B": mock_axes2,
        }

        # Asserting that ion() was called if self.ion is True
        self.axes_handler.ion = True
        self.axes_handler._open_figure()
        mock_ion.assert_called_once()

        # Reset the mock objects
        mock_ion.reset_mock()
        mock_gcf.reset_mock()

    @patch("matplotlib.pyplot.gcf")
    @patch("matplotlib.pyplot.ion")
    def test_init_clear(self, mock_ion, mock_gcf):
        # Mocking Axes class
        mock_axes1 = MagicMock(spec=Axes)
        mock_axes2 = MagicMock(spec=Axes)

        # Mocking gcf().subplot_mosaic() to return a dictionary of mock Axes
        mock_gcf.return_value.subplot_mosaic.return_value = {
            "A": mock_axes1,
            "B": mock_axes2,
        }

        # Asserting that gcf().clear() was called if self.clear is True
        self.axes_handler.clear = True
        self.axes_handler._open_figure()
        mock_gcf.return_value.clear.assert_called_once()

        # Asserting that gcf().set_size_inches() is called with the correct arguments
        expected_size = [
            int(x) for x in (5.0, 5.0)
        ]  # Replace with your expected size tuple

        self.axes_handler.size = expected_size  # Set the expected size

        # Reset the mock objects before invoking _open_figure() again
        mock_gcf.return_value.reset_mock()

        # Call _open_figure() again to trigger set_size_inches()
        self.axes_handler._open_figure()

        # Assert that set_size_inches() was called exactly once with expected_size
        mock_gcf.return_value.set_size_inches.assert_called_once_with(*expected_size)

        # Asserting that the axes were correctly set
        assert self.axes_handler.get_axes == [mock_axes1, mock_axes2]

        # Reset the mock objects
        mock_ion.reset_mock()
        mock_gcf.reset_mock()

    @patch("matplotlib.pyplot.gcf")
    @patch("matplotlib.pyplot.ion")
    def test_invalid_mosaic(self, mock_ion, mock_gcf):
        # Asserting that a ValueError is raised when mosaic is an empty string
        with pytest.raises(ValueError):
            self.axes_handler.mosaic = ""
            self.axes_handler._open_figure()

        # Reset the mock objects
        mock_ion.reset_mock()
        mock_gcf.reset_mock()
