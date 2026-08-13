"""Target-local publication styling for explicit Matplotlib Axes."""

from __future__ import annotations

from matplotlib.axes import Axes
from matplotlib.ticker import AutoLocator
from matplotlib.transforms import nonsingular

from .._core.errors import PlotError
from .._core.targets import normalize_axes
from .._core.types import AxesTarget
from .._core.validation import ensure_bool

PAPER_CYCLE_RGBA = (
    (0.267004, 0.004874, 0.329415, 1.0),
    (0.229739, 0.322361, 0.545706, 1.0),
    (0.127568, 0.566949, 0.550556, 1.0),
    (0.369214, 0.788888, 0.382914, 1.0),
    (0.993248, 0.906157, 0.143936, 1.0),
)


class _RoundNumberAutoLocator(AutoLocator):
    """Keep default automatic ticks with object-local round-number limits."""

    def view_limits(self, dmin: float, dmax: float) -> tuple[float, float]:
        """Return stable round limits without consulting global ``rcParams``."""

        dmin, dmax = nonsingular(dmin, dmax, expander=1e-12, tiny=1e-13)
        ticks = self.tick_values(dmin, dmax)
        return float(ticks[0]), float(ticks[-1])


def _set_typography(axis: Axes) -> None:
    """Apply the frozen 10-point DejaVu Sans baseline to one Axes."""

    text_objects = (
        axis.title,
        axis.xaxis.label,
        axis.yaxis.label,
        axis.xaxis.get_offset_text(),
        axis.yaxis.get_offset_text(),
    )
    for text in text_objects:
        text.set_fontfamily("DejaVu Sans")
        text.set_fontsize(10)


def _style_axis(axis: Axes, *, cycle: bool) -> None:
    """Apply one already-validated paper plan."""

    axis.set_facecolor("white")
    axis.grid(False, which="both", axis="both")
    axis.margins(x=0, y=0, tight=False)
    axis.xaxis.labelpad = 6
    axis.yaxis.labelpad = 6

    for spine in axis.spines.values():
        spine.set_visible(True)
        spine.set_color("black")
        spine.set_linewidth(0.8)

    axis.minorticks_on()
    axis.tick_params(
        axis="both",
        which="major",
        direction="in",
        bottom=True,
        top=True,
        left=True,
        right=True,
        length=3.5,
        width=0.8,
        pad=6,
        labelsize=10,
        labelfontfamily="DejaVu Sans",
    )
    axis.tick_params(
        axis="both",
        which="minor",
        direction="in",
        bottom=True,
        top=True,
        left=True,
        right=True,
        length=2,
        width=0.6,
        labelsize=10,
        labelfontfamily="DejaVu Sans",
    )
    _set_typography(axis)

    if axis.get_xscale() == "linear" and isinstance(
        axis.xaxis.get_major_locator(), AutoLocator
    ):
        axis.xaxis.set_major_locator(_RoundNumberAutoLocator())
    if axis.get_yscale() == "linear" and isinstance(
        axis.yaxis.get_major_locator(), AutoLocator
    ):
        axis.yaxis.set_major_locator(_RoundNumberAutoLocator())
    if cycle:
        axis.set_prop_cycle(color=PAPER_CYCLE_RGBA)


def paper(target: AxesTarget, *, cycle: bool = True) -> None:
    """Apply the frozen publication baseline to explicit Axes only.

    Parameters
    ----------
    target
        One Axes or a finite ordered Axes sequence, array, or mapping.
    cycle
        Install the five-color paper property cycle. Populated Axes require
        ``False`` so an existing cycle is never restarted unpredictably.

    Returns
    -------
    None
        The supplied Axes are styled in place.

    Raises
    ------
    PlotError
        If the target is invalid, ``cycle`` is not boolean, or cycle
        installation is requested for a populated Axes.

    Notes
    -----
    Styling is target-local and does not change global ``rcParams``. Artists
    created directly through Matplotlib after this call retain Matplotlib's
    creation-time defaults where no Axes-local retrofit exists.

    Examples
    --------
    >>> import gsplot as gs
    >>> figure, ax = gs.subplots(style=None)
    >>> gs.paper(ax)
    >>> ax.get_facecolor()[:3]
    (1.0, 1.0, 1.0)
    >>> figure.clear()
    """

    plan = normalize_axes(target, operation="paper")
    selected_cycle = ensure_bool(cycle, "cycle", error=PlotError)
    if selected_cycle and any(axis.lines or axis.collections for axis in plan.axes):
        raise PlotError(
            "paper: cycle=True requires Axes without existing lines or collections; "
            "use cycle=False to preserve the active cycle"
        )
    for axis in plan.axes:
        _style_axis(axis, cycle=selected_cycle)


__all__ = ["paper"]
