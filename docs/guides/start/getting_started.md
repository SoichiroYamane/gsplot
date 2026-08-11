# Getting started

## Install

`gsplot` supports Python 3.10 and newer. Install it from PyPI with:

```bash
python -m pip install gsplot
```

## Verify the installation

```python
import gsplot as gs

print(gs.build_info())
```

## Create a first figure

```python
import gsplot as gs

fig, ax = gs.subplots(figsize=(6, 4))
gs.line(ax, [0, 1, 2, 3], [0, 1, 4, 9], props={"label": "y = x²"})
gs.legend(ax)
gs.savefig(fig, "first_figure", show=False)
```

This creates a normal Matplotlib figure and saves `first_figure.png`. The
canonical `savefig` operation defaults to `show=True`; pass `show=False` for
batch or headless output.

Continue with the [demonstrations](../demo/index.md) to learn about layouts,
configuration, styling, compatibility, and reproducibility.
