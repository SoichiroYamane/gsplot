import gsplot as gs

# Create a Figure and an explicit mosaic mapping.
fig, axes = gs.subplots(figsize=(10, 5), mosaic="ABBB;ACCD")
for name, axis in axes.items():
    gs.title(axis, f"Panel {name}")

# The output target and display policy are explicit.
gs.savefig(fig, "axes", show=False, overwrite=True)
