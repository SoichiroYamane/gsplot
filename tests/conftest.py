import os

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib as mpl  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def isolate_matplotlib_state():
    original_rc_params = mpl.rcParams.copy()
    yield
    mpl.rcParams.update(original_rc_params)
    plt.close("all")
