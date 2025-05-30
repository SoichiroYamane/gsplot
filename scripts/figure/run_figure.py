import matplotlib.pyplot as plt
from rich import print

import gsplot as gs

test = gs.config_load()
print(test)

# Create list of axes
axes = gs.axes(store=False, mosaic="AB;CD", size=[6, 6])


# plot a line on the first axis: corresponding to A
gs.line(
    axis_target=0,
    x=[1, 2, 3],
    y=[1, 1, 1],
)

gs.line(
    axis_target=2,
    x=[1, 2, 10],
    y=[1, 1, 10],
)

gs.label(
    [
        ["$A_x$", "$A_y$"],
        ["$B_x$", "$B_y$"],
        ["$C_x$", "$C_y$"],
        ["$D_x$", "$D_y$"],
    ],
)


gs.label_add_index(position="in", glyph="alphabet", capitalize=True)

gs.show("test")
