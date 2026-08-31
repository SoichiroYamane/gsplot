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

## Fixed-size output and annotations

An explicit `size` and `unit` define the Figure design canvas. Use
`figure_fit=True` when independent gsplot annotations may be placed outside an
Axes; `index`, `panel_labels`, `title`, and `suptitle` are shifted inward by
the minimum amount needed to remain visible without changing the Figure size.
Axis labels, tick labels, and legends remain under Matplotlib's layout rules.

Use `crop=False` when the exported PDF or image must retain the exact Figure
canvas dimensions. `crop=True` computes a tight content bounding box and may
change the physical output size even when `figure_fit=True` is enabled.

```python
import gsplot as gs

figure, axes = gs.subplots(
    size=(240, 400),
    unit="pt",
    figure_fit=True,
)
gs.index(axes, loc="corner", offset=(-42, 0))
gs.save(figure, "figure.pdf", crop=False, show=False)
```
