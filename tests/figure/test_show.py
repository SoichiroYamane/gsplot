from unittest.mock import patch

import pytest

from gsplot.figure.show import Show
from gsplot.figure.store import StoreSingleton


class TestShow:
    @pytest.fixture(autouse=True)
    def reset_store(self):
        store = StoreSingleton()
        original = store.store
        store.store = False
        yield
        store.store = original

    @patch("matplotlib.pyplot.savefig", autospec=True)
    @patch("matplotlib.pyplot.show", autospec=True)
    def test_store_and_show_respect_their_flags(self, mock_show, mock_savefig):
        store = StoreSingleton()
        store.store = True
        show_instance = Show(name="test", ft_list=["png"], dpi=300, show=True)

        show_instance.store_fig()
        show_instance.show_fig()

        mock_show.assert_called_once_with()
        mock_savefig.assert_called_once_with("test.png", bbox_inches="tight", dpi=300)

    @patch("matplotlib.pyplot.savefig", autospec=True)
    @patch("matplotlib.pyplot.show", autospec=True)
    def test_disabled_store_and_show_do_nothing(self, mock_show, mock_savefig):
        show_instance = Show(name="test", ft_list=["png"], dpi=300, show=False)

        show_instance.store_fig()
        show_instance.show_fig()

        mock_show.assert_not_called()
        mock_savefig.assert_not_called()
