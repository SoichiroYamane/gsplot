import gsplot as gs
import numpy as np


xdata = np.linspace(0, 4 * np.pi, 10)
ydata = np.sin(xdata)


gs.axes(store=False, mosaic="A")
gs.line_colormap(0, xdata, ydata, ydata, linewidth=10, ls="dashed")
gs.label(
    [
        [
            "A",
            "B",
        ],
    ]
)
gs.show()
