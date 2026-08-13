"""Build the concise publication figure used by the documentation."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import gsplot as gs

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
NAMES = ("A1g", "A2u", "B1g", "B1u", "Eg1i", "Eg10", "Eu10", "Eg11", "Eu11")
EVEN = ("A1g", "B1g", "Eg1i", "Eg10", "Eg11")
LABELS = (
    r"$A_{1g}$",
    r"$A_{2u}$",
    r"$B_{1g}$",
    r"$B_{1u}$",
    r"$E_g(1,i)$",
    r"$E_g(1,0)$",
    r"$E_u(1,0)$",
    r"$E_g(1,1)$",
    r"$E_u(1,1)$",
)
AXES = (
    (r"$T/T_c$", r"$\Delta_0(T)/k_BT_c$", (0, 1.2), (0, 3)),
    (r"$T/T_c$", r"$C_s/C_n$", (0, 1.2), (0, 3)),
    (r"$T/T_c$", r"$Y(T)$", (0, 1), (0, 1)),
)


def read(group: str, prefix: str, names: tuple[str, ...]) -> list[np.ndarray]:
    return [
        gs.read(DATA / group / f"{prefix}{name}.dat", skip_header=1, delimiter="\t")
        for name in names
    ]


def main() -> None:
    """Build, save, display, and close the publication figure."""
    gap = read("gap", "Gapeq_", NAMES)
    hs = read("heat_capacity", "C_", NAMES)
    ys = read("yosida", "Y(T)_", EVEN)
    fig, ax = gs.subplots("ABC", size=(8.3, 2.85))
    fig.get_layout_engine().set(wspace=0.08)
    sq = gs.inset(
        ax["B"],
        (0.22, 0.64, 0.36, 0.30),
        label=(r"$(T/T_c)^2$", r"$C_s/C_n$", (0, 0.25), (0, 1)),
    )
    for i, (g, h, name) in enumerate(zip(gap, hs, LABELS)):
        t = np.append(h[0], [1, 1.5])
        cap = np.append(h[1], [1, 1])
        kw = {"series": i, "label": name, "ms": 0, "lw": 2}
        gs.line(ax["A"], *g, **kw)
        gs.line(ax["B"], t, cap, **kw)
        gs.line(sq, t**2, cap, **kw)
    for v, name in zip(ys, EVEN):
        i = NAMES.index(name)
        gs.line(ax["C"], *v, series=i, label=LABELS[i], ms=0, lw=2)
    p = {"fontsize": 7, "columnspacing": 0.4, "handlelength": 1.4}
    gs.legend(ax["A"], loc="lower left", props={**p, "ncols": 2})
    gs.legend(ax["C"], loc="upper left", props=p)
    sq.tick_params(labelsize=7, pad=5)
    plt.setp((sq.xaxis.label, sq.yaxis.label), fontsize=7)
    gs.label(ax, AXES, square=True, index="out")
    try:
        gs.save(fig, ROOT / "SC_cal")
    finally:
        plt.close(fig)


if __name__ == "__main__":
    main()
