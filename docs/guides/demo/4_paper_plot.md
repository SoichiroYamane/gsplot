# 4. Example plot for a paper

This example combines configuration, data loading, inset axes, colormaps,
labels, legends, and square plot geometry in a publication-style figure.

## Example

### Main Functions

| Function                                                          | A Brief Overview                                          |
| :---:                                                             | :-------:                                                 |
| [gsplot.config_load](#gsplot.config.config.config_load)           | Load configuration file with a specific path              |
| [gsplot.axes](#gsplot.figure.axes.axes)                           | Add axes to a figure                                      |
| [gsplot.axes_inset](#gsplot.figure.axes_inset.axes_inset)               | Add inset axes to a figure                                |
| [gsplot.line](#gsplot.plot.line.line)                             | Add line plot to the axis specified by axis_target        |
| [gsplot.legend](#gsplot.style.legend.legend)                      | Add legend to the axis specified by axis_target           |
| [gsplot.graph_square_axes](#gsplot.style.graph.graph_square_axes) | Make all axes square                                      |
| [gsplot.label](#gsplot.style.label.label)                         | Add labels, limits, and ticks to all axes                 |
| [gsplot.label_add_index](#gsplot.style.label.label_add_index)     | Add index to all axes                                     |
| [gsplot.show](#gsplot.figure.show.show)                           | Save a figure when storage is enabled and optionally display it |

### Code

```{literalinclude} ../../../demo/4_paper_plot/paper_plot.py
```

```{note}
The example data is included in the repository and is also available
[here](https://github.com/SoichiroYamane/gsplot/tree/main/demo/data).
```

### Configuration

```{literalinclude} ../../../demo/4_paper_plot/gsplot.json
```

### Plot

```{image} ../../../demo/4_paper_plot/SC_cal.png
:alt: SC_cal
:class: bg-primary
:width: 1500px
:align: center
```
