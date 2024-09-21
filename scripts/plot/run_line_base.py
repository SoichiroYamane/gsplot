import gsplot as gs

axes = gs.axes(store=False, mosaic="A")
gs.line(
    0,
    x=[1, 2, 3],
    y=[1, 1, 1],
    label="line 1",
    # markersize=23,
    # ms=17,
)


gs.line(
    0,
    x=[2, 3, 4],
    y=[2, 2, 2],
)

gs.line(
    0,
    x=[3, 4, 5],
    y=[3, 3, 3],
)

gs.line(
    0,
    x=[4, 5, 6],
    y=[4, 4, 4],
)

gs.line(0, x=[5, 6, 7], y=[5, 5, 5])

gs.line(
    0,
    x=[6, 7, 8],
    y=[6, 6, 6],
)

gs.line(
    0,
    x=[7, 8, 9],
    y=[7, 7, 7],
)
