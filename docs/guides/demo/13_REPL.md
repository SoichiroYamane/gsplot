# 13. Use gsplot in a REPL

The Python REPL is useful for quick data exploration and interactive figures.
`gsplot` returns normal Matplotlib `Figure`, `Axes`, and artist objects.

```pycon
>>> import gsplot as gs
>>> fig, ax = gs.subplots(mosaic="A")
>>> gs.line(ax, [0, 1, 2], [0, 1, 4])
>>> gs.savefig(fig, "repl-figure", show=True)
```

For a backend that must be selected explicitly, call `gs.use_backend(...)`
before importing `matplotlib.pyplot` or creating a managed Figure. In many
interactive environments, setting `MPLBACKEND` before starting Python is the
simplest option.
