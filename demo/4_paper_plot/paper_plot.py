"""Build the compact publication-style example used by the documentation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

import gsplot as gs

DEMO_DIR = Path(__file__).resolve().parent
DATA_DIR = DEMO_DIR.parent / "data"
CONFIG_PATH = DEMO_DIR / "gsplot.json"
OUTPUT_PATH = "SC_cal"

SYMMETRIES = ("A1g", "A2u", "B1g", "B1u", "Eg1i", "Eg10", "Eu10", "Eg11", "Eu11")
EVEN_SYMMETRIES = ("A1g", "B1g", "Eg1i", "Eg10", "Eg11")
LINE_STYLES: tuple[Any, ...] = (
    "-",
    "--",
    "-.",
    ":",
    (0, (1, 1, 3, 1)),
    (0, (1, 1, 5, 2)),
    (0, (5, 2, 1, 2)),
    (0, (5, 2, 1, 2, 1, 2)),
    (0, (3, 1, 1, 2)),
)
EVEN_LINE_STYLES: tuple[Any, ...] = (
    "-",
    "-.",
    (0, (1, 1, 3, 1)),
    (0, (1, 1, 5, 2)),
    (0, (5, 2, 1, 2, 1, 2)),
)
LABELS = (
    "$A_{1g}$",
    "$A_{2u}$",
    "$B_{1g}$",
    "$B_{1u}$",
    "$E_{g}(1,i)$",
    "$E_{g}(1,0)$",
    "$E_{u}(1,0)$",
    "$E_{g}(1,1)$",
    "$E_{u}(1,1)$",
)
EVEN_LABELS = (
    "$A_{1g}$",
    "$B_{1g}$",
    "$E_{g}(1,i)$",
    "$E_{g}(1,0)$",
    "$E_{g}(1,1)$",
)

# These are the small, local publication defaults used by the 0.3.x example.
# They are scoped to this Figure and do not change gsplot's library defaults.
PUBLICATION_RCPARAMS = {
    "axes.autolimit_mode": "round_numbers",
    "axes.xmargin": 0,
    "axes.ymargin": 0,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.top": True,
    "ytick.right": True,
    "xtick.major.pad": 6,
    "ytick.major.pad": 6,
    "legend.fancybox": False,
    "legend.framealpha": None,
    "legend.edgecolor": "inherit",
    "legend.frameon": False,
    "legend.labelspacing": 0.3,
    "legend.loc": "lower left",
}


def _read_data(
    root: Path, directory: str, prefix: str, names: tuple[str, ...]
) -> list[np.ndarray]:
    """Read one family of the example's two-column data files."""

    return [
        gs.read_array(
            root / directory / f"{prefix}{name}.dat",
            options={"skip_header": 1, "delimiter": "\t", "unpack": True},
        )
        for name in names
    ]


def _line_props(color: Any, label: str, linestyle: Any) -> dict[str, Any]:
    """Return only the line options that differ from the gsplot defaults."""

    return {
        "color": color,
        "label": label,
        "markersize": 0,
        "linewidth": 2,
        "linestyle": linestyle,
    }


def _axis_spec(
    xlabel: str,
    ylabel: str,
    xlim: tuple[float, float],
    ylim: tuple[float, float],
    *,
    pad: float,
) -> gs.AxisSpec:
    """Build one compact publication axis specification."""

    return gs.AxisSpec(
        xlabel=xlabel,
        ylabel=ylabel,
        xlim=xlim,
        ylim=ylim,
        xminor=True,
        yminor=True,
        xlabelpad=pad,
        ylabelpad=pad,
    )


