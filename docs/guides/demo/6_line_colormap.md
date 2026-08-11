# 6. Colormapped lines

`gsplot.cmap_line` maps one scalar value per polyline vertex to segment
colors. `gsplot.cmap_dash` uses the same validation with an explicit positive
dash pattern. Repeated points are ignored as zero-length segments.

```{literalinclude} ../../../demo/6_line_colormap/line_colormap.py
```

```{image} ../../../demo/6_line_colormap/line_colormap.png
:alt: Colormapped solid and dashed lines
:class: bg-primary
:width: 1000px
:align: center
```
