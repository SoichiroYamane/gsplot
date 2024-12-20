import matplotlib.pyplot as plt

import gsplot as gs

x = [1, 2, 3, 4, 5]
y = [1, 4, 9, 16, 25]

axes = gs.axes(store=True, size=[5, 5], unit="in", mosaic="AB;CD")
gs.line(axis_target=0, x=x, y=y, label="Line 1")
gs.line(axis_target=axes[1], x=x, y=y)

# gsplot is compatible with matplotlib
# Plot data by matplotlib plot
axes[2].plot(x, y)

plt.sca(axes[3])
plt.plot(x, y)

gs.legend(0, loc="lower right")
gs.label(
    [
        # add label without specifying limits
        ["$x_1$", "$y_1$"],
        # add label with limits
        ["$x_2$", "$y_2$", [0, 10], [0, 30]],
        # add label with specifying the minor ticks
        ["$x_3$", "$y_3$", [0, 10, 5], [0, 30, 5]],
        # add label with limits and scale
        ["$x_4$", "$y_4$", [1, 100, "log"], [0, 30]],
    ],
    minor_ticks_all=False,
)
gs.label_add_index(loc="in")
gs.show("compatibility")
