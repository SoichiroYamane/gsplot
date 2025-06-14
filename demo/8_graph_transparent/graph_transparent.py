import gsplot as gs

# Set the facecolor of axes to transparent
gs.graph_transparent_axes()

axs = gs.axes(store=True, size=(10, 5), mosaic="AB")

x = [1, 2, 3, 4, 5]
y = [1, 4, 9, 16, 25]

gs.line(axs[0], x, y, color="red")
gs.line_colormap_solid(axs[1], x, y, x, lw=2, interpolation_points=100)

gs.label([["x", "y"], ["x", "y"]])

gs.show("graph_transparent")
