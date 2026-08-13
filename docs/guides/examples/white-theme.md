# White-on-black theme

`gsplot.set_theme` applies a `Theme` to an explicit Figure or Axes. It does
not mutate Matplotlib's process-wide `rcParams`. This example sets black Figure
and Axes backgrounds with white text, spines, and ticks.

```{literalinclude} ../../../examples/themes/white.py
```

```{image} ../../../examples/themes/graph_white.png
:alt: Explicit dark theme applied to a Figure
:class: bg-primary
:width: 900px
:align: center
```
