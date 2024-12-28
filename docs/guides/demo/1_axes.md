# 1. Axes

- [gsplot.axes](#gsplot.figure.axes.axes) provide a [list](https://docs.python.org/3/library/stdtypes.html#list) of [matplotlib.axes.Axes](https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.html). They are the most important part of a figure and are axes where the data are plotted. You can have multiple axes in a single figure by `mosaic`, each axis is compatible to [matplotlib](https://matplotlib.org).

## Example

### Main Functions

| Function                                | A Brief Overview                                          |
| :---:                                   | :-------:                                                  |
| [gsplot.axes](#gsplot.figure.axes.axes) | Add axes to a figure                                      |
| [gsplot.show](#gsplot.figure.show.show) | Show a figure and save it if store in gsplot.axes is True |

### Code

:::{tip}
`unit` provides a way to set [gsplot.label](#gsplot.style.label.label) of `10 px` (default) to all axes of the figure. This ensures consistency when creating presentations with a unified style.
his ensures consistency when creating presentations with a unified style.

**PowerPoint**: Set the `unit` to `cm` and insert the figure with the same size in PowerPoint. The font size will default to `10 pt` on the PowerPoint slide

**Keynote**: Set the `unit` to `pt` and insert the figure with the same size in Keynote. The font size will default to `10 pt` on the Keynote slide
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
