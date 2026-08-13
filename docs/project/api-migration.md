# API migration matrix

This page is the cumulative migration matrix for the structural reform tracked
in [Issue #165](https://github.com/SoichiroYamane/gsplot/issues/165) and the
concise publication API tracked in
[Issue #183](https://github.com/SoichiroYamane/gsplot/issues/183). It maps the
historical 0.3 API, the pre-concise 0.4 baseline, and the currently implemented
concise contract that is intended to stabilize through 1.x. The runtime,
generated API index, and inventory command remain the authority for merged
behavior; unmerged roadmap work is not described as available.

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
- A documented historical module's declared functions resolve to the same
  reviewed adapters as the root names. Compatibility-only implementation
  classes may remain reachable from their historical modules, but they are not
  canonical exports and cannot replace the root adapter for a documented
  function.

## Effective default-value matrix

Signature compatibility alone is not sufficient for plotting APIs. The
following matrix records the effective defaults during the compatibility
window.

| Surface | Historical 0.3 | Pre-concise 0.4 baseline | Current 0.4 / 1.x contract |
| --- | --- | --- | --- |
| Figure size | 5 x 5 in | Matplotlib default unless explicit | `auto`: 85 mm for one column, 170 mm for multiple columns; tuple/preset override |
| Layout | tight | none unless explicit | constrained for a new Figure; preserve a reused Figure |
| Reused-Figure clearing | true | false | false |
| Style ownership | process-global import/config effects | ambient or explicit target helpers | target-local `paper` on newly created Axes |
| Line defaults | marker `o`, size 7, edge width 1.5, `--`, width 1, alpha 1, face alpha 0.2 | preserved by the root helper | preserved by concise `line` |
| Scatter defaults | marker `o`, size 1, alpha 1 | preserved by the root helper | preserved by concise `scatter` |
| Option-free color | historical shared viridis sequence | compatibility-dependent root sequence | target Axes cycle; pure `series=n` when requested |
| Labels | minor ticks, 5 pt pad, incidental relayout | concise `label` plus advanced `AxisSpec` | minor ticks and 5 pt pad, no Figure relayout |
| Panel indexes | lowercase labels positioned from rendered bounds | concise `index` plus advanced `panel_labels` | lowercase bijective labels; outside aligns to the y-label left edge with a 6-point top gap |
| Legend | ambient/config placement (`best` without config; demos often used `lower left`), globally frameless/non-fancy with spacing 0.3 | explicit options with conservative replacement | explicit `best`, frameless, non-fancy, spacing 0.3; conservative replacement |
| Inset zoom | two explicit connector corner pairs | advanced placement only | automatic or exact two-pair connectors; indicator defaults 0.01 below child z-order 5 |
| Text read | comma delimiter, unpacked columns | explicit options mapping; structured unpack was coerced | comma delimiter and unpack true; native structured field arrays preserved |
| Save | PNG+PDF, 600 DPI, tight crop, show, overwrite | conservative `savefig`; suffix-free path selected PNG | transactional `save` restores the historical flow; `savefig` remains conservative |
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

## Implemented concise root migration

The implemented primary concise surface is:

```text
subplots  inset  line  scatter  colors  label  index  square
legend  paper  save  show  read
```

| Current 0.4 surface | Concise target | 1.x classification and contract |
| --- | --- | --- |
| `subplots` | `subplots` | additive shape, auto-size, layout, style, and schema-2 support; native return retained |
| `inset_axes` | `inset` | concise tuple/`InsetSpec` placement, paper style, optional label, automatic or exact-pair zoom, and explicit layering; placement-only advanced function retained |
| `line`, `scatter` | same names | additive direct finite options, multi-target preflight, and deterministic `series` |
| `sample_cmap` | `colors` | concise inclusive sampler with midpoint for one color; advanced value normalization API retained |
| `style_axes` | `label` | new concise records/shared-value operation; typed advanced API retained |
| `box_aspect` | `square` | concise finite-aspect spelling; advanced helper retained |
| `panel_labels` | `index` | concise lowercase labels with DPI-aware inside clearance and y-label-aligned outside placement; advanced helper retained |
| `legend` | `legend` | additive direct finite paper defaults and multi-target semantics |
| `legends`, `legend_entries`, `cmap_legend` | unchanged advanced APIs | retained through 1.x |
| `set_theme`, `fig_facecolor` | `paper` plus unchanged advanced APIs | `paper` owns the publication baseline; other themes remain explicit |
| `title`, `suptitle`, `minor_ticks` | unchanged advanced APIs | retained; concise `label` covers common axis styling only |
| `savefig` | `save` | concise transactional historical workflow added; conservative advanced API retained |
| `show` | `show` | display-only ownership retained and generalized to same-Figure Axes targets |
| `read_array` | `read` | CSV and unpack defaults plus finite common NumPy options; native ndarray-or-field-list result and options-mapping API retained |
| `load_config` | `load_config` | explicit loading retained; schema 2 becomes canonical |
| `write_meta`, `build_info`, `use_backend` | unchanged advanced APIs | retained through 1.x |
| `cmap_line`, `cmap_dash`, `cmap_scatter` | unchanged advanced APIs | retained through 1.x |

### Public boundary inventory

The compatibility audit freezes the following finite surfaces. Counts are
acceptance checks, not a substitute for reviewing the names in the JSON
inventory.

| Boundary | Count | Source and enforcement |
| --- | ---: | --- |
| Canonical root `__all__` | 67 | Must equal the lazy canonical manifest, static canonical exports, and canonical autosummary index. |
| Historical v0.3 root `__all__` | 41 | Frozen from tag `v0.3.0`; must equal the discoverable legacy root list. |
| Historical direct root attributes outside `__all__` | 5 | `Config`, `logger`, `save_metadata`, `__commit__`, and `__version__`. |
| Lazy legacy manifest | 44 | The 41 historical discoverable names plus shadowed `Config`, `logger`, and `save_metadata`. |
| Direct metadata attributes | 2 | `__commit__` and `__version__`; neither is a lazy function export. |
| Documented historical modules | 20 | Frozen module paths and each module's ordered `__all__` from the v0.3 API reference. |

Every canonical function has a finite annotated runtime signature, an
annotated return, no visible omission sentinel, and no `**kwargs` in the
primary introspection view. The overlapping `line`, `scatter`, `label`,
`legend`, `title`, and `show` adapters also have finite implementation binders;
their concise signatures cannot conceal a generic compatibility keyword bag.
Type aliases are inventoried as type aliases rather than misleading callable
signatures. The generated root API pages are the detailed signature and return
reference; the tables on this page classify every changed or retained surface.

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
`SizeSpec`, `LayoutMode`, `StyleMode`, and `ZoomCorners` are additive and remain
valid on Python 3.10.

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
| `axes_inset` | `inset` | adapter + explicit ownership | The parent `Axes` is explicit; tuple bounds, labels, zoom corner pairs, paper style, and layering use the concise operation. |
| `axes_inset_padding` | `inset` / `inset_axes` | adapter | Advanced width/height placement uses `InsetSpec`; no current-object lookup. |
| `get_figure_size` | `Figure.get_size_inches()` | adapter | New code uses the Matplotlib figure directly; a compatibility helper may preserve the old convenience call. |
| `show` | `save` and `show` | adapter + breaking behavior | `save(target, ..., show=True)` transactionally saves before display. Canonical `show(target)` displays one explicit Figure or same-Figure Axes target and never saves or closes. |
| `get_cmap` | `colors` / `sample_cmap` | adapter + breaking signature | Count sampling uses concise `colors`; value normalization remains in the advanced sampler. |
| `line` | `line` | canonical name retained | One or more explicit same-Figure Axes return a native `list[Line2D]` or target-ordered tuple of lists; the concise view and finite long options use a closed property schema. |
| `line_colormap_solid` | `cmap_line` | adapter + breaking name | The compatibility adapter preserves its one-item list return; canonical `cmap_line` owns colored-segment validation and returns a `LineCollection`. |
| `line_colormap_dashed` | `cmap_dash` | adapter + breaking name | The compatibility adapter preserves its legacy list return; canonical `cmap_dash` returns a tuple of `LineCollection` objects and validates positive dash lengths. |
| `scatter` | `scatter` | canonical name retained | One or more explicit same-Figure Axes return a native `PathCollection` or target-ordered tuple; the concise view and finite long options use a closed property schema. |
| `scatter_colormap` | `cmap_scatter` | adapter + breaking name | The target validates color data and returns a `PathCollection`. |
| `graph_square` | `box_aspect` | adapter + breaking name | Aspect application is explicit and does not inspect a caller frame or global axes store. |
| `graph_square_axes` | `box_aspect` | adapter | The target accepts an explicit `Axes` or typed target collection. |
| `graph_white` | `set_theme` | adapter + breaking name | Theme application is explicit and does not mutate global `rcParams`. |
| `graph_white_axes` | `set_theme` | adapter | The target takes a `Figure` or `Axes` target and a `Theme` value. |
| `graph_transparent` | `set_theme` | adapter + breaking name | Transparency is a named theme value rather than an implicit current-figure operation. |
| `graph_transparent_axes` | `set_theme` | adapter | The target takes an explicit target. |
| `graph_facecolor` | `fig_facecolor` | adapter + breaking name | Figure ownership is explicit. |
| `label` | `label` | adapter + explicit ownership | An Axes target selects concise labels; historical record-only calls retain current-Figure behavior behind one warning. |
| `label_add_index` | `index` | adapter + breaking ownership | Panel targets and placement are explicit; the concise helper returns native `Text` objects. |
| `title` | `title` | adapter + breaking ownership | The canonical call targets an explicit `Axes`; figure-level text uses `suptitle`. |
| `title_axes` | `title` | adapter | The old explicit-Axes spelling forwards to the canonical explicit target form. |
| `legend` | `legend` | canonical rename retained | Handles, labels, handler maps, replacement, and properties are explicit. |
| `legend_axes` | `legends` | adapter + breaking name | The target returns all legends on an explicit target. |
| `legend_handlers` | `legend` | adapter | Handler maps become local call arguments and are never global mutable state. |
| `legend_reverse` | `legend` | adapter | Reversal is an explicit `reverse` option. |
| `legend_get_handlers` | `legend_entries` | adapter + breaking name | The target returns a typed `LegendEntries` value. |
| `legend_colormap` | `cmap_legend` | adapter + breaking name | Colormap legend construction uses explicit handles, labels, and color mapping. |
| `ticks_off` | `minor_ticks` | adapter + breaking name | The target has one explicit `enabled` operation. |
| `ticks_on` | `minor_ticks` | adapter + breaking name | The target has one explicit `enabled` operation. |
| `ticks_on_axes` | `minor_ticks` | adapter | The target accepts explicit axes and an axis selector. |
| `load_file` | `read` / `read_array` | adapter + breaking name | Concise CSV loading has finite direct options; advanced options remain explicit and neither path changes the working directory. |
| `load_file_fast` | `read(loader="loadtxt")` | adapter | The loader choice is explicit rather than encoded in a second public function. |
| `config_load` | `load_config` | adapter + breaking name | Loading is explicit and returns an immutable `Config`. Importing the package does not load files. |
| `config_dict` | `Config` | adapter + breaking ownership | Configuration is a typed immutable value, not a mutable process-wide dictionary. |
| `config_entry_option` | `Config.get` / `Config.section` | adapter | Accessors validate the schema and do not expose mutable global state. |
| `save_metadata` | `write_meta` | rejecting adapter + breaking ownership | It warns and raises `MetadataError`; metadata destination and snapshot must be explicit and writes are atomic and validated. |
| `home` | no canonical replacement | compatibility-only | New code uses `Path.home()` or an explicit path. |
| `pwd` | no canonical replacement | compatibility-only | New code uses `Path.cwd()` or an explicit path. |
| `pwd_main` | no canonical replacement | compatibility-only | New code owns its path explicitly. |
| `pwd_move` | no canonical replacement | deprecated adapter | The compatibility call warns and is a no-op; the reform does not mutate the working directory. |
| `hello_world` | documentation example | docs-only adapter | The retained call warns and is a no-op; it is not part of the canonical scientific plotting API. |
| `__version__` | `__version__` | canonical compatibility attribute | The value comes from installed distribution metadata with a safe source-tree fallback. |
| `__commit__` | `build_info().commit` | deprecating adapter | The canonical build value is typed metadata; `commit` is `None` after cutover unless explicitly supplied by a build system. |

### Lazy-only compatibility entries

The lazy manifest also contains entries that are not part of root `__all__`
or normal interactive discovery:

| Name | Classification | Contract |
| --- | --- | --- |
| `Config` | shadowed legacy fallback | Canonical resolution wins; the legacy target remains inventoried so a boundary rewrite cannot silently change precedence. |
| `save_metadata` | rejecting deprecation adapter | Warns and directs callers to explicit `write_meta`; it never performs implicit metadata collection. |
| `logger` | side-effect-free no-op adapter | The root and historical module call warn and return `None`; they never recreate the removed application log. New code configures standard-library logging explicitly. |

## Current canonical root manifest

The implemented 0.4 root exports the following functions:

```text
subplots  inset  inset_axes  line  scatter  cmap_line  cmap_dash  cmap_scatter
colors  sample_cmap  label  square  index  style_axes  title  suptitle  minor_ticks
box_aspect  panel_labels  fig_facecolor  legend  legends  legend_entries
cmap_legend  set_theme  save  savefig  show  load_config  read  read_array  write_meta
build_info  use_backend
```

It also exports the following typed values and errors:

```text
Config  AxisSpec  Theme  InsetSpec  MetadataSnapshot  BuildInfo
LegendEntries  GsplotError  ConfigError  DataError  LayoutError  PlotError
OutputError  MetadataError
```

The stable aliases and protocols are `MosaicSpec`, `NormalizeSpec`,
`ColorSpec`, `AxesTarget`, `PerTarget`, `LineStyle`, `Marker`, `Unit`,
`SizePreset`, `SizeSpec`, `LayoutMode`, `StyleMode`, `ZoomCorners`, `Limit`,
`Scale`, `TickSpec`, `LabelRecord`, and `LabelRecords`. The canonical package
advertises `py.typed` and uses NumPy-style docstrings for every public function
and class.

## Historical module migration

The following module and symbol pages were part of the pre-cutover API
reference. During the compatibility window their declared functions are
forwarding-only shims to the same reviewed root adapters. Their old signatures
may be accepted only at that adapter boundary; compatibility-only classes may
remain available as fallback attributes, and new implementation code must not
import either form.

| Historical path | Target area |
| --- | --- |
| `gsplot.hello_world.hello_world` | documentation example |
| `gsplot.plot.line` | `gsplot.line` |
| `gsplot.plot.line_colormap_solid` | `gsplot.cmap_line` |
| `gsplot.plot.line_colormap_dashed` | `gsplot.cmap_dash` |
| `gsplot.plot.scatter` | `gsplot.scatter` |
| `gsplot.plot.scatter_colormap` | `gsplot.cmap_scatter` |
| `gsplot.config.config` | `gsplot.Config`, `gsplot.load_config` |
| `gsplot.figure.show` | `gsplot.save`, advanced `gsplot.savefig`, or `gsplot.show` |
| `gsplot.figure.figure_tools` | `gsplot.build_info`, `gsplot.use_backend` |
| `gsplot.figure.axes` | `gsplot.subplots` |
| `gsplot.figure.axes_inset` | `gsplot.inset` or advanced `gsplot.inset_axes` |
| `gsplot.color.colormap` | `gsplot.colors` or advanced `gsplot.sample_cmap` |
| `gsplot.path.path` | path compatibility helpers only |
| `gsplot.style.ticks` | `gsplot.minor_ticks` |
| `gsplot.style.graph` | `gsplot.box_aspect`, `gsplot.set_theme`, `gsplot.fig_facecolor` |
| `gsplot.style.legend` | `gsplot.legend`, `gsplot.legends`, `gsplot.legend_entries` |
| `gsplot.style.legend_colormap` | `gsplot.cmap_legend` |
| `gsplot.style.label` | `gsplot.label`, `gsplot.index`, advanced `gsplot.style_axes` and `gsplot.panel_labels` |
| `gsplot.style.title` | `gsplot.title`, `gsplot.suptitle` |
| `gsplot.data.load_file` | `gsplot.read` or advanced `gsplot.read_array` |

The complete current inventory can be regenerated with:

```bash
poetry run python tools/maintenance/collect_public_api.py
```

That command is intentionally read-only and prints JSON to standard output;
it does not create an inventory file or alter the working tree. Its output
separates root `__all__`, lazy canonical targets, lazy legacy targets,
type-checker exports, API-index exports, typed kinds and signatures, direct
metadata attributes, structured parameter/default/annotation contracts,
docstring summaries and fingerprints, the frozen v0.3 baseline, and the actual
exports of every compatibility path parsed from this page. This makes hidden
lazy names such as `save_metadata` and `logger` reviewable without promoting
them into the concise API.

### Warning and exception migration

Valid canonical calls emit no compatibility warning. Importing a historical
module emits `DeprecationWarning`; a documented function from that module then
uses the same finite adapter as its root spelling. A legacy call form emits a
caller-facing `DeprecationWarning`, while ambiguous or mixed canonical/legacy
forms fail before current-Figure or compatibility state is consulted.
Type/binding ambiguity raises `TypeError` or `OptionError`; validated domain
failures use `ConfigError`, `DataError`, `LayoutError`, `PlotError`,
`OutputError`, or `MetadataError` as documented by the canonical operation.
The special `save_metadata` adapter warns and raises `MetadataError`; `logger`,
`hello_world`, and `pwd_move` warn and return without their removed side
effects.
