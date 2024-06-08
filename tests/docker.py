import gsplot as gs


gs.plts.Axes(mosaic="ABCD;EFGH", store=0, clear=True, ion=False)

x = [1, 2, 3, 4, 5]
y = [1, 4, 9, 16, 25]

x1 = [2, 3, 4, 5, 6]
y1 = [2, 5, 10, 17, 26]

gs.Line().plot(0, x, y, markersize=7, c="red", mec="black", mfc="blue", label="Line")
gs.Line().plot(
    0, x1, y1, markersize=7, c="red", mec="green", mfc="red", alpha=1, label="Line"
)
gs.Line().plot(1, x, y, markersize=7, c="red")
gs.Line().plot(2, x, y, markersize=7, c="red")
gs.Line().plot(3, x, y, markersize=7, color="red")

gs.style.Labels(
    [
        ["X-axis", "Y-axis"],
    ],
)

gs.plts.Show()
