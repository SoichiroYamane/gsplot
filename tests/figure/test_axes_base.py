import numpy as np
import pytest
from matplotlib.axes import Axes

from gsplot.figure.axes_range_base import AxesRangeSingleton, AxisRangeController


def test_axes_range_singleton_stores_ranges_per_axes() -> None:
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(1, 2)
    ranges = AxesRangeSingleton()
    ranges.reset()

    assert AxesRangeSingleton() is ranges
    assert ranges.get_axes_range(ax1) == [None, None]

    x_range = np.array([0.0, 2.0])
    y_range = np.array([-1.0, 3.0])
    ranges.add_range(ax1, x_range, y_range)

    stored_x, stored_y = ranges.get_axes_range(ax1)
    np.testing.assert_array_equal(stored_x, x_range)
    np.testing.assert_array_equal(stored_y, y_range)
    assert ranges.get_axes_range(ax2) == [None, None]

    ranges.reset()
    assert ranges.axes_ranges_dict == {}
    plt.close(fig)


def test_axes_range_singleton_calculates_finite_extrema() -> None:
    ranges = AxesRangeSingleton()
    np.testing.assert_equal(
        ranges.get_max_wo_inf(np.array([1.0, np.inf, 3.0])),
        3.0,
    )
    np.testing.assert_equal(
        ranges.get_min_wo_inf(np.array([-np.inf, 1.0, 3.0])),
        1.0,
    )
    np.testing.assert_array_equal(
        ranges._get_wider_range(np.array([0.0, 2.0]), np.array([-1.0, 3.0])),
        np.array([-1.0, 3.0]),
    )


def test_axis_range_controller_wraps_matplotlib_axes() -> None:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    controller = AxisRangeController(ax)

    controller.set_axis_xrange(np.array([-2.0, 4.0]))
    controller.set_axis_yrange(np.array([1.0, 5.0]))

    np.testing.assert_array_equal(controller.get_axis_xrange(), [-2.0, 4.0])
    np.testing.assert_array_equal(controller.get_axis_yrange(), [1.0, 5.0])
    assert isinstance(ax, Axes)
    plt.close(fig)
