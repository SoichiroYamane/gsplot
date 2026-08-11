import gsplot as gs

fig, axes = gs.subplots(figsize=(10, 5), mosaic="AB")

for i in range(7):
    x = [i, i + 1, i + 2]
    y = [i, i, i]

    props = {"label": f"line {i}"}
    gs.line(axes["A"], x, y, props=props)
    gs.line(axes["B"], x, y, props=props)

gs.legends(fig)
gs.style_axes(axes, gs.AxisSpec(xlabel="x", ylabel="y", xlim=(-1, 10), ylim=(-1, 10)))
gs.panel_labels(axes)
gs.savefig(fig, "line_and_label", show=False, overwrite=True)
