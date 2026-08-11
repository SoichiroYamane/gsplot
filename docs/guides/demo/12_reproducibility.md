# 12. Reproducibility

Reproducibility has two parts: record which `gsplot` revision produced a
figure, and preserve the configuration used to create it. The package records
the first part automatically and can record the second part when metadata is
enabled.

## Package log

Importing `gsplot` updates:

```text
~/.config/gsplot/gsplot_log.yml
```

The YAML file groups observed package versions and records the corresponding
commit hash and timestamp. It is a local history, not a replacement for a
dependency lockfile or source archive. To reproduce a result exactly, keep the
same Python dependencies (for example with `poetry.lock`), input data, source
code, and Matplotlib backend as well.

A typical entry looks like this:

```yaml
versions:
  - version: 0.2.0
    commits:
      - commit: 1d0c220a25e2ec79eea0d73212d4631524f25150
        date: "2025-01-01 12:00:00"
```

The values above are illustrative; use the values written by the installed
package as the authoritative record.

## Per-script metadata

Set `metadata` to `true` in `gsplot.json`:

```json
{
  "metadata": true
}
```

When a script is executed, `gsplot` writes the following files next to the
executed main file:

```text
project/
├── main.py
└── .gsplot/
    ├── metadata.yml
    ├── config.json
    └── history/
        └── history.txt
```

- `metadata.yml` contains the date, package version, and commit hash.
- `config.json` contains the complete loaded configuration.
- `history/history.txt` contains one JSON record whenever the metadata or
  configuration changes.

The `.gsplot/` directory is ignored by this repository because it contains
run-specific output. Copy it into an experiment archive when it is part of the
record you need to preserve.
