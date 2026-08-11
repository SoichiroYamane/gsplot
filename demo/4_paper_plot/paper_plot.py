import numpy as np

import gsplot as gs

config = gs.load_config("./gsplot.json")

symmetries = ["A1g", "A2u", "B1g", "B1u", "Eg1i", "Eg10", "Eu10", "Eg11", "Eu11"]
even_symmetries = ["A1g", "B1g", "Eg1i", "Eg10", "Eg11"]
line_styles = ["-", "--", "-.", ":", "-", "--", "-.", ":", "-"]
even_styles = ["-", "-.", "--", ":", "-"]


def load_data(directory: str, prefix: str, names: list[str]) -> list[np.ndarray]:
    """Load the tab-separated two-column data used by this example."""

    return [
        gs.read_array(
            f"../data/{directory}/{prefix}{name}.dat",
            options={"skip_header": 1, "delimiter": "\t", "unpack": True},
        )
        for name in names
    ]


gap_data = load_data("gap", "Gapeq_", symmetries)
heat_capacity = load_data("c", "C_", symmetries)
yosida_data = load_data("yosida", "Y(T)_", even_symmetries)

fig, axes = gs.subplots(config=config, mosaic="ABC")
inset_heat = gs.inset_axes(axes["B"], gs.InsetSpec(bounds=(0.57, 0.12, 0.25, 0.25)))
inset_square = gs.inset_axes(axes["B"], gs.InsetSpec(bounds=(0.2, 0.55, 0.35, 0.35)))

colors = gs.sample_cmap("viridis", count=len(symmetries))
labels = [
    "$A_{1g}$",
    "$A_{2u}$",
    "$B_{1g}$",
    "$B_{1u}$",
    "$E_{g}(1,i)$",
    "$E_{g}(1,0)$",
    "$E_{u}(1,0)$",
    "$E_{g}(1,1)$",
    "$E_{u}(1,1)$",
]
even_labels = ["$A_{1g}$", "$B_{1g}$", "$E_{g}(1,i)$", "$E_{g}(1,0)$", "$E_{g}(1,1)$"]

for index, (gap, heat, label, linestyle) in enumerate(
    zip(gap_data, heat_capacity, labels, line_styles)
):
    props = {
        "color": colors[index],
        "label": label,
        "linewidth": 2,
        "linestyle": linestyle,
    }
    gs.line(axes["A"], gap[0], gap[1], props=props)
    temperature = np.append(heat[0], [1, 1.5])
    capacity = np.append(heat[1], [1, 1])
    gs.line(axes["B"], temperature, capacity, props=props)
    gs.line(inset_heat, temperature, capacity, props=props)
    gs.line(inset_square, temperature**2, capacity, props=props)

for index, (data, label, linestyle) in enumerate(
    zip(yosida_data, even_labels, even_styles)
):
    color_index = symmetries.index(even_symmetries[index])
    gs.line(
        axes["C"],
        data[0],
        data[1],
        props={
            "color": colors[color_index],
            "label": label,
            "linewidth": 2,
            "linestyle": linestyle,
        },
    )

gs.legend(axes["A"], props={"handlelength": 3})
gs.legend(axes["C"], props={"handlelength": 3, "loc": "lower right"})
gs.style_axes(
    axes["A"],
    gs.AxisSpec(
        xlabel="$T/T_{\\rm{c}}$",
        ylabel="$\\Delta_0(T)/k_{\\rm{B}}T_{\\rm{c}}$",
        xlim=(0, 1.2),
        ylim=(0, 3),
    ),
)
gs.style_axes(
    axes["B"],
    gs.AxisSpec(
        xlabel="$T/T_{\\rm{c}}$",
        ylabel="$C_{\\rm{s}}/C_{\\rm{n}}$",
        xlim=(0, 1.2),
        ylim=(0, 3),
    ),
)
gs.style_axes(
    axes["C"],
    gs.AxisSpec(xlabel="$T/T_{\\rm{c}}$", ylabel="$Y(T)$", xlim=(0, 1), ylim=(0, 1)),
)
gs.style_axes(inset_heat, gs.AxisSpec(xlim=(0.9, 1.01), ylim=(1.5, 1.8)))
gs.style_axes(inset_square, gs.AxisSpec(xlim=(0, 0.25), ylim=(0, 1)))
gs.box_aspect((axes["A"], axes["B"], axes["C"]), 1)
gs.panel_labels(axes)
gs.savefig(fig, "SC_cal", show=False, overwrite=True)
