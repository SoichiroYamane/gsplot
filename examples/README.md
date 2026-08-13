# gsplot examples

These examples are executable documentation for the public `gsplot` API. Run
an individual script from its own directory, or validate and rebuild every
declared output from the repository root:

```bash
MPLBACKEND=Agg poetry run python -m tools.maintenance.build_example_images
```

`manifest.json` is the source of truth for executable scripts, documentation
pages, and generated PNG/PDF files. Generated figures are ignored build
products and must not be committed. The shared builder runs each script in a
fresh isolated Python process with temporary user and Matplotlib directories.

The semantic groups are:

- `layouts/`: figure mosaics and Matplotlib interoperability;
- `plotting/`: lines, labels, scatter plots, and colormapped lines;
- `configuration/`: explicit immutable JSON configuration;
- `publication/`: the complete concise publication figure and its data;
- `themes/`: explicit figure-local theme changes;
- `paths/`: explicit path and metadata behavior; and
- `compatibility/`: the intentionally deprecated 0.x API surface.

## Source-path migration

| Previous path | Current path |
| --- | --- |
| `demo/1_axes/axes.py` | `examples/layouts/mosaic.py` |
| `demo/10_subplots/subplots.py` | `examples/layouts/matplotlib_interoperability.py` |
| `demo/2_line_and_label/line_and_label.py` | `examples/plotting/lines_and_labels.py` |
| `demo/5_scatter/scatter.py` | `examples/plotting/scatter.py` |
| `demo/6_line_colormap/line_colormap.py` | `examples/plotting/colored_lines.py` |
| `demo/3_config/config.py` | `examples/configuration/configuration.py` |
| `demo/4_paper_plot/paper_plot.py` | `examples/publication/publication.py` |
| `demo/7_graph_white/graph_white.py` | `examples/themes/white.py` |
| `demo/8_graph_transparent/graph_transparent.py` | `examples/themes/transparent.py` |
| `demo/11_directory/directory.py` | `examples/paths/explicit_paths.py` |
| `demo/9_compatibility/compatibility.py` | `examples/compatibility/legacy_v0.py` |

The numbered documentation URLs remain available as redirects. Historical
benchmark paths pinned to tags or commits remain unchanged.
