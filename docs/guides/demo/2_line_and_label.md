# 2. Line and Label

- [gsplot.line](#gsplot.plot.line.line) is a type of plot that displays information as a series of data points called 'markers' connected by straight lines. It is one of the most basic types of plots and is commonly used in data visualization.
- [gsplot.label](#gsplot.style.label.label) adds labels, limits, and ticks to all axes of the plot. It is used to provide additional information on axes. Argument of [gsplot.label](#gsplot.style.label.label) is `[x_label, y_label, [xlim, *args], [ylim, *args]]`. More details can be found in [gsplot.label](#gsplot.style.label.label).

## Example

### Main Functions

| Function                                               | A Brief Overview                                   |
| :---:                                                  | :-------:                                          |
| [gsplot.line](#gsplot.plot.line.line)                  | Add line plot to the axis specified by axis_target |
| [gsplot.legend_axes](#gsplot.style.legend.legend_axes) | Add legend to all axes                             |
| [gsplot.label](#gsplot.style.label.label)              | Add labels, limits, and ticks to all axes          |

### Code

```{literalinclude} ../../../demo/2_line_and_label/line_and_label.py
```

### Plot

```{image} ../../../demo/2_line_and_label/line_and_label.png
:alt: line_and_label
:class: bg-primary
:width: 1000px
:align: center
```
