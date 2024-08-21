import gsplot as gs

gs.axes(store=False, mosaic="A")
gs.line_colormap(
    0,
    [0, 1, 2, 3, 4],
    [0, 1, 2, 3, 4],
    [0, 1, 2, 3, 4],
    ls="--",
    lw=20,
    label="A",
    fontsize=12,
    num_points=4,
)
gs.label(
    [
        [
            "A",
            "B",
        ],
    ]
)
gs.show()
