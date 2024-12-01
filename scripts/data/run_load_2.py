import matplotlib.pyplot as plt
from rich import print

import gsplot as gs

# Load the data
data = gs.load_file("SC_gap_vs_T_iso.dat", unpack=True, delimiter="	", skip_header=1)
print(data)
# Create list of axes
axes = gs.axes(store=False, mosaic="AB;CD", size=[6, 6])


gs.line(
    axis_target=0,
    x=data[0],
    y=data[1],
    ms=5,
)

axes[1].plot(data[0] * 10, data[1] * 10, "o", ms=5)

gs.line_colormap_dashed(
    axis_target=0,
    x=data[0] * 10,
    y=data[1] * 10,
    cmapdata=data[0],
    line_pattern=(10, 10),
)


gs.label(
    [
        ["$B_x$", "$B_y$"],
        ["$B_x$", "$B_y$"],
        ["$B_x$", "$B_y$"],
        ["$B_x$", "$B_y$"],
    ],
)


gs.label_add_index(position="in", glyph="alphabet", capitalize=True)

gs.show("test")
