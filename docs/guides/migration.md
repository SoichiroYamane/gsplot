# Migration to the concise API

The concise API restores the economy and publication defaults of gsplot 0.3
without restoring caller inspection, hidden current-Figure ownership, global
color counters, implicit configuration discovery, or import-time `rcParams`
changes.

## Common replacements

| Historical or repair-era form | Concise form |
| --- | --- |
| `axes(...)` | `fig, ax = subplots(...)` |
| `figsize=(w, h)` | `size=(w, h)` with an explicit `unit` when needed |
| `tight_layout=True` | `layout="tight"`; the new-Figure default is constrained |
| `line(ax, x, y, props={...})` | `line(ax, x, y, label=..., lw=..., ms=...)` |
| `scatter(ax, x, y, props={...})` | `scatter(ax, x, y, label=..., s=...)` |
| `axes_inset(...)` | `inset(parent, bounds, label=..., zoom=...)` |
| `label_add_index(...)` | `index(target)` or `label(..., index="in")` |
| `legend_axes(...)` | `legend(target)` |
| historical saving `show(...)` | `save(fig, path)` |
| `load_file(...)` | `read(path)` |
| implicit `gsplot.json` | `config = load_config(path)` and `config=config` |

The advanced names `savefig`, `style_axes`, `inset_axes`, colored plotting
helpers, and typed styling values remain supported; they are no longer needed
for the primary publication recipe.

## Defaults that intentionally changed

- New Figures use an 85/170 mm automatic paper canvas, constrained layout,
  and target-local paper style. Pass `size=None`, `layout="none"`, and
  `style=None` for ambient Matplotlib behavior.
- `legend` defaults to best placement rather than the historical lower-left
  position. Pass `loc="lower left"` when placement is part of the figure's
  meaning.
- `read` defaults to comma-delimited input with `unpack=True`. Use
  `delimiter=None` for whitespace-separated text or an explicit delimiter for
  tab-separated data.
- `save` defaults to PNG and PDF, 600-DPI raster output, tight crop,
  `show=True`, and overwrite. `savefig` retains its conservative advanced
  contract.
- Option-free `line` and `scatter` calls on ordinary Matplotlib Axes use that
  Axes property cycle. Use `series=n`, an explicit color, or `paper(ax)` for a
  deterministic publication identity.

## Compatibility window

Safe historical root names and documented module imports remain adapters
through 1.x. Valid concise calls do not warn. Historical call forms warn at the
compatibility boundary, and candidate removal is no earlier than 2.0 after a
separate breaking-change review.

The complete import, signature, default, return, warning, and exception matrix
is maintained in the
[API migration contract](../project/api-migration.md). The
[compatibility demonstration](demo/9_compatibility.md) is intentionally the
only numbered plotting demo that uses the deprecated 0.x workflow.
