# Use gsplot in a REPL

The Python REPL is useful for quick data exploration and interactive figures.
`gsplot` returns normal Matplotlib `Figure`, `Axes`, and artist objects.

To avoid opening multiple windows during repeated interactive execution, pass
`live=True` to `gs.subplots(...)`. This automatically reuses and clears the active
canvas for seamless iteration:

```python
import gsplot as gs

fig, ax = gs.subplots("AB", live=True)
gs.line(ax["A"], [0, 1, 2], [0, 1, 4])
gs.label(ax, "x", "y")
```

For final export, omit `live=True` and call `gs.save(...)`:

```python
gs.save(fig, "repl-figure")
```

For a backend that must be selected explicitly, call `gs.use_backend(...)`
before importing `matplotlib.pyplot` or creating a managed Figure. In many
interactive environments, setting `MPLBACKEND` before starting Python is the
simplest option.

