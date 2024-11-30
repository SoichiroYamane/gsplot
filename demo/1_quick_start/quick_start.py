import gsplot as gs
import matplotlib.pyplot as plt

# Create new axes
axes = gs.axes(store=True, size=[5, 5], unit="in", mosaic="AB;CD")

x = [1, 2, 3, 4, 5]
y = [1, 4, 9, 16, 25]

# Plot data by index
gs.line(axis_target=0, x=x, y=y, label="Line 1")

# Plot data by axis
gs.line(axis_target=axes[1], x=x, y=y)

# Plot data by matplotlib plot
axes[2].plot(x, y)

plt.sca(axes[3])
plt.plot(x, y)

# Add legend
gs.legend(0, loc="lower right")

# Label axes
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

# Add index
gs.label_add_index(loc="in")

gs.show("quick_start")
