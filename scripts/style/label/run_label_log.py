import gsplot as gs

gs.axes(store=False, mosaic="AB")
gs.label(
    [
        ["a", "b", [1, 100, 5], [0, 10]],
        ["c", "f", [1, 100, 5], [0, 10]],
    ],
    minor_ticks_all=False,
    add_index=True,
)
