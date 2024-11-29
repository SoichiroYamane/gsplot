import gsplot as gs
import numpy as np
import matplotlib.pyplot as plt


xdata = np.linspace(0, 4 * np.pi, 1000)
ydata = np.sin(xdata)
# ydata = xdata * 0


gs.axes(store=False, mosaic="A")

gs.line_colormap_dashed(
    0,
    xdata * 10,
    ydata * 10,
    xdata * 10,
    label="test",
    linewidth=2,
    line_pattern=(10, 10),
)
# plt.plot([0, 30], [0, 0], "k--", lw=2)

gs.label(
    [
        [
            "A",
            "B",
        ],
    ]
)
gs.show()
