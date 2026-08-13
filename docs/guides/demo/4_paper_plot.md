# 4. A publication-style plot

This example combines concise data loading, deterministic series styles,
inset axes, exact zoom connectors, labels, legends, and square panel geometry.
It uses the public defaults directly rather than rebuilding the paper profile
in application code.

```{literalinclude} ../../../demo/4_paper_plot/paper_plot.py
```

The example data is included in the repository and is also available
[in the demo data directory](https://github.com/SoichiroYamane/gsplot/tree/main/demo/data).

Running the example writes `SC_cal.png` and `SC_cal.pdf` transactionally from
the same Figure. `gs.save` uses 600 DPI for the PNG, Type 42 PDF fonts, and a
tight crop with 0.1-inch padding. Its default `show=True` displays the Figure
after successful output; the script then closes its explicitly owned Figure.
Sphinx regenerates both ignored build products in a fresh headless subprocess
and rejects missing or stale outputs.

The complete example is 82 physical lines, 69 executable lines, 2189
executable characters, and 12 gsplot calls. It retains the reviewed scientific
content while staying within the tracked source budgets.

```{image} ../../../demo/4_paper_plot/SC_cal.png
:alt: Three line-chart panels showing gap, heat-capacity, and Yosida data, with two heat-capacity insets and legends
:class: bg-primary
:width: 1500px
:align: center
```

The [publication guide](../publication.md) explains when to retain the design
canvas with `crop=False`, how these defaults relate to journal dimensions, and
which submission requirements still need independent verification.
