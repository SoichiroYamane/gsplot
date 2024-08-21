import gsplot as gs

# Create list of axes
axes = gs.axes(
    store=True,
    size=[5, 5],
    mosaic="AB;CD",
    clear= False,
    ion=True,
)

# plot a line on the first axis: corresponding to A
gs.line(
    axis_index=0,
    xdata=[1, 2, 3],
    ydata=[1, 1, 1],
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
