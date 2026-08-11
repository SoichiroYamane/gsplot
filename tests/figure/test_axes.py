from unittest.mock import patch

import numpy as np
import pytest

from gsplot.figure.axes import AxesHandler, Unit, UnitConv


def test_unit_conversion() -> None:
    converter = UnitConv()

    assert converter.convert(1, Unit.MM) == pytest.approx(1 / 25.4)
    assert converter.convert(1, Unit.CM) == pytest.approx(1 / 2.54)
    assert converter.convert(1, Unit.IN) == pytest.approx(1)
    assert converter.convert(1, Unit.PT) == pytest.approx(1 / 72)

    with pytest.raises(ValueError, match="Invalid unit"):
        converter.convert(1, Unit.INVALID)


def test_axes_handler_creates_a_mosaic_and_applies_size() -> None:
    import matplotlib.pyplot as plt

    with patch.object(plt, "ion") as ion:
        handler = AxesHandler(size=(10, 8), unit="cm", mosaic="AB", ion=True)
        handler.create_figure()

        assert len(handler.get_axes) == 2
        np.testing.assert_allclose(plt.gcf().get_size_inches(), [10 / 2.54, 8 / 2.54])
        ion.assert_called_once()


def test_axes_handler_rejects_invalid_size_and_mosaic() -> None:
    invalid_size = AxesHandler(size=(5,), mosaic="A")
    with pytest.raises(ValueError, match="Size must contain exactly two elements"):
        invalid_size.create_figure()

    invalid_mosaic = AxesHandler(mosaic="")
    with pytest.raises(ValueError, match="Mosaic must be specified"):
        invalid_mosaic.create_figure()
