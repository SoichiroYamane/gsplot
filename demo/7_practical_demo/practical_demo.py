import numpy as np
from rich import print

import gsplot as gs

# Load the configuration file
config = gs.config_load("./gsplot.json")


# Load the data files
symmmetries = ["A1g", "A2u", "B1g", "B1u", "Eg1i", "Eg10", "Eu10", "Eg11", "Eu11"]
even_symmetries = [
    "A1g",
    "B1g",
    "Eg1i",
    "Eg10",
    "Eg11",
]

gap_data_list = [gs.load_file(f"../data/gap/Gapeq_{s}.dat") for s in symmmetries]
c_data_list = [gs.load_file(f"../data/c/C_{s}.dat") for s in symmmetries]
yosida_data_list = [
    gs.load_file(f"../data/yosida/Y(T)_{s}.dat") for s in even_symmetries
]


# Create axes
axes = gs.axes(store=True)

# Plot the data
cm = gs.get_cmap(N=9)
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
labels_even = ["$A_{1g}$", "$B_{1g}$", "$E_{g}(1,i)$", "$E_{g}(1,0)$", "$E_{g}(1,1)$"]
for i, (data, label) in enumerate(zip(gap_data_list, labels)):
    gs.line(0, data[0], data[1], color=cm[i], label=label, ms=0, lw=2, ls="-")
    gs.line(
        1,
        # add trivial points to the data from normal states
        np.append(c_data_list[i][0], [1, 1.5]),
        np.append(c_data_list[i][1], [1, 1]),
        color=cm[i],
        label=label,
        ms=0,
        lw=2,
        ls="-",
    )

for i, (data, label) in enumerate(zip(yosida_data_list, labels_even)):
    idx = symmmetries.index(even_symmetries[i])
    gs.line(2, data[0], data[1], color=cm[idx], label=label, ms=0, lw=2, ls="-")

# Add Legend
gs.legend(0)
gs.legend(2, loc="lower right")

# Set square aspect ratio
gs.graph_square_axes()

# Add labels
gs.label(
    [
        ["$T/T_{\\rm{c}}$", "$\\Delta_0(T)/k_{\\rm{B}}T_{\\rm{c}}$", [0, 1.2], [0, 3]],
        ["$T/T_{\\rm{c}}$", "$C_{\\rm{s}}/C_{\\rm{n}}$", [0, 1.2], [0, 3]],
        ["$T/T_{\\rm{c}}$", "$Y(T)$", [0, 1], [0, 1]],
    ]
)

# Add index
gs.label_add_index(loc="in")

gs.show("SC_cal")
