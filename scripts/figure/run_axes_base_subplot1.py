import gsplot as gs
import matplotlib.pyplot as plt
import gsplot as gsp

fig, axs = plt.subplots(2, 2)

ax1 = axs[0, 0]
ax2 = axs[0, 1]
ax3 = axs[1, 0]
ax4 = axs[1, 1]


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
