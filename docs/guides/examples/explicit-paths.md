# Explicit paths

The canonical API does not change the process working directory or infer a
script path. Use `pathlib.Path` for path inspection and pass output paths to
`gsplot.save` or `gsplot.write_meta` explicitly.

```{literalinclude} ../../../examples/paths/explicit_paths.py
```
