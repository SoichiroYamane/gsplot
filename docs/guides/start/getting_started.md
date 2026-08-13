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

fig, ax = gs.subplots()
gs.line(ax, [0, 1, 2, 3], [0, 1, 4, 9], label="y = x²")
gs.label(ax, "x", "x²", square=True)
gs.legend(ax)
gs.save(fig, "first_figure", show=False)
```

This creates a normal Matplotlib figure and saves `first_figure.png` and
`first_figure.pdf`. Concise `save` defaults to 600 DPI, tight cropping with
0.1-inch padding, transactional replacement, and `show=True`; pass
`show=False` for batch or headless output. Pass `crop=False` when the exported
media box must exactly match the Figure design canvas. Advanced `savefig`
retains its conservative one-format default and `overwrite=False` policy.

`label` keeps the Figure lifecycle explicit: it changes only `ax`, enables
minor ticks with 5-point label padding, and makes the panel square without
executing a Figure layout engine. `legend` uses best placement with no frame,
no rounded box, and compact 0.3 label spacing unless you pass direct options.

Continue with the [publication guide](../publication.md) for sizing and output
decisions, the [advanced guide](../advanced.md) for explicit Matplotlib-level
control, or the [examples](../examples/index.md) for executable recipes.
