import matplotlib.pyplot as plt
import numpy as np

import gsplot as gs

x = np.linspace(0, 10, 100)
y = np.sin(x)

# Create subplots
fig, axs = plt.subplots(2, 2, figsize=(10, 10))

axs[0, 0].plot(x, y)

# gsplot can be used to plot on the subplots
gs.line(axs[0, 1], x, y)
gs.line_colormap_solid(axs[1, 0], x, y, x)
gs.line_colormap_dashed(axs[1, 0], x, y + 1, x)
gs.scatter(axs[1, 1], x, y)
gs.scatter_colormap(axs[1, 1], x, y + 1, x)


gs.label([["x", "y"], ["x", "y"], ["x", "y"], ["x", "y"]])

# Needs to save the figure
plt.savefig("subplots.png")
plt.show()
