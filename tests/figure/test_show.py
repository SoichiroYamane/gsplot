import pytest
from unittest.mock import patch
from gsplot.figure.show import Show


class TestShow:

    @patch("matplotlib.pyplot.savefig", autospec=True)
    @patch("matplotlib.pyplot.show", autospec=True)
    def test_show_with_store(self, mock_show, mock_savefig):
        # Mock the return values or behaviors of savefig and show if needed
        mock_show.return_value = None
        mock_savefig.return_value = None

        # Creating instance of Show
        show_instance = Show(name="test", ft_list=["png"], dpi=300, show=True)

        # Perform assertions
        mock_show.assert_called_once()  # Assert show() was called once

        # Check if savefig() was called with the correct arguments
        if show_instance._get_store():  # Access the store using _get_store method
            mock_savefig.assert_called_once_with(
                "test.png", bbox_inches="tight", dpi=300
            )
        else:
            mock_savefig.assert_not_called()  # Ensure savefig() wasn't called if store is False

    @patch("matplotlib.pyplot.savefig", autospec=True)
    @patch("matplotlib.pyplot.show", autospec=True)
    def test_show_without_store(self, mock_show, mock_savefig):
        # Mock the return values or behaviors of savefig and show if needed
        mock_show.return_value = None
        mock_savefig.return_value = None

        # Creating instance of Show
        show_instance = Show(name="test", ft_list=["png"], dpi=300, show=False)

        # Perform assertions
        mock_show.assert_not_called()  # Assert show() was not called

        # Check if savefig() was called with the correct arguments
        if show_instance._get_store():  # Access the store using _get_store method
            mock_savefig.assert_called_once_with(
                "test.png", bbox_inches="tight", dpi=300
            )
        else:
            mock_savefig.assert_not_called()  # Ensure savefig() wasn't called if store is False
