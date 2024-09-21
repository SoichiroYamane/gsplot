# import gsplot as gs
#
# gs.axes(store=False, mosaic="A")
# test = gs.line(
#     axis_index=0,
#     xdata=[1, 2, 3],
#     ydata=[1, 2, 3],
#     color="red",
#     markeredgecolor="black",
#     markerfacecolor="blue",
#     marker="o",
#     linestyle="--",
# )
# print(gs.get_pwd())


import matplotlib.pyplot as plt
import gsplot as gs

# Create a figure with 2 axes
axes = gs.axes(store=True, size=[5, 5], unit="in", mosaic="AB")

# Plot using plot method defined in Axes object
axes[0].plot([1, 2, 3], [1, 2, 3])

# Line plot function defined in gsplot
gs.line(axis_index=1, xdata=[1, 2, 3], ydata=[1, 2, 3])
