import pytest

# import gsplot as gs
import gsplot as gs
import matplotlib.pyplot as plt
import matplotlib as mpl


# fig = gs.figure(0, size=(10, 10), unit="pt", mosaic="AA", clear=True)


mpl.use("MacOSX")
axes = gs.plts.Axes(0, size=(500, 500), unit="pt", mosaic="A", clear=True)

test_axes = gs.plts._Axes()
print(test_axes.axes)


plt.show()
