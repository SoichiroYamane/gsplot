import numpy as np

import gsplot as gs

# Load the configuration file
config = gs.config_load("./gsplot.json")

# Load the data files
symmetries = ["A1g", "A2u", "B1g", "B1u", "Eg1i", "Eg10", "Eu10", "Eg11", "Eu11"]
even_symmetries = ["A1g", "B1g", "Eg1i", "Eg10", "Eg11"]
ls_list = [
    "-",
    "--",
    "-.",
    ":",
    (0, (1, 1, 3, 1)),
    (0, (1, 1, 5, 2)),
    (0, (5, 2, 1, 2)),
    (0, (5, 2, 1, 2, 1, 2)),
    (0, (3, 1, 1, 2)),
]
ls_even = ["-", "-.", (0, (1, 1, 3, 1)), (0, (1, 1, 5, 2)), (0, (5, 2, 1, 2, 1, 2))]

gap_data_list = [gs.load_file(f"../data/gap/Gapeq_{s}.dat") for s in symmetries]
c_data_list = [gs.load_file(f"../data/c/C_{s}.dat") for s in symmetries]
yosida_data_list = [
    gs.load_file(f"../data/yosida/Y(T)_{s}.dat") for s in even_symmetries
]


# Create axes
axs = gs.axes(store=True)
axins1 = gs.axes_inset(
    axs[1],
    bounds=(0.57, 0.12, 0.25, 0.25),
    lab_lims=["$T/T_{\\rm{c}}$", "$C_{\\rm}/C_{\\rm{n}}$", [0.9, 1.01], [1.5, 1.8]],
    zoom=((3, 2), (4, 1)),
    xpad_label=0,
    ypad_label=0,
)

axins2 = gs.axes_inset(
    axs[1],
    bounds=(0.2, 0.55, 0.35, 0.35),
    lab_lims=["($T/T_{\\rm{c}})^2$", "$C_{\\rm}/C_{\\rm{n}}$", [0, 0.25], [0, 1.0]],
    zoom=False,
    xpad_label=0,
    ypad_label=0,
)

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
for i, (data, label, ls) in enumerate(zip(gap_data_list, labels, ls_list)):
    gs.line(axs[0], data[0], data[1], color=cm[i], label=label, ms=0, lw=2, ls=ls)

    # add trivial points to the data from normal states
    tc = np.append(c_data_list[i][0], [1, 1.5])
    c = np.append(c_data_list[i][1], [1, 1])
    gs.line(axs[1], tc, c, color=cm[i], label=label, ms=0, lw=2, ls=ls)
    gs.line(axins1, tc, c, color=cm[i], label=label, ms=0, lw=2, ls=ls)
    gs.line(axins2, tc**2, c, color=cm[i], label=label, ms=0, lw=2, ls=ls)

for i, (data, label, ls) in enumerate(zip(yosida_data_list, labels_even, ls_even)):
    idx = symmetries.index(even_symmetries[i])
    gs.line(axs[2], data[0], data[1], color=cm[idx], label=label, ms=0, lw=2, ls=ls)

# Add Legend
gs.legend(axs[0], handlelength=3)
gs.legend(axs[2], handlelength=3, loc="lower right")

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
