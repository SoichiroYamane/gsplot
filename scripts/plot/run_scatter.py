import gsplot as gs
import numpy as np


xdata = np.linspace(0, 4 * np.pi, 100)
ydata = np.sin(xdata)


gs.axes(store=False, mosaic="A")
gs.scatter(0, xdata, ydata, c="green")


gs.scatter(
    0,
    xdata,
    ydata + 1,
)

gs.scatter(
    0,
    xdata,
    ydata + 2,
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
