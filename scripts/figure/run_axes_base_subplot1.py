import gsplot as gs
import matplotlib.pyplot as plt

from gsplot.figure.axes_base import AxisTargetHandler

fig, axs = plt.subplots(2, 2)

test = AxisTargetHandler(axs[0, 0])

test_fig = test.get_figure()

print(test_fig)

test_axes = test.get_axes()
print(test_axes)
