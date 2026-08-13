# A publication-style plot

This example combines concise data loading, deterministic series styles, an
inset axis, labels, legends, and square panel geometry.
It uses the public paper and output defaults without rebuilding the profile in
application code. The dense three-panel layout uses an explicit
8.3-by-2.85-inch design canvas, producing an approximately 5000-pixel-wide PNG
at the standard 600 DPI while keeping its labels and inset within the
canvas. Ordinary multi-panel calls retain the 170 mm automatic default.

```{literalinclude} ../../../examples/publication/publication.py
```

The example data is included in the repository and is also available
[in the publication data directory](https://github.com/SoichiroYamane/gsplot/tree/main/examples/publication/data).

Running the example writes `SC_cal.png` and `SC_cal.pdf` transactionally from
the same Figure. `gs.save` uses 600 DPI for the PNG, Type 42 PDF fonts, and a
tight crop with 0.1-inch padding. Its default `show=True` displays the Figure
after successful output; the script then closes its explicitly owned Figure.
Sphinx regenerates both ignored build products in a fresh headless subprocess
and rejects missing or stale outputs.

The complete example is 74 physical lines, 62 executable lines, 2038
executable characters, and 11 gsplot calls. It retains the reviewed scientific
content while staying within the tracked source budgets.

```{image} ../../../examples/publication/SC_cal.png
:alt: Three line-chart panels showing gap, heat-capacity, and Yosida data, with one labeled heat-capacity inset and legends
:class: bg-primary
:width: 1500px
:align: center
```

[Download the generated vector PDF](../../../examples/publication/SC_cal.pdf).

The [publication guide](../publication.md) explains when to retain the design
canvas with `crop=False`, how these defaults relate to journal dimensions, and
which submission requirements still need independent verification.
