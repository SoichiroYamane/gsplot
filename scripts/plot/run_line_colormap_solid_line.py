import gsplot as gs

gs.axes(store=False, mosaic="A")
gs.line_colormap_solid(
    0,
    [0, 1, 2, 3, 4],
    [0, 1, 2, 3, 4],
    [0, 1, 2, 3, 4],
    lw=20,
    label="A",
    fontsize=30,
    interpolation_points=100,
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
