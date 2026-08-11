# 13. Use gsplot in a REPL

The Python REPL is useful for quick data exploration and interactive figures.
`gsplot` returns normal Matplotlib `Axes` objects, so the usual Matplotlib and
backend controls remain available.

## Advantages

- inspect data and figures one command at a time;
- adjust labels, limits, and styles interactively;
- use a Matplotlib backend appropriate for the current desktop or notebook.

## Example session

```pycon
>>> import gsplot as gs
>>> axes = gs.axes(mosaic="A", ion=True)
>>> gs.line(axes[0], [0, 1, 2], [0, 1, 4])
>>> gs.show(show=True)
```

The exact interactive behavior depends on the Matplotlib backend and the
terminal or editor hosting the REPL.

## Select a backend

If a backend must be selected through `gsplot.json`, use the singular
`backend` key:

```json
{
  "rcParams": {
    "backend": "QtAgg"
  },
  "axes": {
    "ion": true,
    "clear": true
  },
  "show": {
    "show": true
  }
}
```

Place the file where `gsplot` can discover it before starting the REPL and
before importing `gsplot`. Backend names are platform- and installation-
dependent. On macOS, `MacOSX` may be available; on Linux, a Qt, Tk, GTK, or
non-interactive backend may be more appropriate. You can also set
`MPLBACKEND` in the shell before launching Python.

```bash
MPLBACKEND=QtAgg python
```

The repository includes a short editor demonstration below when the generated
documentation is viewed in a browser:

```{raw} html
<video controls muted loop style="display:block;max-width:80%;margin:1rem auto">
  <source src="../../_static/tutorial/repl_tutorial.mp4" type="video/mp4">
  <p>Your browser does not support embedded video.</p>
</video>
```
