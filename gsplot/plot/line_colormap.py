from ..params.params import Params
from ..base.base import AttributeSetter
from ..plts.axes_base import AxesSingleton, AxesRangeSingleton, AxisLayout
from ..style.legend_colormap import LegendColormap


import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np


class LineColormap:
    def __init__(
        self,
        axis_index: int,
        xdata: np.ndarray,
        ydata: np.ndarray,
        cmapdata: np.ndarray,
        cmap: str = "viridis",
        linewidth=1,
        linestyle="solid",
        linepattern=None,
        scale=None,
        label=None,
        *args,
        **kwargs,
    ):
        self.axis_index = axis_index
        self.__axes = AxesSingleton()
        self._axis = self.__axes.axes[self.axis_index]

        self.xdata = np.array(xdata)
        self.ydata = np.array(ydata)
        self.cmapdata = np.array(cmapdata)

        self.cmap = cmap
        self.linewidth = linewidth

        self.linestyle = self._check_linestyle(linestyle)
        self.linepattern = linepattern
        self.label = label
        self.args = args
        self.kwargs = kwargs

        self._set_legend()

    def _check_linestyle(self, linestyle):
        # Define the allowed line styles
        ls_dict = {
            "solid": "solid",
            "dashed": "dashed",
            "-": "solid",
            "--": "dashed",
        }

        # Check if the specified line style is allowed
        if linestyle not in ls_dict:
            raise ValueError(
                f"Invalid linestyle '{linestyle}'. Allowed values are {list(ls_dict.keys())}."
            )
        return ls_dict[linestyle]

    def _check_linepattern(self, linepattern):
        if linepattern is not None:
            if not isinstance(linepattern, (list, tuple)) or len(linepattern) != 2:
                raise ValueError(
                    "Invalid linepattern. It must be a list or tuple of length 2."
                )

        linepattern = self.DEFAULT_PATTERN if linepattern is None else linepattern
        linepattern = np.array(linepattern)
        return linepattern

    def plot_line_colormap(self):
        # Linestyle section
        if self.linestyle == "solid":
            LineColormapSolid(
                self.axis_index,
                self.xdata,
                self.ydata,
                self.cmapdata,
                self.cmap,
                self.linewidth,
                *self.args,
                **self.kwargs,
            ).plot_line_colormap_solid()
            pass
        elif self.linestyle == "dashed":
            # unit is inches
            self.DEFAULT_PATTERN = [0.1, 0.1]
            self.length_solid, self.length_gap = self._check_linepattern(
                self.linepattern
            )

            LineColormapDashed(
                self.axis_index,
                self.xdata,
                self.ydata,
                self.cmapdata,
                self.cmap,
                self.linewidth,
                self.length_solid,
                self.length_gap,
                *self.args,
                **self.kwargs,
            ).plot_dash_colormap()

    #! Bad statement of args and kwargs
    # TODO: Fix this part
    def _set_legend(self):
        NUM_STRIPES = 100
        if self.label is not None:
            LegendColormap(
                axis_index=self.axis_index,
                cmap=self.cmap,
                label=self.label,
                num_stripes=NUM_STRIPES,
                *self.args,
                **self.kwargs,
            ).add_legend_colormap()


