from ..plts.axes import AxesSingleton


# class ScatterColormap:
#     def __init__(self, axis_index, xdata, ydata, cmapdata, cmpa):
#         self.axis_index = axis_index
#         self.xdata = xdata
#         self.ydata = ydata
#         self.cmapdata = cmapdata
#         self.cmpa = cmpa
#
#
#
#         self.__axes = AxesSingleton()
#         self._axes = self.__axes.axes
#         self.axis = self._axes[self.axis_index]


# def Yama_colormap_plot(
#     plts_i,
#     datax,
#     datay,
#     colordata,
#     s=1,
#     cmap="viridis",
#     zorder=0,
#     alpha=1,
#     *args,
#     **kwargs,
# ):
#     cl_max = max(colordata)
#     cl_min = min(colordata)
#     cl_data = colordata
#     color_bar = (cl_data - cl_min) / (cl_max - cl_min)
#     plts_i.scatter(
#         datax,
#         datay,
#         c=color_bar,
#         cmap=cmap,
#         vmin=min(color_bar),
#         vmax=max(color_bar),
#         alpha=alpha,
#         s=s,
#         zorder=zorder,
#         *args,
#         **kwargs,
#     )
