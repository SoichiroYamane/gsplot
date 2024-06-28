# from ..figure.axes import _Axes
# from ..figure.axes_tool import AxisRangeController
# from ..figure.axes_tool import AxisRangeManager
#
# import numpy as np
#
#
# class LineCollectionRangeController:
#     def __init__(self, axis_index: int, xdata: np.ndarray, ydata: np.ndarray):
#         self.axis_index = axis_index
#         self.xdata = xdata
#         self.ydata = ydata
#
#         self.__axes = _Axes()
#         self._axes = self.__axes.axes
#         self.axis = self._axes[self.axis_index]
#
#         self._is_init_axis = AxisRangeManager(self.axis_index).is_init_axis()
#
#         self.xrange, self.yrange = self._get_axis_range()
#
#     def _get_axis_range(self):
#         if self._is_init_axis:
#             axis_xrange = None
#             axis_yrange = None
#         else:
#             axis_xrange = AxisRangeController(self.axis_index).get_axis_xrange()
#             axis_yrange = AxisRangeController(self.axis_index).get_axis_yrange()
#         return axis_xrange, axis_yrange
#
#     def _calculate_data_range(self, data) -> np.ndarray:
#         min_data = np.min(data)
#         max_data = np.max(data)
#         return np.array([min_data, max_data])
#
#     def _calculate_padding_range(self, range: np.ndarray) -> np.ndarray:
#         PADDING_FACTOR = 0.05
#         span = range[1] - range[0]
#         return range + np.array([-PADDING_FACTOR, PADDING_FACTOR]) * span
#
#     def set_axis_range(self):
#         xrange, yrange = self._get_axis_range()
#         xrange_data, yrange_data = (
#             self._calculate_data_range(self.xdata),
#             self._calculate_data_range(self.ydata),
#         )
#
#         if xrange is None or yrange is None:
#             new_xrange = xrange_data if xrange is None else xrange
#             new_yrange = yrange_data if yrange is None else yrange
#
#             new_xrange_padding = self._calculate_padding_range(new_xrange)
#             new_yrange_padding = self._calculate_padding_range(new_yrange)
#
#             AxisRangeController(self.axis_index).set_axis_xrange(new_xrange_padding)
#             AxisRangeController(self.axis_index).set_axis_yrange(new_yrange_padding)
#         else:
#             new_xrange = np.array(
#                 [min(xrange[0], xrange_data[0]), max(xrange[1], xrange_data[1])]
#             )
#             new_yrange = np.array(
#                 [min(yrange[0], yrange_data[0]), max(yrange[1], yrange_data[1])]
#             )
#
#             new_xrange_padding = self._calculate_padding_range(new_xrange)
#             new_yrange_padding = self._calculate_padding_range(new_yrange)
#
#             AxisRangeController(self.axis_index).set_axis_xrange(new_xrange_padding)
#             AxisRangeController(self.axis_index).set_axis_yrange(new_yrange_padding)
