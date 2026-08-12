# API migration matrix

This page is the cumulative migration matrix for the structural reform tracked
in [Issue #165](https://github.com/SoichiroYamane/gsplot/issues/165) and the
concise publication API tracked in
[Issue #183](https://github.com/SoichiroYamane/gsplot/issues/183). It maps the
historical 0.3 API, current 0.4 implementation, and approved 1.x concise target.
An entry describes target behavior only after its linked implementation slice
has merged; until then the current 0.4 column is runtime truth.

## Compatibility policy

- The canonical API is available from `import gsplot as gs`.
- The reform targets the 0.4.x compatibility line and the 1.x stabilization
  line. Legacy root calls and documented legacy module imports remain
  forwarding-only adapters throughout those lines.
- Candidate removal of legacy adapters is a separate decision for a future
  major release, no earlier than 2.0, after downstream usage has been
  audited.
- The primary concise surface is additive during 1.x. Existing advanced
  canonical functions, types, exceptions, legacy root forms, and documented
  compatibility modules remain importable through that line.
- The old `gsplot.base.*` implementation namespace is not a supported public
  compatibility surface unless it was part of the pre-cutover API reference.
- A compatibility adapter may normalize old arguments, but canonical modules
 must never import the compatibility layer or contain duplicate algorithms.

## Effective default-value matrix

Signature compatibility alone is not sufficient for plotting APIs. The
following matrix records the effective defaults during the compatibility
window.

| Surface | Historical 0.3 | Current 0.4 | Concise 1.x target |
| --- | --- | --- | --- |
| Figure size | 5 x 5 in | Matplotlib default unless explicit | `auto`: 85 mm for one column, 170 mm for multiple columns; tuple/preset override |
| Layout | tight | none unless explicit | constrained for a new Figure; preserve a reused Figure |
| Reused-Figure clearing | true | false | false |
| Style ownership | process-global import/config effects | ambient or explicit target helpers | target-local `paper` on newly created Axes |
| Line defaults | marker `o`, size 7, edge width 1.5, `--`, width 1, alpha 1, face alpha 0.2 | preserved by the root helper | preserved by concise `line` |
| Scatter defaults | marker `o`, size 1, alpha 1 | preserved by the root helper | preserved by concise `scatter` |
| Option-free color | historical shared viridis sequence | compatibility-dependent root sequence | target Axes cycle; pure `series=n` when requested |
| Labels | minor ticks, 5 pt pad, incidental relayout | explicit target via `AxisSpec` | minor ticks and 5 pt pad, no Figure relayout |
| Panel indexes | lowercase labels positioned from rendered bounds | `panel_labels`, uppercase generated labels | `index`, lowercase bijective labels at frozen Axes transforms |
| Legend | lower left, frameless, non-fancy, spacing 0.3 | explicit options, conservative replacement | `best` placement with frameless, non-fancy styling and spacing 0.3 |
| Save | PNG+PDF, 600 DPI, tight crop, show, overwrite | conservative `savefig`; suffix-free defaults to PNG | `save` restores historical flow transactionally; `savefig` unchanged |
| Display | coupled to historical save/store flow | `show(Figure)` is display-only | explicit Figure/same-Figure Axes, no-op on non-interactive backend |
| Config | implicit legacy JSON/singleton | explicit immutable schema 1 | explicit immutable schema 2; schema 1 translates through 1.x |
| Import | changed `rcParams` and initialized legacy services | side-effect-light | side-effect-light |

The historical shared color counter has been removed from ordinary root and
canonical `line` and `scatter` calls; they use the corresponding property
cycle of each target Axes unless an explicit color, Config color, or
deterministic `series=0..9` identity is supplied. Axes returned by the
deprecated `gs.axes()` adapter alone retain the shared five-color sequence in
weak compatibility state. The compatibility store flag remains isolated at
the root adapter boundary. Removing import-time Matplotlib `rcParams` mutation
is also intentional; ambient Matplotlib defaults apply unless an application
configures them explicitly.

## Current-to-concise root migration

The primary concise target is:

```text
subplots  inset  line  scatter  colors  label  index  square
legend  paper  save  show  read
```

| Current 0.4 surface | Concise target | 1.x classification and contract |
| --- | --- | --- |
| `subplots` | `subplots` | additive shape, auto-size, layout, style, and schema-2 support; native return retained |
| `inset_axes` | `inset` | new concise tuple-bounds adapter; advanced function retained |
| `line`, `scatter` | same names | additive direct finite options, multi-target preflight, and deterministic `series` |
| `sample_cmap` | `colors` | new concise sampler; advanced normalization API retained |
| `style_axes` | `label` | new concise records/shared-value operation; typed advanced API retained |
| `box_aspect` | `square` | concise finite-aspect spelling; advanced helper retained |
| `panel_labels` | `index` | concise lowercase labels and frozen transforms; advanced helper retained |
| `legend` | `legend` | additive direct finite paper defaults and multi-target semantics |
| `legends`, `legend_entries`, `cmap_legend` | unchanged advanced APIs | retained through 1.x |
| `set_theme`, `fig_facecolor` | `paper` plus unchanged advanced APIs | `paper` owns the publication baseline; other themes remain explicit |
| `title`, `suptitle`, `minor_ticks` | unchanged advanced APIs | retained; concise `label` covers common axis styling only |
| `savefig` | `save` | concise transactional historical workflow added; conservative advanced API retained |
| `show` | `show` | display-only ownership retained and generalized to same-Figure Axes targets |
| `read_array` | `read` | finite common NumPy options added; options-mapping API retained |
| `load_config` | `load_config` | explicit loading retained; schema 2 becomes canonical |
| `write_meta`, `build_info`, `use_backend` | unchanged advanced APIs | retained through 1.x |
| `cmap_line`, `cmap_dash`, `cmap_scatter` | unchanged advanced APIs | retained through 1.x |

### Line and scatter advanced option table

The primary introspection and API reference show only the concise parameters.
The following finite long spellings remain directly accepted through 1.x; the
same fields may be supplied through `props`, but one field cannot be supplied
both directly and through `props`. The short/long pairs `c`/`color`,
`ms`/`markersize`, `mew`/`markeredgewidth`, `mec`/`markeredgecolor`,
`mfc`/`markerfacecolor`, `ls`/`linestyle`, `lw`/`linewidth`, and `s`/`size`
are aliases and cannot be combined in one call.

| Operation | Retained finite direct options beyond the concise view |
| --- | --- |
| `line` | `color`, `markersize`, `markeredgewidth`, `markeredgecolor`, `markerfacecolor`, `linestyle`, `linewidth`, `antialiased`, `dash_capstyle`, `dash_joinstyle`, `drawstyle`, `fillstyle`, `gapcolor`, `markevery`, `markerfacecoloralt`, `picker`, `pickradius`, `solid_capstyle`, `solid_joinstyle`, `visible`, `zorder` |
| `scatter` | `color`, `size`, `cmap`, `norm`, `vmin`, `vmax`, `edgecolors`, `facecolors`, `linewidths`, `antialiaseds`, `plotnonfinite`, `rasterized`, `picker`, `visible`, `zorder` |

For `line`, alpha is materialized independently into the line and marker-edge
RGBA colors. Marker-face RGBA uses `alpha * alpha_mfc`; the Artist-level
`Line2D.alpha` remains unset so Matplotlib cannot override that independent
face transparency during rendering. This matches the 0.3 visual contract.

For multiple targets, one x/y pair broadcasts. Per-target x/y always uses an
exact-key mapping. Numeric and text style sequences may follow target order;
colors and other sequence-valued scalar styles use exact-key mappings to avoid
shape guessing. A retained Matplotlib scatter `c` value array remains a single
dataset-level advanced value rather than a per-target style sequence.

The public values `Config`, `AxisSpec`, `Theme`, `InsetSpec`,
`MetadataSnapshot`, `BuildInfo`, `LegendEntries`, `MosaicSpec`,
`NormalizeSpec`, and `ColorSpec`; all typed public exceptions; `__version__`;
and `__commit__` remain governed by the compatibility policy. New shared type
aliases `AxesTarget`, `PerTarget`, `LineStyle`, `Marker`, `Unit`, `SizePreset`,
`SizeSpec`, `LayoutMode`, and `StyleMode` are additive and remain valid on
Python 3.10.

## Configuration schema migration

Canonical JSON loading remains explicit. Schema 1 is translated into a fresh
immutable schema-2 value and emits one caller-facing migration warning; input
files are never rewritten.

| Schema-1 field | Schema-2 field/value | Translation and compatibility |
| --- | --- | --- |
| `schema_version: 1` | `schema_version: 2` | accepted through 1.x with one migration warning |
| `figure.figsize: [w, h]` | `figure.size: [w, h]` | exact finite positive tuple in `figure.unit` |
| `figure.figsize: null` | `figure.size: null` | preserves the ambient Matplotlib size contract |
| `figure.unit` | `figure.unit` | unchanged; schema 2 permits non-inch units only for tuple size |
| `figure.squeeze` | `figure.squeeze` | unchanged boolean |
| `tight_layout: true`, constrained false | `figure.layout: "tight"` | deterministic translation |
| constrained true, `tight_layout: false` | `figure.layout: "constrained"` | deterministic translation |
| both layout flags false or omitted | `figure.layout: "none"` | deterministic translation |
| both layout flags true | no value | remains `ConfigError` before Config creation |
| `plotting.default_color` | same field | unchanged; `"axes"` remains the cycle sentinel |
| `plotting.default_cmap` | same field | unchanged non-empty colormap name |
| `plotting.nonfinite` | same field | unchanged reviewed policy |

`Config()` changes from schema-1 Figure defaults (`figsize=None`, inch unit,
no layout) to schema-2 concise defaults (`size="auto"`, inch unit,
`squeeze=True`, `layout="auto"`). Deprecated `Config.figure.figsize`,
`tight_layout`, and `constrained_layout`, plus equivalent `Config.get()`
lookups, remain through 1.x. The `figsize` view returns a tuple only for tuple
size and returns `None` for named presets or null; layout views report equality
with their named mode. Each deprecated read warns and never mutates Config.

Schema 2 adds no keys for paper style, line/scatter options, output paths,
overwrite, display/close policy, series identity, arbitrary labels, metadata,
backend selection, logging, or open Matplotlib property dictionaries.

## Root export migration

The classification uses these terms:

- **canonical**: the spelling and ownership used by new code;
- **adapter**: the old spelling remains callable and forwards to the
  canonical implementation;
- **breaking**: new code must use a different name, ownership model, return
  contract, or configuration contract;
- **docs-only**: retained as an explanatory example rather than as a
  supported runtime API.

| 0.3.x root name | Reform target | Classification | Migration contract |
| --- | --- | --- | --- |
| `axes` | `subplots` | adapter + breaking return contract | New code receives `(Figure, axes)` and owns the returned objects explicitly. The old flat-list behavior is isolated in `_compat`. |
| `axes_inset` | `inset_axes` | adapter + breaking signature | The parent `Axes` and typed `InsetSpec` are explicit. |
| `axes_inset_padding` | `inset_axes` | adapter | Padding is represented by `InsetSpec`; no current-object lookup. |
| `get_figure_size` | `Figure.get_size_inches()` | adapter | New code uses the Matplotlib figure directly; a compatibility helper may preserve the old convenience call. |
| `show` | `savefig` and `show` | adapter + breaking behavior | `savefig(fig, ..., show=True)` saves before displaying. Canonical `show(fig)` displays only and never saves or closes. |
| `get_cmap` | `sample_cmap` | adapter + breaking signature | Sampling returns a typed `N x 4` array and validates count, values, and normalization explicitly. |
| `line` | `line` | canonical rename retained | The target takes an explicit `Axes`, returns `list[Line2D]`, and uses a closed property schema rather than an open keyword bag. |
| `line_colormap_solid` | `cmap_line` | adapter + breaking name | The target owns colored-segment validation and returns a `LineCollection`. |
| `line_colormap_dashed` | `cmap_dash` | adapter + breaking name | The target returns a tuple of `LineCollection` objects and validates positive dash lengths. |
| `scatter` | `scatter` | canonical rename retained | The target takes an explicit `Axes` and returns the Matplotlib `PathCollection`. |
| `scatter_colormap` | `cmap_scatter` | adapter + breaking name | The target validates color data and returns a `PathCollection`. |
| `graph_square` | `box_aspect` | adapter + breaking name | Aspect application is explicit and does not inspect a caller frame or global axes store. |
| `graph_square_axes` | `box_aspect` | adapter | The target accepts an explicit `Axes` or typed target collection. |
| `graph_white` | `set_theme` | adapter + breaking name | Theme application is explicit and does not mutate global `rcParams`. |
| `graph_white_axes` | `set_theme` | adapter | The target takes a `Figure` or `Axes` target and a `Theme` value. |
| `graph_transparent` | `set_theme` | adapter + breaking name | Transparency is a named theme value rather than an implicit current-figure operation. |
| `graph_transparent_axes` | `set_theme` | adapter | The target takes an explicit target. |
| `graph_facecolor` | `fig_facecolor` | adapter + breaking name | Figure ownership is explicit. |
| `label` | `style_axes` | adapter + breaking name | Axis labels, limits, scales, ticks, and padding use typed `AxisSpec` values. |
| `label_add_index` | `panel_labels` | adapter + breaking name | Panel targets and label placement are explicit and return created `Text` objects. |
| `title` | `title` | adapter + breaking ownership | The canonical call targets an explicit `Axes`; figure-level text uses `suptitle`. |
| `title_axes` | `title` | adapter | The old current-axes behavior forwards to the explicit target form. |
| `legend` | `legend` | canonical rename retained | Handles, labels, handler maps, replacement, and properties are explicit. |
| `legend_axes` | `legends` | adapter + breaking name | The target returns all legends on an explicit target. |
| `legend_handlers` | `legend` | adapter | Handler maps become local call arguments and are never global mutable state. |
| `legend_reverse` | `legend` | adapter | Reversal is an explicit `reverse` option. |
| `legend_get_handlers` | `legend_entries` | adapter + breaking name | The target returns a typed `LegendEntries` value. |
| `legend_colormap` | `cmap_legend` | adapter + breaking name | Colormap legend construction uses explicit handles, labels, and color mapping. |
| `ticks_off` | `minor_ticks` | adapter + breaking name | The target has one explicit `enabled` operation. |
| `ticks_on` | `minor_ticks` | adapter + breaking name | The target has one explicit `enabled` operation. |
| `ticks_on_axes` | `minor_ticks` | adapter | The target accepts explicit axes and an axis selector. |
| `load_file` | `read_array` | adapter + breaking name | The target has explicit loader, `ndmin`, and option validation and never changes the working directory. |
| `load_file_fast` | `read_array` | adapter | The loader choice is explicit rather than encoded in a second public function. |
| `config_load` | `load_config` | adapter + breaking name | Loading is explicit and returns an immutable `Config`. Importing the package does not load files. |
| `config_dict` | `Config` | adapter + breaking ownership | Configuration is a typed immutable value, not a mutable process-wide dictionary. |
| `config_entry_option` | `Config.get` / `Config.section` | adapter | Accessors validate the schema and do not expose mutable global state. |
| `save_metadata` | `write_meta` | adapter + breaking ownership | Metadata destination and snapshot are explicit; writes are atomic and validated. |
| `home` | no canonical replacement | compatibility-only | New code uses `Path.home()` or an explicit path. |
| `pwd` | no canonical replacement | compatibility-only | New code uses `Path.cwd()` or an explicit path. |
| `pwd_main` | no canonical replacement | compatibility-only | New code owns its path explicitly. |
| `pwd_move` | no canonical replacement | deprecated adapter | The reform does not offer a working-directory mutation helper; the adapter warns or becomes a documented no-op. |
| `hello_world` | documentation example | docs-only | It is not part of the canonical scientific plotting API. |
| `__version__` | `__version__` | canonical compatibility attribute | The value comes from installed distribution metadata with a safe source-tree fallback. |
| `__commit__` | `build_info().commit` | deprecating adapter | The canonical build value is typed metadata; `commit` is `None` after cutover unless explicitly supplied by a build system. |

### Lazy-only compatibility entries

The lazy manifest also contains entries that are not part of root `__all__`
or normal interactive discovery:

| Name | Classification | Contract |
| --- | --- | --- |
| `Config` | shadowed legacy fallback | Canonical resolution wins; the legacy target remains inventoried so a boundary rewrite cannot silently change precedence. |
| `save_metadata` | rejecting deprecation adapter | Warns and directs callers to explicit `write_meta`; it never performs implicit metadata collection. |
| `logger` | compatibility-only module value | Retained for safe historical import lookup only; new code uses standard-library logging and gsplot does not configure logging on import. |

## Current canonical root manifest

The implemented 0.4 root exports the following functions. The concise names
listed above are added by their linked Issue #183 slices; this list must not be
read as evidence that an unmerged target already exists.

```text
subplots  inset_axes  line  scatter  cmap_line  cmap_dash  cmap_scatter
sample_cmap  style_axes  title  suptitle  minor_ticks  box_aspect
panel_labels  fig_facecolor  legend  legends  legend_entries  cmap_legend
set_theme  savefig  show  load_config  read_array  write_meta  build_info
use_backend
```

It also exports the following typed values and errors:

```text
Config  AxisSpec  Theme  InsetSpec  MetadataSnapshot  BuildInfo
LegendEntries  GsplotError  ConfigError  DataError  LayoutError  PlotError
OutputError  MetadataError
```

The stable aliases and protocols are `MosaicSpec`, `NormalizeSpec`, and
`ColorSpec`. The canonical package advertises `py.typed` and uses NumPy-style
docstrings for every public function and class.

## Historical module migration

The following module and symbol pages were part of the pre-cutover API
reference. During the compatibility window they are forwarding-only shims to
the canonical root implementation. Their old signatures may be accepted only
at the adapter boundary; new implementation code must not import them.

| Historical path | Target area |
| --- | --- |
| `gsplot.hello_world.hello_world` | documentation example |
| `gsplot.plot.line` | `gsplot.line` |
| `gsplot.plot.line_colormap_solid` | `gsplot.cmap_line` |
| `gsplot.plot.line_colormap_dashed` | `gsplot.cmap_dash` |
| `gsplot.plot.scatter` | `gsplot.scatter` |
| `gsplot.plot.scatter_colormap` | `gsplot.cmap_scatter` |
| `gsplot.config.config` | `gsplot.Config`, `gsplot.load_config` |
| `gsplot.figure.show` | `gsplot.savefig`, `gsplot.show` |
| `gsplot.figure.figure_tools` | `gsplot.build_info`, `gsplot.use_backend` |
| `gsplot.figure.axes` | `gsplot.subplots` |
| `gsplot.figure.axes_inset` | `gsplot.inset_axes` |
| `gsplot.color.colormap` | `gsplot.sample_cmap` |
| `gsplot.path.path` | path compatibility helpers only |
| `gsplot.style.ticks` | `gsplot.minor_ticks` |
| `gsplot.style.graph` | `gsplot.box_aspect`, `gsplot.set_theme`, `gsplot.fig_facecolor` |
| `gsplot.style.legend` | `gsplot.legend`, `gsplot.legends`, `gsplot.legend_entries` |
| `gsplot.style.legend_colormap` | `gsplot.cmap_legend` |
| `gsplot.style.label` | `gsplot.style_axes`, `gsplot.panel_labels` |
| `gsplot.style.title` | `gsplot.title`, `gsplot.suptitle` |
| `gsplot.data.load_file` | `gsplot.read_array` |

The complete current inventory can be regenerated with:

```bash
poetry run python tools/maintenance/collect_public_api.py
```

That command is intentionally read-only and prints JSON to standard output;
it does not create an inventory file or alter the working tree. Its output
separates root `__all__`, lazy canonical targets, lazy legacy targets,
discoverable legacy names, direct metadata attributes, and compatibility paths
parsed from this page. This makes hidden lazy names such as `save_metadata` and
`logger` reviewable without promoting them into the concise API.
