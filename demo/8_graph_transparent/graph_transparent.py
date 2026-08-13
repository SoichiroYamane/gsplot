import gsplot as gs

fig, axes = gs.subplots("AB", size=(10, 5))
gs.set_theme(fig, gs.Theme.transparent())

x = [1, 2, 3, 4, 5]
y = [1, 4, 9, 16, 25]

gs.line(axes["A"], x, y, c="red")
gs.cmap_line(axes["B"], x, y, x, props={"linewidths": 2})
gs.style_axes(axes, gs.AxisSpec(xlabel="x", ylabel="y"))
gs.savefig(fig, "graph_transparent", show=False, overwrite=True)
