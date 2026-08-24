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

## Mosaic iteration order

Mosaic mappings iterate in panel-name (alphabetical) order, not in mosaic
first-appearance order. `"ACE;BDE"` iterates as `('A', 'B', 'C', 'D', 'E')`
even though the specification mentions C and E before B and D. Integer
indexes and slices follow that same order.

Per-target value sequences — label records, titles, limits, colors, or
generated panel indexes — therefore line up with the panel letters: the first
record belongs to A, the second to B, and so on. Exact-key dictionaries such
as `{"A": ..., "B": ...}` also work when you want to be explicit. Keyed access
such as `axes["B"]` never depends on position.
