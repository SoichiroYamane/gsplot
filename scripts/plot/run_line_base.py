import gsplot as gs

gs.axes(store=False, mosaic="A")
gs.plot(
    axis_index=0,
    xdata=[1, 2, 3],
    ydata=[1, 1, 1],
)

gs.plot(
    axis_index=0,
    xdata=[2, 3, 4],
    ydata=[2, 2, 2],
)

gs.plot(
    axis_index=0,
    xdata=[3, 4, 5],
    ydata=[3, 3, 3],
)

gs.plot(
    axis_index=0,
    xdata=[4, 5, 6],
    ydata=[4, 4, 4],
)

gs.plot(
    axis_index=0,
    xdata=[5, 6, 7],
    ydata=[5, 5, 5],
)

gs.plot(
    axis_index=0,
    xdata=[6, 7, 8],
    ydata=[6, 6, 6],
)

gs.plot(
    axis_index=0,
    xdata=[7, 8, 9],
    ydata=[7, 7, 7],
)
