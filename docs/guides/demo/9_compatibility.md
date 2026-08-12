# 9. Compatibility

This is the one demo that intentionally exercises the deprecated 0.x root
surface. It is retained to validate the forwarding adapters during the 0.4.x
and 1.x compatibility window. New code should follow demos 1–8 and use the
explicit canonical API.

`gsplot` works with ordinary [Matplotlib](https://matplotlib.org/) figures and
axes. The following example mixes gsplot helpers with `Axes.plot`,
`Axes.scatter`, `plt.sca`, and `plt.plot`.

During the compatibility window, `gs.axes()` keeps its historical 5-by-5 inch
single-panel default, tight layout, and `store` flag. Option-free root
`gs.line()` and `gs.scatter()` calls keep the historical viridis automatic
color sequence. Legacy `gs.show()` writes its default PNG and PDF only when
the legacy store flag is enabled. New code should use `gs.subplots()`,
explicit `props` or `Config` values, and `gs.savefig(fig, ...)` instead.

## Example

### Code

```{literalinclude} ../../../demo/9_compatibility/compatibility.py
```

### Plot

```{image} ../../../demo/9_compatibility/compatibility.png
:alt: compatibility
:class: bg-primary
:width: 1000px
:align: center
```
