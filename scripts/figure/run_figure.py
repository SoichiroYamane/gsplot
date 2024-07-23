import gsplot as gs


gs.axes(
    mosaic="AB",
    clear=True,
    ion=True,
    store=True,
    size=[5, 5],
    unit="in",
)

test = gs.get_json_params()

# AxesHandlerTest(store=True, mosaic="A", size=[10, 5], test="test")
test2 = gs.get_cmap()
# gs.show()