def build_publication_figure(
    *,
    data_root: Path = DATA_DIR,
    config_path: Path = CONFIG_PATH,
) -> tuple[Figure, dict[str, Axes], dict[str, Axes]]:
    """Build the publication Figure without saving it."""

    config = gs.load_config(config_path)
    gap_data = _read_data(data_root, "gap", "Gapeq_", SYMMETRIES)
    heat_capacity = _read_data(data_root, "c", "C_", SYMMETRIES)
    yosida_data = _read_data(data_root, "yosida", "Y(T)_", EVEN_SYMMETRIES)

    with mpl.rc_context(PUBLICATION_RCPARAMS):
        figure, axes_value = gs.subplots(config=config, mosaic="ABC")
        axes = cast(dict[str, Axes], axes_value)
        inset_heat = gs.inset_axes(
            axes["B"], gs.InsetSpec(bounds=(0.57, 0.12, 0.25, 0.25))
        )
        inset_square = gs.inset_axes(
            axes["B"], gs.InsetSpec(bounds=(0.2, 0.55, 0.35, 0.35))
        )

        colors = gs.sample_cmap(config.plotting.default_cmap, count=len(SYMMETRIES))
        for index, (gap, heat, label, linestyle) in enumerate(
            zip(gap_data, heat_capacity, LABELS, LINE_STYLES)
        ):
            props = _line_props(colors[index], label, linestyle)
            gs.line(axes["A"], gap[0], gap[1], props=props)
            temperature = np.append(heat[0], [1, 1.5])
            capacity = np.append(heat[1], [1, 1])
            for axis, x_values in (
                (axes["B"], temperature),
                (inset_heat, temperature),
                (inset_square, temperature**2),
            ):
                gs.line(axis, x_values, capacity, props=props)

        for index, (data, label, linestyle) in enumerate(
            zip(yosida_data, EVEN_LABELS, EVEN_LINE_STYLES)
        ):
            color = colors[SYMMETRIES.index(EVEN_SYMMETRIES[index])]
            gs.line(
                axes["C"],
                data[0],
                data[1],
                props=_line_props(color, label, linestyle),
            )

        gs.legend(axes["A"], props={"handlelength": 3})
        gs.legend(axes["C"], props={"handlelength": 3, "loc": "lower right"})

        for axis, spec in zip(
            (axes["A"], axes["B"], axes["C"]),
            (
                _axis_spec(
                    "$T/T_{\\rm{c}}$",
                    "$\\Delta_0(T)/k_{\\rm{B}}T_{\\rm{c}}$",
                    (0, 1.2),
                    (0, 3),
                    pad=5,
                ),
                _axis_spec(
                    "$T/T_{\\rm{c}}$",
                    "$C_{\\rm{s}}/C_{\\rm{n}}$",
                    (0, 1.2),
                    (0, 3),
                    pad=5,
                ),
                _axis_spec("$T/T_{\\rm{c}}$", "$Y(T)$", (0, 1), (0, 1), pad=5),
            ),
        ):
            gs.style_axes(axis, spec)
        for axis, spec in zip(
            (inset_heat, inset_square),
            (
                _axis_spec(
                    "$T/T_{\\rm{c}}$",
                    "$C_{\\rm}/C_{\\rm{n}}$",
                    (0.9, 1.01),
                    (1.5, 1.8),
                    pad=0,
                ),
                _axis_spec(
                    "($T/T_{\\rm{c}})^2$",
                    "$C_{\\rm}/C_{\\rm{n}}$",
                    (0, 0.25),
                    (0, 1),
                    pad=0,
                ),
            ),
        ):
            gs.style_axes(axis, spec)

        gs.box_aspect(axes, 1)
        axes["B"].indicate_inset_zoom(inset_heat, edgecolor="black", alpha=0.3)
        engine = figure.get_layout_engine()
        if engine is not None and hasattr(engine, "set"):
            engine.set(w_pad=2, h_pad=2)
        gs.panel_labels(
            axes,
            labels=("($\\,$a$\\,$)", "($\\,$b$\\,$)", "($\\,$c$\\,$)"),
            loc="in",
            props={"fontsize": "large", "ha": "center", "va": "center"},
        )
        return figure, axes, {"heat": inset_heat, "square": inset_square}


def save_publication_figure(
    figure: Figure,
    path: str | Path = OUTPUT_PATH,
) -> tuple[Path, ...]:
    """Save and display the same Figure as a 600-DPI PNG and PDF."""

    with mpl.rc_context({"pdf.fonttype": 42, "ps.fonttype": 42}):
        return gs.savefig(
            figure,
            path,
            formats=("png", "pdf"),
            dpi=600,
            props={"bbox_inches": "tight"},
            show=True,
            overwrite=True,
        )


def main() -> None:
    """Build, save, display, and close the documentation Figure."""

    figure, _, _ = build_publication_figure()
    try:
        save_publication_figure(figure)
    finally:
        plt.close(figure)


if __name__ == "__main__":
    main()
