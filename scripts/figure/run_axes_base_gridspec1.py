import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import gsplot as gsp


fig = plt.figure()
gs = gridspec.GridSpec(3, 3)

ax1 = fig.add_subplot(gs[0, :])
ax2 = fig.add_subplot(gs[1, :-1])
ax3 = fig.add_subplot(gs[1:, -1])
ax4 = fig.add_subplot(gs[-1, 0])

gsp.line(
    axis_target=ax1,
    x=[1, 2, 3],
    y=[1, 1, 1],
)
gsp.label(
    [
        ["A_x", "A_y"],
        ["B_x", "B_y"],
        ["C_x", "C_y"],
        ["D_x", "D_y"],
    ]
)
gsp.label_add_index(position="in", glyph="alphabet", capitalize=True)


gsp.show("test")
