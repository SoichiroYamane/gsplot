import numpy as np

import gsplot as gs

xdata = np.linspace(0, 4 * np.pi, 1000)
ydata = np.sin(xdata)


gs.axes(store=False, mosaic="A")
gs.line_colormap_solid(
    0, xdata, ydata, ydata, label="$\\sin(x)$", interpolation_points=None
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
