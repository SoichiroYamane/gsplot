import matplotlib.pyplot as plt
from gsplot.figure.axes_base import AxisTargetHandler
import matplotlib.gridspec as gridspec


fig = plt.figure()

# 位置を [左, 下, 幅, 高さ] の比率で指定 (0から1の範囲)
ax2 = fig.add_axes([0.2, 0.6, 0.6, 0.3])  # 上部に小さなAxes
ax1 = fig.add_axes([0.1, 0.1, 0.8, 0.4])  # 下部に大きなAxekkks

print(ax1)

input_test = ax1

test = AxisTargetHandler(input_test)
test_fig = test.get_figure()
print(test_fig)

test_axes = test.get_axes()
print(test_axes)

idx = test.get_idx_axis()
print(idx)

test_axis = test.get_axis()
print(test_axis)
