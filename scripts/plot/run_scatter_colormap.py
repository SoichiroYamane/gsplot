import gsplot as gs
import numpy as np


xdata = np.linspace(0, 4 * np.pi, 1000)
ydata = np.sin(xdata)


gs.axes(store=False, mosaic="A")
gs.scatter_colormap(0, xdata, ydata, ydata, s=10, cmap="gnuplot", label="sin(x)")
gs.label(
    [
        [
            "A",
            "B",
        ],
    ]
)
gs.show()
