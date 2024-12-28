import gsplot as gs

# Create figure size (10 x 5) inches  with two axes defined by the mosaic
# Unit can be "in", "cm", "mm", and "pt". Default is "in".
axs = gs.axes(
    store=True,
    size=[10, 5],
    unit="in",
    mosaic="""
           ABBB
           ACCD
           """,
)
# You can also use the following syntax
# axs = gs.axes(store=True, size=[10, 5], unit="in", mosaic="ABBB;ACCD")

# Show figure and store figure with the name "axes"
gs.show("axes")
