# 2. Line and Label

`gsplot.line` draws a line on a target axis. `gsplot.label` adds labels,
limits, and tick settings to the axes in a figure. A label entry can contain
`[x_label, y_label, [xlim, *args], [ylim, *args]]`; see the API reference for
the complete form.

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
