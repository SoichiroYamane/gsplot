# 1. Explicit layouts

`gsplot.subplots` returns an explicit `Figure` and either an `Axes`, an array,
or a mosaic mapping. Each returned object is a native Matplotlib object.

## Example

The `unit` option accepts `in`, `cm`, `mm`, or `pt` and is converted to inches
before Matplotlib creates the Figure.

```{literalinclude} ../../../demo/1_axes/axes.py
```

```{image} ../../../demo/1_axes/axes.png
:alt: Explicit gsplot mosaic layout
:class: bg-primary
:width: 1000px
:align: center
```
