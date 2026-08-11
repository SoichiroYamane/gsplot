# 9. Compatibility

This is the one demo that intentionally exercises the deprecated 0.x root
surface. It is retained to validate the forwarding adapters during the 0.4.x
and 1.x compatibility window. New code should follow demos 1–8 and use the
explicit canonical API.

`gsplot` works with ordinary [Matplotlib](https://matplotlib.org/) figures and
axes. The following example mixes gsplot helpers with `Axes.plot`,
`Axes.scatter`, `plt.sca`, and `plt.plot`.

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
