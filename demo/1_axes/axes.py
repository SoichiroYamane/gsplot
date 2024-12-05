import gsplot as gs

# Create figure size (10 x 5) inches  with two axes defined by the mosaic
axes = gs.axes(
    store=True,
    size=[10, 5],
    mosaic="""
           ABBB
           ACCD
           """,
)
# You can also use the following syntax
# axes = gs.axes(store=True, size=[10, 5], mosaic="ABBB;ACCD")

# Show figure and store figure with the name "axes"
gs.show("axes")
