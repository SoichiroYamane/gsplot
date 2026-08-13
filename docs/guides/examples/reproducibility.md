# Reproducibility metadata

Reproducibility is explicit: retain the input data, configuration, source
revision, and backend used for a Figure. `gsplot.build_info()` returns bounded
package metadata without writing a file during import.

```python
import gsplot as gs

snapshot = gs.MetadataSnapshot(
    package_version=gs.build_info().version,
    commit=gs.build_info().commit,
    labels={"experiment": "example"},
)
gs.write_meta(snapshot, "results/figure.json", create_parent=True)
```

The JSON output is stable, size-bounded, and written atomically. Metadata
destinations are caller-owned; gsplot does not create hidden `.gsplot`
directories or user log files.
