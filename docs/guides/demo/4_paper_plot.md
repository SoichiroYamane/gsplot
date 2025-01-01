# 4. Example Plot for Paper

Create a cool plot with `gsplot` ✨

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
| [gsplot.show](#gsplot.figure.show.show)                           | Show a figure and save it if store in gsplot.axes is True |

### Code

```{literalinclude} ../../../demo/4_paper_plot/paper_plot.py
```

```{note}
Data can be available from [here](https://github.com/SoichiroYamane/gsplot/tree/main/demo/data)
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
