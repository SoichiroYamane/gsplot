import matplotlib.pyplot as plt
from gsplot.figure.axes_base import AxisTargetHandler
import matplotlib.gridspec as gridspec


fig = plt.figure()
gs = gridspec.GridSpec(3, 3)

ax1 = fig.add_subplot(gs[0, :])  # 上部の行を1つの大きなプロットに
ax2 = fig.add_subplot(gs[1, :-1])  # 左下に1つのプロット
ax3 = fig.add_subplot(gs[1:, -1])  # 右側の2行にまたがるプロット
ax4 = fig.add_subplot(gs[-1, 0])  # 左下のプロット

test = AxisTargetHandler(ax1)
test_fig = test.get_figure()
print(test_fig)

test_axes = test.get_axes()
print(test_axes)
