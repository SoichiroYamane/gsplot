import gsplot as gs

gs.axes(store=False, mosaic="A")
test = gs.line(
    axis_index=0,
    xdata=[1, 2, 3],
    ydata=[1, 2, 3],
    color="red",
    markeredgecolor="black",
    markerfacecolor="blue",
    marker="o",
    linestyle="--",
)
print(gs.get_pwd())
