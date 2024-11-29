import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import gsplot as gsp


fig = plt.figure()


ax1 = fig.add_axes([0.1, 0.1, 0.8, 0.4])
ax2 = fig.add_axes([0.2, 0.6, 0.6, 0.3])


gsp.line(
    axis_target=ax1,
    x=[1, 2, 3],
    y=[1, 1, 1],
)
gsp.label(
    [
        ["A_x", "A_y"],
        ["B_x", "B_y"],
    ]
)

gsp.label_add_index(position="in", glyph="alphabet", capitalize=True)


gsp.show("test")
