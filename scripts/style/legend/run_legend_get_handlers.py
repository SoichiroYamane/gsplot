import gsplot as gs
from matplotlib import pyplot as plt

axes = gs.axes(store=False, mosaic="AB")

gs.plot(axis_index=0, xdata=[0, 100], ydata=[0, 100], label="a")

gs.plot(axis_index=0, xdata=[0, 50], ydata=[0, 10], label="b")


gs.label(
    [
        ["a", "b", [0, 100, 5], [0, 100]],
        ["c", "f", [0, 100, 5], [0, 10]],
    ],
    minor_ticks_all=False,
    add_index=True,
)


gs.legend(
    axis_index=0,
    loc="lower right",
)

test = gs.legend_get_handlers(axis_index=0)
