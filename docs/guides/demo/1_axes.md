# 1. Axes

`gsplot.axes` returns a [list](https://docs.python.org/3/library/stdtypes.html#list)
of [matplotlib.axes.Axes](https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.html)
objects. You can create multiple axes in one figure with `mosaic`, and each
axis remains compatible with [Matplotlib](https://matplotlib.org).

## Example

### Main Functions

| Function                                | A Brief Overview                                          |
| :---:                                   | :-------:                                                  |
| [gsplot.axes](#gsplot.figure.axes.axes) | Add axes to a figure                                      |
| [gsplot.show](#gsplot.figure.show.show) | Show a figure and save it if store in gsplot.axes is True |

### Code

:::{tip}
`unit` lets the layout use a physical size such as `cm`, `mm`, or `pt`. This
helps keep figure dimensions and the default label sizing consistent when a
figure is prepared for a presentation or paper.

**PowerPoint**: Set `unit` to `cm` and insert the figure with the same size in
PowerPoint.

**Keynote**: Set `unit` to `pt` and insert the figure with the same size in
Keynote.
:::

```{literalinclude} ../../../demo/1_axes/axes.py
```

### Plot

```{image} ../../../demo/1_axes/axes.png
:alt: axes
:class: bg-primary
:width: 1000px
:align: center
```
