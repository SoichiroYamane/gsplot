# Structural reform baseline

This page records the reviewed Phase 0 characterization of the pre-reform
implementation. It is intentionally limited to public-safe, reproducible
facts. It is not a progress diary and it does not preserve raw terminal
output.

## Snapshot

The baseline was measured from the clean `main` revision used to start the
Issue #165 reform branch. The current package is the flat-layout 0.3.x
implementation with `gsplot/` at the repository root, `setup.py`, and a
generated-version workflow. The exact public root names and signatures are
available from `collect_public_api.py`; the reviewed mapping is in the
[API migration matrix](api-migration.md).

The repository contained:

- 30 Python source files under the package directory;
- 11 Python test files;
- 13 demo scripts in the numbered demo tree; and
- 96 top-level function or class definitions found by the Phase 0 inventory.

These counts are orientation data, not acceptance thresholds. The reform
must measure behavior and public contracts rather than optimize for file
counts.

## Validation baseline

The following checks were run in the locked development environment:

| Check | Result |
| --- | --- |
| `MPLBACKEND=Agg poetry run pytest -q` | 27 passed |
| `poetry run black --check gsplot tests scripts docs/conf.py` | passed; 74 files unchanged |
| `poetry run isort --check-only --profile black gsplot tests scripts docs/conf.py` | passed |
| `poetry run mypy --config-file .mypy.ini gsplot` | passed; 30 files checked |
| `poetry run pyright gsplot` | passed; 0 errors and 0 warnings |
| `python -m compileall -q gsplot tests scripts` | passed |
| `poetry run pip-audit --local` | passed; no known vulnerabilities reported |
| `poetry check --lock` | passed; Poetry emitted existing metadata deprecation warnings |
| coverage report | unavailable; `pytest-cov` is not installed in the baseline environment |

The unavailable coverage report is a recorded limitation, not a passing
quality gate. Coverage configuration and the target thresholds belong to the
implementation slices that add the new test layout.

Documentation and package-artifact validation remain required for the
packaging and documentation slices; they are not inferred from the checks
above.

## Documentation/demo output allowlist

The docs build runs every demo in an isolated headless subprocess. The only
files a demo may create or modify are the declared image outputs below; source
data, configuration, and Python files are inputs and must remain unchanged.

| Demo | Allowed outputs |
| --- | --- |
| `0_hello_world`, `11_directory` | none |
| `1_axes` | `axes.png`, `axes.pdf` |
| `2_line_and_label` | `line_and_label.png`, `line_and_label.pdf` |
| `3_config` | `config.png`, `config.pdf` |
| `4_paper_plot`, `test_plot` | `SC_cal.png`, `SC_cal.pdf` |
| `5_scatter` | `scatter.png`, `scatter.pdf` |
| `6_line_colormap` | `line_colormap.png`, `line_colormap.pdf` |
| `7_graph_white` | `graph_white.png`, `graph_white.pdf` |
| `8_graph_transparent` | `graph_transparent.png`, `graph_transparent.pdf` |
| `9_compatibility` | `compatibility.png`, `compatibility.pdf` |
| `10_subplots` | `subplots.png` |

The allowlist is enforced by `docs/conf.py`; an unexpected created or modified
file fails the Sphinx build. Demo subprocesses run with bytecode generation
disabled, and the compatibility demo's non-interactive display warning is
expected under the Agg backend.

## Reform validation snapshot

The canonical implementation now reports 85.99 percent coverage across the
`_core`, `_config`, `_figure`, `_plot`, `_style`, and `_io` modules, while the
pure `_core` modules report 98.67 percent. These are enforced as CI minimums
of 85 percent and 95 percent respectively; historical compatibility modules
remain covered by their characterization tests but are not part of the
canonical implementation threshold.

The reform benchmark uses 30 warmed iterations and closes each temporary
Figure. Its recorded medians are approximately 45.65 ms for a fresh import,
2.68 ms for an ordinary line, 2.93 ms for an ordinary scatter, and 3.20 ms
for a colored line. The memory-retention integration test creates and closes
repeated Figures and confirms that the canonical package owns no Figure/Axes
registry or cache. Values are environment-dependent reference points, not
machine-specific performance promises.

## Import and state characterization

An isolated-process probe observed the following behavior when importing the
current package:

- `matplotlib.pyplot` is imported eagerly;
- several Matplotlib `rcParams`, including the x and y margins, are modified
  during import;
- the probe did not observe a backend change when `MPLBACKEND=Agg` was set;
- importing can create project logging/configuration output and Matplotlib or
  font caches in the user cache/config locations; and
- no figure existed immediately after the import probe.

The reform target removes application file writes, eager pyplot import,
implicit configuration loading, root-logger setup, backend selection, and
`rcParams` mutation from ordinary package import. These are explicit
acceptance items, not assumptions about the current implementation.

## Performance reference points

The same isolated probes produced these reference points:

- fresh-process `import gsplot`: median approximately 546 ms across 30
  samples;
- warmed ordinary `line` plotting call: median approximately 0.596 ms across
  30 calls, with each temporary figure closed after the call.

These numbers are environment-dependent and are used only as relative
references. Final performance validation must use the reform benchmark
protocol: 30 warmed iterations, separate ordinary and colored plotting
cases, and a documented Python/Matplotlib environment without publishing
machine-specific paths or identifying details.

## Phase 0 acceptance

Phase 0 is complete when the following remain true in its merged PR:

1. every current root export has a canonical target or an explicit
   compatibility-only classification;
2. every documented pre-cutover module page has a forwarding-shim decision;
3. the public requirements record the target ownership, configuration,
   dependency, packaging, and compatibility decisions;
4. the inventory command is read-only and reproducible; and
5. the baseline checks and unavailable checks are recorded without leaking
   private paths, credentials, or raw environment output.
