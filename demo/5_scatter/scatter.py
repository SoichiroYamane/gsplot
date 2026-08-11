import numpy as np

import gsplot as gs

fig, axes = gs.subplots(figsize=(10, 5), mosaic="AB")

x = np.linspace(0, 10, 100)
y = np.sin(x)
for i in range(5):
    gs.scatter(axes["A"], x, y + i, props={"label": f"{i}th", "s": 5})

s = np.linspace(0, 10, 100)
t = np.cos(s)
gs.cmap_scatter(axes["B"], s, t, s, props={"label": "cos(x)", "s": 5})

gs.legends(fig)
gs.style_axes(axes, gs.AxisSpec(xlabel="x", ylabel="value"))
gs.savefig(fig, "scatter", show=False, overwrite=True)