class LineColormapBase:
    def __init__(self):
        pass

    def _create_segment(self, xdata, ydata):
        # Create a set of line segments so that we can color them individually
        # This creates the points as an N x 1 x 2 array so that we can stack points
        # together easily to get the segments. The segments array for line collection
        # needs to be (numlines) x (points per line) x 2 (for x and y)
        points = np.array([xdata, ydata]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        return segments

    def _create_cmap(self, cmapdata):
        # Create a continuous norm to map from data points to colors
        norm = plt.Normalize(cmapdata.min(), cmapdata.max())
        return norm


class LineColormapSolid:
    def __init__(self, axis_index, xdata, ydata, cmapdata, cmap, linewidth):
        self.axis_index = axis_index
        self.__axes = AxesSingleton()
        self.axis = self.__axes.axes[self.axis_index]

        self.xdata = xdata
        self.ydata = ydata
        self.cmapdata = cmapdata

        self.cmap = cmap
        self.linewidth = linewidth

    @AxesRangeSingleton.update
    def plot_line_colormap_solid(self):
        segments = LineColormapBase()._create_segment(self.xdata, self.ydata)
        norm = LineColormapBase()._create_cmap(self.cmapdata)

        lc = LineCollection(segments, cmap=self.cmap, norm=norm)
        lc.set_array(self.cmapdata)
        lc.set_linewidth(self.linewidth)
        self.axis.add_collection(lc)


class LineColormapDashed:
    def __init__(
        self,
        axis_index,
        xdata,
        ydata,
        cmapdata,
        cmap,
        linewidth,
        length_solid,
        length_gap,
        xspan=None,
        yspan=None,
    ):
        self.axis_index = axis_index
        self.__axes = AxesSingleton()
        self.axis = self.__axes.axes[self.axis_index]

        self.xdata = xdata
        self.ydata = ydata
        self.cmapdata = cmapdata

        self.cmap = cmap
        self.linewidth = linewidth
        self.length_solid = length_solid
        self.length_gap = length_gap

        xspan_data, yspan_data = self._get_data_span()

        self.xspan = xspan_data if xspan is None else xspan
        self.yspan = yspan_data if yspan is None else yspan

        # unit is inches
        self.xaxis_inches, self.yaxis_inches = AxisLayout(
            self.axis_index
        ).get_axis_size_inches()

        SCALE_FACTOR = 1

        self.xscale = self.xaxis_inches / (self.xspan * SCALE_FACTOR)
        self.yscale = self.yaxis_inches / (self.yspan * SCALE_FACTOR)

        self._create_uniform_coordinates()

    def normal_interpolate_points(self, num_points):
        xdiff = np.diff(self.xdata)
        ydiff = np.diff(self.ydata)
        distances = np.sqrt(xdiff**2 + ydiff**2)
        cumulative_distances = np.insert(np.cumsum(distances), 0, 0)
        interpolated_distances = np.linspace(0, cumulative_distances[-1], num_points)

        x_interpolated = np.interp(
            interpolated_distances, cumulative_distances, self.xdata
        )
        y_interpolated = np.interp(
            interpolated_distances, cumulative_distances, self.ydata
        )

        # Interpolate cmapdata
        cmap_interpolated = np.interp(
            interpolated_distances, cumulative_distances, self.cmapdata
        )

        return x_interpolated, y_interpolated, cmap_interpolated

    def _get_data_span(self):
        xmax, xmin = np.max(self.xdata), np.min(self.xdata)
        ymax, ymin = np.max(self.ydata), np.min(self.ydata)
        xspan = xmax - xmin
        yspan = ymax - ymin
        return np.array([xspan, yspan])

    def _create_uniform_coordinates(self):
        self.scaled_xdata = self.xdata * self.xscale
        self.scaled_ydata = self.ydata * self.yscale

        self.scaled_xdiff = np.diff(self.scaled_xdata)
        self.scaled_ydiff = np.diff(self.scaled_ydata)
        self.scaled_distances = np.sqrt(self.scaled_xdiff**2 + self.scaled_ydiff**2)
        self.scaled_total_distances = np.sum(self.scaled_distances)

        FACTOR = 5
        NUM_POINTS = int(self.scaled_total_distances * FACTOR // self.length_solid)
        print("NUMPOINTS", NUM_POINTS)

        self.x_interpolated, self.y_interpolated, self.cmap_interpolated = (
            self.normal_interpolate_points(NUM_POINTS)
        )

        self.scaled_inter_xdiff = np.gradient(self.x_interpolated * self.xscale)
        self.scaled_inter_ydiff = np.gradient(self.y_interpolated * self.yscale)
        self.scaled_inter_distances = np.sqrt(
            self.scaled_inter_xdiff**2 + self.scaled_inter_ydiff**2
        )

    @AxesRangeSingleton.update
    def plot_dash_colormap(self):
        current_length = 0
        draw_dash = True
        idx_start = 0

        norm = LineColormapBase()._create_cmap(self.cmapdata)

        for i in range(len(self.x_interpolated) - 1):
            current_length += self.scaled_inter_distances[i]

            if draw_dash:
                if current_length >= self.length_solid:
                    segments = LineColormapBase()._create_segment(
                        self.x_interpolated[idx_start : i + 1],
                        self.y_interpolated[idx_start : i + 1],
                    )

                    lc = LineCollection(
                        segments,
                        cmap=self.cmap,
                        norm=norm,
                    )
                    lc.set_array(self.cmap_interpolated[idx_start : i + 1])
                    lc.set_linewidth(self.linewidth)
                    lc.set_linestyle("solid")
                    self.axis.add_collection(lc)

                    draw_dash = False
                    current_length = 0
                    idx_start = i
            else:
                if current_length >= self.length_gap:
                    draw_dash = True
                    current_length = 0
                    idx_start = i

            # at last with the last point if draw_dash is True
            if i == len(self.x_interpolated) - 2 and draw_dash:
                segments = LineColormapBase()._create_segment(
                    self.x_interpolated[idx_start:],
                    self.y_interpolated[idx_start:],
                )

                lc = LineCollection(
                    segments,
                    cmap=self.cmap,
                    norm=norm,
                )
                lc.set_array(self.cmap_interpolated[idx_start:])
                lc.set_linewidth(self.linewidth)
                lc.set_linestyle("solid")
                self.axis.add_collection(lc)
