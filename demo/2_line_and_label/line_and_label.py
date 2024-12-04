import gsplot as gs

axes = gs.axes(store=True, size=[10, 5], mosaic="AB")

for i in range(7):
    x = [i, i + 1, i + 2]
    y = [i, i, i]

    # Plot line by axis index
    gs.line(0, x, y, label=f"line {i}")

    # Plot line by axis
    # Fill the facecolor of the marker by alpha_mfc
    gs.line(axes[1], x, y, label=f"line {i}", alpha_mfc=1)

# Add legends to the all axes
gs.legend_axes()

# Add labels to the all axes
gs.label(
    [
        # ["xlabel", "ylabel", [xlim, *args], [ylim, *args]]
        ["$x_1$", "$y_1$", [-1, 10], [-1, 10]],
        ["$x_2$", "$y_2$", [-1, 10], [-1, 10]],
    ]
)

gs.show("line_and_label")
