# API migration matrix

This page is the reviewed migration matrix for the structural reform tracked
in [Issue #165](https://github.com/SoichiroYamane/gsplot/issues/165). It maps
the canonical implementation to the 0.3.x compatibility baseline and is the
starting point for downstream migration work.

## Compatibility policy

- The canonical API is available from `import gsplot as gs`.
- The reform targets the 0.4.x compatibility line and the 1.x stabilization
  line. Legacy root calls and documented legacy module imports remain
  forwarding-only adapters throughout those lines.
- Candidate removal of legacy adapters is a separate decision for a future
  major release, no earlier than 2.0, after downstream usage has been
  audited.
- The old `gsplot.base.*` implementation namespace is not a supported public
  compatibility surface unless it was part of the pre-cutover API reference.
- A compatibility adapter may normalize old arguments, but canonical modules
 must never import the compatibility layer or contain duplicate algorithms.

## Effective default-value matrix

Signature compatibility alone is not sufficient for plotting APIs. The
following matrix records the effective defaults during the compatibility
window.

| Surface | Effective default | Classification |
| --- | --- | --- |
| `gs.subplots()` | One ordinary subplot, Matplotlib figure size, `squeeze=True`, `clear=False`, no layout engine | Canonical breaking replacement for `axes()` |
| `gs.axes()` | `size=(5, 5)`, `unit="in"`, `mosaic="A"`, `clear=True`, tight layout enabled | Compatible legacy adapter |
| Root `gs.line()` and `gs.scatter()` without `props` or `config` | Five-color viridis automatic sequence, matching the 0.3.x compatibility behavior | Compatible root default |
| Canonical line/scatter implementation with explicit `props` or `Config` | Ordinary Matplotlib Axes property cycle unless an explicit color is supplied | Canonical explicit behavior |
| `gs.cmap_line()` | `cmap="viridis"`, `linewidths=1.0` | Canonical explicit default |
| `gs.cmap_dash()` | `cmap="viridis"`, `dash=(10.0, 10.0)`, `linewidths=1.0` | Canonical explicit default |
| `gs.cmap_scatter()` | `cmap="viridis"`, `s=1.0`, `alpha=1.0` | Canonical explicit default |
| Legacy `gs.show()` | `fname="gsplot"`, `ft_list=("png", "pdf")`, `dpi=600`; files are written only when legacy `store=True` | Compatible adapter |
| `gs.savefig(fig, ...)` | `show=True`; a supplied suffix selects the format, while a suffix-free path defaults to PNG when `formats` is omitted | Canonical explicit lifecycle |
| `gs.show(fig)` | Display only; never saves or closes | Canonical breaking split from legacy `show()` |

The compatibility color sequence and store flag are implemented only at the
root adapter boundary. Canonical implementation modules do not depend on the
historical singleton state. Removing import-time Matplotlib `rcParams` mutation
is also intentional; ambient Matplotlib defaults now apply unless an
application configures them explicitly.

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

## Canonical root manifest

The reformed root exports the following functions:

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

The exact 0.3.x root export names and signatures can be regenerated with:

```bash
poetry run python tools/maintenance/collect_public_api.py
```

That command is intentionally read-only and prints JSON to standard output;
it does not create an inventory file or alter the working tree.
