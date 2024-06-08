"""
def Yama_square_figure(plts):
    for plts_i in plts:
        plts_i.set_box_aspect(1)


def GioWhiteGraph(graph):
    graph.yaxis.label.set_color("w")
    graph.xaxis.label.set_color("w")
    graph.title.set_color("w")
    for child in graph.get_children():
        if hasattr(child, "set_color"):
            child.set_color("w")
    graph.tick_params(axis="x", colors="w")
    graph.tick_params(axis="y", colors="w")
    graph.patch.set_alpha(0)


def Yama_transparent(plts):
    plt.rcParams.update(
        {
            "figure.facecolor": (1.0, 0.0, 0.0, 0),  # red   with alpha = 30%
            "axes.facecolor": (0.0, 1.0, 0.0, 0),  # green with alpha = 50%
            "savefig.facecolor": (0.0, 0.0, 1.0, 0),  # blue  with alpha = 20%
        }
    )
    for plt_i in plts:
        plt_i.patch.set_alpha(0)
"""
