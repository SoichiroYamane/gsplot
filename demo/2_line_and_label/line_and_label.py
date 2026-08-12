import gsplot as gs

fig, axes = gs.subplots("AB", size=(10, 5))

for i in range(7):
    x = [i, i + 1, i + 2]
    y = [i, i, i]

    gs.line(axes["A"], x, y, series=i, label=f"line {i}")
    gs.line(axes["B"], x, y, series=i, label=f"line {i}")

gs.legend(axes)
gs.label(axes, "x", "y", (-1, 10), (-1, 10), square=True, index="in")
gs.savefig(fig, "line_and_label", show=False, overwrite=True)
