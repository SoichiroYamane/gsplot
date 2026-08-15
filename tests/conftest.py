import os

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib as mpl  # noqa: E402

mpl.use("Agg", force=True)
import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def isolate_matplotlib_state(
    monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory
):
    fake_home = tmp_path_factory.mktemp("fake_home")
    monkeypatch.setenv("HOME", str(fake_home))
    original_rc_params = mpl.rcParams.copy()
    was_interactive = plt.isinteractive()
    yield
    mpl.rcParams.clear()
    mpl.rcParams.update(original_rc_params)
    plt.close("all")
    if not was_interactive and plt.isinteractive():
        plt.ioff()
    mpl.use("Agg", force=True)
