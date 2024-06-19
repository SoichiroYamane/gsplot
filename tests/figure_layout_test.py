# import gsplot as gs
import gsplot as gs
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.ticker as plticker
import numpy as np


axes = gs.axes(mosaic="AB")
print(plt.gcf())
print(plt.gca())

x = [0, 1]
y = [0, 1]
x2 = [1, 2, 3, 4, 5]
y2 = [1, 8, 27, 64, 125]


xdata = np.linspace(0, 10, 100)
ydata = np.sin(xdata) * 0.01


gs.plot.line_colormap.LineColormap(
    0, xdata, ydata, xdata, linestyle="--", cmap="inferno", label="test2"
).plot_line_colormap()
gs.plot.line_colormap.LineColormap(1, xdata, ydata, xdata).plot_line_colormap()


# gs.Line(0, [0, 0.1], [0, 0.1], label="y = x^2").plot()

# axes[0].plot([-100, 0], [0, 1000])
# xtest = axes[0].get_xlim()
# ytest = axes[0].get_ylim()


# gs.Line(
#     1,
#     x2,
#     y2,
#     label=r"y = $x^3 \int x \lambda \theta_{\rm K}$",
# ).plot()
# axes[0].plot(x2, y2)

# gs.Line(
#     1,
#     x,
#     y,
#     label=r"y = $x^3 \int x \lambda \theta_{\rm K}$",
# ).plot()

# test = gs.style.legend.Legend(0).legend()
gs.style.legend_colormap.LegendColormap(
    1, max=1, min=0, num_stripes=100
).add_legend_colormap()


gs.style.Labels(
    [
        [
            "x",
            "y",
        ],
        [
            "x",
            "y",
        ],
    ],
    x_pad=2,
    y_pad=2,
    add_index=True,
)

gs.plts.Show()
