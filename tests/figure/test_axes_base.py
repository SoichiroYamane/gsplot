from unittest.mock import MagicMock

import pytest
from matplotlib.axes import Axes
from numpy import ndarray

from gsplot.figure.axes_base import AxesRangeSingleton, AxesSingleton


class TestAxesSingleton:

    def setup_method(self):
        # Mocking Axes class
        self.mock_axes1 = MagicMock(spec=Axes)
        self.mock_axes2 = MagicMock(spec=Axes)

        # Creating first instance of AxesSingleton
        self.singleton1 = AxesSingleton()
        self.singleton1.axes = [self.mock_axes1, self.mock_axes2]

        # Creating second instance of AxesSingleton
        self.singleton2 = AxesSingleton()

    def test_singleton(self):
        # Asserting that both instances are the same
        assert self.singleton1 is self.singleton2

        # Asserting that changes in one instance are reflected in the other
        assert self.singleton1.axes == self.singleton2.axes

    def test_get_axis(self):
        # Asserting that get_axis method works as expected
        assert self.singleton1.get_axis(0) is self.mock_axes1
        assert self.singleton1.get_axis(1) is self.mock_axes2

        # Asserting that get_axis raises an IndexError when the index is out of range
        with pytest.raises(IndexError):
            self.singleton1.get_axis(2)


class TestAxesRangeSingleton:
    def setup_method(self):
        # Mocking Axes class
        self.mock_axes1 = MagicMock(spec=Axes)
        self.mock_axes2 = MagicMock(spec=Axes)

        # Mocking ndarray
        self.mock_ndarray1 = MagicMock(spec=ndarray)
        self.mock_ndarray2 = MagicMock(spec=ndarray)

        # Creating first instance of AxesRangeSingleton
        self.singleton1 = AxesRangeSingleton()
        self.singleton1.axes_ranges = [[self.mock_ndarray1, self.mock_ndarray2]]

        # Creating second instance of AxesRangeSingleton
        self.singleton2 = AxesRangeSingleton()

    def test_singleton(self):
        # Asserting that both instances are the same
        assert self.singleton1 is self.singleton2

        # Asserting that changes in one instance are reflected in the other
        assert self.singleton1.axes_ranges == self.singleton2.axes_ranges

    def test_add_range(self):
        # Mocking ndarray
        mock_ndarray3 = MagicMock(spec=ndarray)
        mock_ndarray4 = MagicMock(spec=ndarray)

        # Adding new range
        self.singleton1.add_range(1, mock_ndarray3, mock_ndarray4)

        # Asserting that new range was added
        assert self.singleton1.axes_ranges[1] == [mock_ndarray3, mock_ndarray4]

    def test_reset(self):
        # Resetting axes ranges
        self.singleton1.reset([self.mock_axes1, self.mock_axes2])

        # Asserting that axes ranges were reset
        assert self.singleton1.axes_ranges == [[None, None], [None, None]]
