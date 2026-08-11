# Getting started

## Install

`gsplot` supports Python 3.10 and newer. Install it from PyPI with:

```bash
python -m pip install gsplot
```

## Verify the installation

Create `hello_gsplot.py`:

```{literalinclude} ../../../demo/0_hello_world/hello_world.py
```

Run it:

```bash
python hello_gsplot.py
```

The command prints the installed `gsplot` version, its recorded commit hash,
and the package logo. The version and commit are read from the installation,
so the values will differ between releases and source checkouts.

## Create a first figure

```python
import gsplot as gs

axes = gs.axes(size=(6, 4), mosaic="A", store=True)
gs.line(axes[0], [0, 1, 2, 3], [0, 1, 4, 9], label="y = x²")
gs.legend(axes[0])
gs.show("first_figure", show=False)
```

This creates a normal Matplotlib figure and saves `first_figure.png` because
`store=True` enables figure storage. Set `show=True` when an interactive
backend is available and the figure should also be displayed.

Continue with the [demonstrations](../demo/index.md) to learn about layouts,
configuration, styling, compatibility, and reproducibility.
