import gsplot as gs
import numpy as np

# Create data
x = np.linspace(0, 10, 100)
y = np.sin(x)
z = np.cos(x)


axes = gs.axes(store=True, size=[5, 5], mosaic="A")

# Scatter plot
gs.scatter(0, x, y, label="sin(x)", s=5)
# Scatter plot with colormap
gs.scatter_colormap(0, x, z, x, label="cos(x)", s=5)

gs.show("scatter")
