"""Publication prototype for the native Figure-and-Axes tuple design."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import gsplot as gs

ROOT = Path(__file__).parent
DATA = ROOT.parent / "data"
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
    """Read one family of two-column data files."""
    return [
        gs.read(
            DATA / group / f"{prefix}{name}.dat",
            skip_header=1,
            delimiter="\t",
            unpack=True,
        )
        for name in names
    ]


def main() -> None:
    """Build, save, display, and close the publication figure."""
    gap = read("gap", "Gapeq_", NAMES)
    heat_data = read("c", "C_", NAMES)
    yosida = read("yosida", "Y(T)_", EVEN)
    fig, ax = gs.subplots("ABC")
    heat = gs.inset(
        ax["B"],
        (0.57, 0.12, 0.25, 0.25),
        label=(r"$T/T_c$", r"$C_s/C_n$", (0.9, 1.01), (1.5, 1.8)),
        zoom=True,
    )
    square = gs.inset(
        ax["B"],
        (0.2, 0.55, 0.35, 0.35),
        label=(r"$(T/T_c)^2$", r"$C_s/C_n$", (0, 0.25), (0, 1)),
        zoom=False,
    )
    for i, (gap_values, heat_values, name) in enumerate(zip(gap, heat_data, LABELS)):
        temperature = np.append(heat_values[0], [1, 1.5])
        capacity = np.append(heat_values[1], [1, 1])
        kw = {"series": i, "label": name, "ms": 0, "lw": 2}
        gs.line(ax["A"], *gap_values, **kw)
        gs.line((ax["B"], heat), temperature, capacity, **kw)
        gs.line(square, temperature**2, capacity, **kw)
    for values, name in zip(yosida, EVEN):
        i = NAMES.index(name)
        gs.line(ax["C"], *values, series=i, label=LABELS[i], ms=0, lw=2)
    gs.legend(ax["A"], handlelength=3)
    gs.legend(ax["C"], loc="lower right", handlelength=3)
    gs.label(ax, AXES, square=True, index="in")
    gs.save(fig, ROOT / "SC_cal")
    plt.close(fig)


if __name__ == "__main__":
    main()
