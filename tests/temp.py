# import gsplot as gs
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as plticker

import gsplot as gs

axes = gs.axes(mosaic="AB")

x = [1, 2, 3, 4, 5]
y = [1, 4, 9, 16, 25]
x2 = [1, 2, 3, 4, 5]
y2 = [1, 8, 27, 64, 125]

gs.Line(
    0,
    x,
    y,
    label="y = x^2",
).plot()

gs.Line(
    0,
    x2,
    y2,
    label=r"y = $x^3 \int x \lambda \theta_{\rm K}$",
).plot()


gs.style.Labels(
    [
        ["x", "y"],
        ["x", "y"],
    ],
    add_index=True,
)


# test = gs.style.legend.Legend(0).legend()
gs.style.legend_colormap.LegendColormap(
    0, label="test", max=1, min=0
).add_legend_colormap()


gs.figure.Show()
