import os

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib as mpl  # noqa: E402

mpl.use("Agg", force=True)
import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402

try:
    from gsplot._compat.legacy.config.config import Config as LegacyConfig
    from gsplot._compat.legacy.figure.axes_range_base import (
        AxesRangeSingleton as LegacyAxesRange,
    )
    from gsplot._compat.legacy.figure.store import StoreSingleton as LegacyStore
except ImportError:
    LegacyConfig = None  # type: ignore[assignment]
    LegacyStore = None  # type: ignore[assignment]
    LegacyAxesRange = None  # type: ignore[assignment]


def _reset_legacy_singletons() -> None:
    if LegacyConfig is not None:
        LegacyConfig._instance = None
    if LegacyStore is not None:
        LegacyStore._instance = None
    if LegacyAxesRange is not None:
        LegacyAxesRange._instance = None


@pytest.fixture(autouse=True)
def isolate_matplotlib_state(
    monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory
):
    fake_home = tmp_path_factory.mktemp("fake_home")
    monkeypatch.setenv("HOME", str(fake_home))
    _reset_legacy_singletons()
    original_rc_params = mpl.rcParams.copy()
    was_interactive = plt.isinteractive()
    yield
    mpl.rcParams.clear()
    mpl.rcParams.update(original_rc_params)
    plt.close("all")
    if not was_interactive and plt.isinteractive():
        plt.ioff()
    mpl.use("Agg", force=True)
    _reset_legacy_singletons()
