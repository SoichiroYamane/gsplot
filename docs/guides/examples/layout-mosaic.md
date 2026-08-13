# Explicit layouts

`gsplot.subplots` returns an explicit `Figure` and either an `Axes`, an array,
or a mosaic mapping. Each returned object is a native Matplotlib object.

## Example

The `unit` option accepts `in`, `cm`, `mm`, or `pt` and is converted to inches
before Matplotlib creates the Figure.

```{literalinclude} ../../../examples/layouts/mosaic.py
```

```{image} ../../../examples/layouts/axes.png
:alt: Explicit gsplot mosaic layout
:class: bg-primary
:width: 1000px
:align: center
```
