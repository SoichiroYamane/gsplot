# Publication figures

gsplot's paper defaults are a strong starting point for scientific figures;
they are not certification for a particular journal. Always check the current
instructions for the journal and article type before submission.

## Concise recipe

```python
import gsplot as gs

fig, ax = gs.subplots("AB")
gs.line(ax["A"], x, signal, series=0, label="signal")
gs.scatter(ax["B"], x, residual, series=1, label="residual", s=8)
gs.label(ax, (("time (s)", "signal"), ("time (s)", "residual")), index="in")
gs.legend(ax)
gs.save(fig, "figure", show=False)
```

`subplots("AB")` returns native Matplotlib objects and selects a 170 mm wide
design canvas, constrained layout, and target-local paper style. A one-column
layout uses 85 mm. `line`, `scatter`, `label`, and `legend` validate complete
multi-Axes plans before mutating the first target.

For a complete data-backed recipe, see
[the publication example](examples/publication.md).

## Defaults owned by gsplot

| Area | Paper baseline |
| --- | --- |
| Canvas | 85 mm for one column; 170 mm for two or more columns |
| Layout | constrained for a new Figure |
| Typography | 10 pt DejaVu Sans; 6 pt axis-label padding |
| Axes | white face, zero margins, visible 0.8 pt black spines, no grid |
| Ticks | inward on all four sides; major 3.5×0.8 pt; minor 2×0.6 pt |
| Legend | best placement, frameless, non-fancy, 0.3 label spacing |
| Raster output | PNG at 600 DPI |
| Vector output | PDF with Type 42 fonts |
| Crop | tight bounding box with 0.1-inch padding |

These values affect only explicit Figures, Axes, or output operations. gsplot
does not change global `rcParams` during import.

## Design canvas and tight crop

The Figure size is the design canvas. The default tight crop removes unused
outer space when writing each file, so the exported media box may be smaller
than 85 or 170 mm. Use `crop=False` when the submission system requires exact
canvas dimensions:

```python
gs.save(fig, "figure", crop=False, show=False)
```

For a different target width, set the Figure size explicitly and keep the unit
beside the values:

```python
fig, ax = gs.subplots(size=(90, 60), unit="mm")
```

When an independent gsplot annotation is intentionally placed beyond an Axes,
pass `figure_fit=True` to `subplots`. The policy keeps `index`, `panel_labels`,
Axes titles, and Figure suptitles inside the fixed Figure canvas without
resizing the Figure or moving Axes. Axis labels, tick labels, and legends
remain under Matplotlib's layout rules:

```python
fig, ax = gs.subplots(
    size=(246, 400),
    unit="pt",
    figure_fit=True,
)
gs.index(ax, loc="corner", offset=(-42, 0))
gs.save(fig, "figure.pdf", crop=False, show=False)
```

`figure_fit=True` is a placement policy, not a tight-crop override. Use
`crop=False` when the PDF or image media box must equal the requested Figure
canvas; `crop=True` may change the physical output dimensions.

## Submission checklist

- Design and inspect the figure at its final physical size.
- Confirm the journal's permitted file formats, dimensions, and raster
  resolution; these rules differ by publisher and article type.
- Check that labels remain readable and lines and markers remain distinct
  after scaling.
- Prefer vector output for charts when accepted, and verify embedded fonts.
- Inspect color, grayscale, and a color-vision-deficiency simulation. Do not
  encode meaning by color alone; combine color with line style, marker, or
  direct labels.
- Crop accidental white space, but retain required margins and prevent labels
  from being clipped.
- Provide captions and alt text according to the target journal's current
  accessibility policy.

Current official references include the
[APS figure guidance](https://journals.aps.org/authors/style-basics),
[AIP author instructions](https://publishing.aip.org/resources/researchers/author-instructions/),
[PLOS ONE figure requirements](https://journals.plos.org/plosone/s/figures),
and
[Elsevier artwork guidance](https://www.elsevier.com/about/policies-and-standards/author/artwork-and-media-instructions/artwork-overview).
These external requirements can change; the links, not this page, are the
authority for a submission.
