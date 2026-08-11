<div align="center">
  <img src="docs/_static/logo/logo_title_gsplot.png" alt="gsplot logo" width="300">
</div>

[![Documentation](https://github.com/SoichiroYamane/gsplot/actions/workflows/gh-pages-sphinx.yml/badge.svg)](https://soichiroyamane.github.io/gsplot/stable/)
[![PyPI](https://img.shields.io/pypi/v/gsplot)](https://pypi.org/project/gsplot/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

# gsplot

`gsplot` is a small scientific-plotting toolkit built on Matplotlib. It adds
explicit figure layouts, consistent styling helpers, validated JSON defaults,
and lightweight build metadata while keeping ordinary Matplotlib `Figure`
and `Axes` objects in the workflow.

The package is still evolving. Check the [documentation](https://soichiroyamane.github.io/gsplot/stable/)
and the [issue tracker](https://github.com/SoichiroYamane/gsplot/issues) before
depending on behavior that is not covered by the public API.

## Install

`gsplot` supports Python 3.10 and newer:

```bash
python -m pip install gsplot
```

## Quick example

```python
import gsplot as gs

fig, axes = gs.subplots(figsize=(8, 4), mosaic="AB")
gs.line(axes["A"], [0, 1, 2], [0, 1, 4], props={"label": "quadratic"})
gs.scatter(axes["B"], [0, 1, 2], [0, 1, 4], props={"label": "samples"})
gs.legends(fig)
gs.savefig(fig, "quickstart", show=False)
```

This creates a two-panel Matplotlib figure, saves `quickstart.png` when
requested, and remains compatible with regular Matplotlib operations:

The canonical helpers always receive their Figure or Axes target explicitly.
`savefig` displays the Figure after successful writes by default; pass
`show=False` for batch or headless output.

For a complete scientific example, see the
[paper-plot demo](https://soichiroyamane.github.io/gsplot/stable/guides/demo/4_paper_plot.html).

## Configuration

Place a `gsplot.json` file in the working directory, or in
`~/.config/gsplot/gsplot.json`, to provide defaults for supported functions.
The first matching location is used. A path can also be loaded explicitly:

```python
import gsplot as gs

config = gs.load_config("path/to/gsplot.json")
fig, axes = gs.subplots(config=config)
```

When a value is specified more than once, the precedence is:

1. an argument passed directly to the function;
2. the corresponding function entry in `gsplot.json`;
3. the function's default value.

See the [configuration guide](https://soichiroyamane.github.io/gsplot/stable/guides/demo/3_config.html)
for the supported schema and backend notes. Configuration is immutable and is
never discovered or applied by a plain `import gsplot`.

## Development

The repository uses Poetry and targets Python 3.10 or newer. With a compatible
Python interpreter:

```bash
python -m pip install "poetry==2.4.1"
poetry install
MPLBACKEND=Agg poetry run pytest -q
MPLBACKEND=Agg poetry run sphinx-build -W -b html docs docs/_build/html
```

The demos under `demo/` are executable documentation. Run one from its own
directory, for example:

```bash
cd demo/1_axes && python axes.py
```

`demo/9_compatibility` intentionally demonstrates the deprecated 0.x surface.
All other plotting demos use the canonical explicit-target API.

See [the developer setup guide](docs/reference/contribution/developer_env.md)
for formatting, type checking, packaging, and Docker instructions.

For private vulnerability reports and the supported-version policy, see
[SECURITY.md](SECURITY.md).

## Authors

This repository was forked from code developed by Giordano Mattoni.

- Giordano Mattoni
- Soichiro Yamane

## License

This project is distributed under the [MIT License](LICENSE).
