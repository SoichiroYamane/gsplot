import numpy as np

import gsplot as gs

axs = gs.axes(store=True, size=[10, 5], mosaic="AB")

x = np.linspace(0, 10, 100)
y = np.sin(x)
for i in range(5):
    # Scatter plot
    gs.scatter(axs[0], x, y + i, label=f"{i}th", s=5)

s = np.linspace(0, 10, 100)
t = np.cos(s)
# Scatter plot with colormap
gs.scatter_colormap(axs[1], s, t, s, label="cos(x)", s=5)

# Add legends to the all axes
gs.legend_axes()

gs.show("scatter")
