import gsplot as gs
import matplotlib.pyplot as plt

# Create list of axes
axes = gs.axes(
    store=False,
    mosaic="AB;CD",
)

# plot a line on the first axis: corresponding to A
gs.line(
    idx=0,
    x=[1, 2, 3],
    y=[1, 1, 1],
)


gs.label(
    [
        ["$A_x$", "$A_y$"],
        ["$B_x$", "$B_y$"],
        ["$C_x$", "$C_y$"],
        ["$D_x$", "$D_y$"],
    ]
)
gs.show()
