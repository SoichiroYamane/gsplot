# import gsplot as gs
import gsplot as gs
import matplotlib.pyplot as plt


# fig = gs.figure(0, size=(10, 10), unit="pt", mosaic="AA", clear=True)


axes = gs.plts.Axes(0, size=(10, 10), unit="pt", mosaic="A", clear=True)

test_axes = gs.plts._Axes()
print(test_axes.axes)
