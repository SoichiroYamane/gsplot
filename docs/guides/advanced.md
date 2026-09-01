# Advanced control and Matplotlib interoperability

The concise API handles common publication work. Advanced functions expose
explicit layout, styling, colored-artist, configuration, and output controls
without replacing Matplotlib's object model.

## Keep ambient Matplotlib behavior

Disable gsplot's paper size, layout, or style explicitly when integrating with
an existing application:

```python
fig, ax = gs.subplots(size=None, layout="none", style=None)
```

For a reused Figure, omitted automatic values preserve its existing size,
layout, and style. `clear=False` prevents accidental destruction of artists.

## Mix native Matplotlib and gsplot

```python
import matplotlib.pyplot as plt
import gsplot as gs

fig, ax = plt.subplots()
ax.plot(x, reference, color="0.5", label="reference")
gs.line(ax, x, measured, series=0, label="measured")
gs.label(ax, "time (s)", "response")
gs.legend(ax)
fig.canvas.draw()
```

gsplot returns ordinary Matplotlib artists. Continue using `Axes`, `Figure`,
and Artist methods directly whenever that is clearer.

## Finite advanced operations

- `style_axes`, `AxisSpec`, `minor_ticks`, `box_aspect`, `panel_labels`, and
  `set_theme` expose explicit styling plans.
- `cmap_line`, `cmap_dash`, `cmap_scatter`, `sample_cmap`, and `cmap_legend`
  cover data-mapped colors.
- `inset_axes` with `InsetSpec` supports placement beyond concise normalized
  bounds.
- `read_array` exposes the reviewed NumPy loader option mapping.
- `savefig` retains conservative one-format output and explicit advanced
  Matplotlib save properties. `save` is the concise PNG+PDF workflow.

The compatibility-only `props` mapping remains accepted through 1.x, but new
`line`, `scatter`, and `legend` calls should use their typed direct options.
Unknown options and duplicate short/long aliases fail before artist mutation.

## Colormap legends

`cmap_legend` creates one native Matplotlib `Legend` entry whose handle is a
horizontal gradient of adjacent rectangles. `stripes` is clamped to 256, and
`reverse=True` reverses the final left-to-right RGBA sequence. With
`label=None`, the function returns an empty native Legend; `replace=True` is
required when replacing an existing canonical Legend.

```python
fig, ax = gs.subplots()
gs.cmap_legend(
    ax,
    cmap="viridis",
    label="intensity",
    stripes=16,
    norm=(0.0, 2.0),
)
```

The deprecated `gsplot.legend_colormap` and
`gsplot.style.legend_colormap.legend_colormap` routes retain the historical
`num_stripes`, `vmin`, and `vmax` arguments, including positional calls. Their
finite raw values are passed directly to the colormap as
`linspace(vmin, vmax, N_effective)`; this is intentionally different from the
canonical synthetic `[0, 1]` positions and `norm` behavior. The legacy
function always safely replaces the current Legend because it has no
`replace` argument. Neither route mutates Matplotlib's default handler map or
adds an invisible proxy patch to the Axes.

Automatic gradient Legends for `cmap_line`, `cmap_dash`, `cmap_scatter`, and
the legacy colored plotter classes are outside this compatibility repair and
remain a separate task.

## Multiple figures and lifecycle

Every operation receives its target explicitly. Keep each Figure reference,
save or show the intended Figure, and close Figures that your script owns:

```python
import matplotlib.pyplot as plt
import gsplot as gs

first, ax1 = gs.subplots()
second, ax2 = gs.subplots()
gs.line(ax1, x, y1)
gs.line(ax2, x, y2)
gs.save(first, "first", show=False)
gs.save(second, "second", show=False)
plt.close(first)
plt.close(second)
```

`show(target)` is display-only. `save(..., close=True)` is available only when
`show=False`; gsplot never silently closes a displayed user-owned Figure.
