# gsplot Requirements

This document defines the stable repository-level requirements for `gsplot`.
It is a product and engineering contract, not a chronological progress log.
Task-specific scope, decisions, evidence, and blockers belong in the linked
GitHub Issue and PR. Draft status is optional and is reserved for genuinely
incomplete work.

## Product definition

`gsplot` is a small scientific-plotting toolkit built on Matplotlib. It adds
convenient figure layouts, plotting helpers, styling helpers, configurable
defaults, data-loading helpers, and optional reproducibility metadata while
keeping ordinary Matplotlib objects in the workflow.

`gsplot` is not a replacement for Matplotlib. Matplotlib remains the rendering
engine and its `Figure`, `Axes`, artist, backend, and lifecycle behavior are
part of the integration contract.

## Users and primary use cases

The project serves people who need to:

- create reproducible scientific figures with a small Python API;
- combine gsplot helpers with ordinary Matplotlib calls;
- reuse figure layout and styling defaults across scripts through JSON
  configuration;
- load simple numerical text data and immediately plot it;
- generate figures in interactive sessions, scripts, notebooks, and headless
  documentation or CI environments; and
- inspect source examples and API documentation without relying on private
  project knowledge.

## Functional requirements

### FR-1: Public plotting API

The package root must expose the documented canonical functions through
`src/gsplot/__init__.py` and the module-level `__all__` declarations. The
following table records the 0.3.x compatibility baseline; the canonical
replacement is defined in the structural reform target contract below:

| Area | Public capabilities |
| --- | --- |
| Figure and layout | `axes`, `axes_inset`, `axes_inset_padding`, `get_figure_size`, `show` |
| Plotting | `line`, `scatter`, `line_colormap_solid`, `line_colormap_dashed`, `scatter_colormap` |
| Color | `get_cmap`, `legend_colormap` |
| Graph styling | `graph_square`, `graph_square_axes`, `graph_white`, `graph_white_axes`, `graph_transparent`, `graph_transparent_axes`, `graph_facecolor` |
| Labels and annotations | `label`, `label_add_index`, `title`, `title_axes` |
| Legends and ticks | `legend`, `legend_axes`, `legend_handlers`, `legend_reverse`, `legend_get_handlers`, `ticks_off`, `ticks_on`, `ticks_on_axes` |
| Data and paths | `load_file`, `load_file_fast`, `home`, `pwd`, `pwd_move`, `pwd_main` |
| Configuration and metadata | `config_load`, `config_dict`, `config_entry_option`, `hello_world`, `__version__`, `__commit__` |

Adding, moving, renaming, or removing an entry from this surface requires an
API compatibility review, documentation updates, focused tests, and an
explicit compatibility classification.

### FR-2: Figure and layout helpers

- `subplots` must create or reuse ordinary Matplotlib figures and axes while
  supporting validated size, unit, mosaic, clearing, and layout options.
- Layout validation must reject invalid dimensions or mosaics with a clear
  error rather than silently producing an unusable figure.
- `inset_axes` must create Matplotlib-compatible inset axes below an explicit
  parent Axes.
- `savefig` must save an explicit Figure in the requested formats and display
  it only after all successful writes when `show=True`.
- `show` must be display-only and must never save or close a Figure.
- Figure lifecycle behavior must remain explicit. A helper must not close or
  replace a user-owned figure unless that behavior is documented for the
  specific function.

### FR-3: Plotting and data helpers

- Line and scatter helpers must accept normal Matplotlib `Axes` objects and
  return or expose the underlying Matplotlib artists expected by their public
  documentation.
- Colormap helpers must produce deterministic colors for deterministic input
  and must validate the input shape and color-related options.
- Plotting helpers must preserve relevant Matplotlib keyword arguments unless
  gsplot intentionally documents an override.
- `read_array` must provide one explicit boundary for the documented
  `numpy.genfromtxt` and `numpy.loadtxt` behaviors. File paths and path-like
  values must remain usable without changing the working directory.
- Numerical helpers must not silently alter the caller's input arrays.

### FR-4: Styling helpers

Graph, label, title, legend, tick, and colormap-legend helpers must operate on
explicit Figure or Axes targets according to their public documentation. They
must remain composable with direct Matplotlib styling calls and must not
require users to use private gsplot classes.

### FR-5: Matplotlib compatibility

The following compatibility behaviors are required:

- gsplot-created axes must work with `Axes.plot`, `Axes.scatter`, `plt.sca`,
  and normal Matplotlib property methods;
- returned artists, labels, limits, collections, and axis state must remain
  inspectable through Matplotlib APIs;
- gsplot must not force an interactive backend from library code;
- headless callers must be able to set `MPLBACKEND=Agg` and run without a
  display; and
- a gsplot helper must not unexpectedly mutate unrelated figures or axes.

### FR-6: Configuration

Configuration is optional. When used, gsplot must:

- discover `gsplot.json` in the documented order: the current working
  directory, the user configuration directory, then the home directory;
- allow an explicit path through `load_config`;
- expose the loaded immutable value through `Config` accessors;
- resolve values with this precedence:

  1. explicit function arguments;
  2. the supplied immutable `Config` value;
  3. the function signature defaults;

- translate legacy function-entry configuration only inside the compatibility
  facade during the documented migration window;
- avoid mutating caller-owned configuration dictionaries or unrelated
  Matplotlib `rcParams`; and
- apply `rcParams` and backend settings with the documented process-wide
  timing constraints.

The configuration schema and its error behavior must be documented. A change
to a configuration key is a public contract change even when the Python
function signature is unchanged.

### FR-7: Reproducibility and metadata

- Version and build metadata must be available through `__version__` and
  `build_info()`.
- Optional metadata recording through `write_meta()` must use an explicit
  destination and must not run network access or disclose private machine data.
- Reproducibility examples must identify the inputs, configuration, output
  settings, and relevant package metadata needed to understand a generated
  figure.
- Ordinary imports and plotting calls must not create project files,
  credentials, or unbounded logs.

### FR-8: Documentation and examples

- README, guides, API reference pages, demos, and package behavior must agree.
- Demos are executable documentation and must remain runnable from their
  documented working directories.
- Sphinx builds must execute representative demos in a failure-visible,
  headless environment.
- The Sphinx demo-output inventory must declare the exact files each demo is
  expected to generate and must fail when a required artifact is missing or
  unchanged from before the current run. Ignored stale PNG/PDF files must not
  make a documentation build pass.
- The publication demo must explicitly generate its PNG and PDF outputs from
  one Figure with its reviewed publication export settings; generated outputs
  remain build products and are not committed.
- Examples must use public APIs and must not rely on private paths, local
  machine state, or hidden generated files.
- Renamed or removed documentation pages must update all toctrees, links, and
  versioned documentation scripts.

### FR-9: Versioned documentation delivery

The website delivery contract tracked by
[Issue #174](https://github.com/SoichiroYamane/gsplot/issues/174) is stable
repository behavior:

- GitHub's published, non-draft, non-prerelease Releases are the source for
  immutable documentation versions. The initial documentation floor is
  v0.1.1, and v0.3.0 must be deployed first as the stable release.
- `/stable/` is a copied alias of the latest successfully built immutable
  release, `/dev/` is the current `main` documentation with `noindex`, and
  `/vX.Y.Z/` is an immutable release tree. The root is a small, no-JavaScript
  entry page pointing to `/stable/`.
- Version catalogs and switcher data are generated from one typed,
  schema-validated catalog. Drafts, prereleases, malformed tags, duplicate
  versions, stale fallback, and missing release refs fail visibly.
- `docs/project/website-release-policy.json` is the reviewed source for any
  historical exclusion, and each exclusion records its public reason, approval
  date, Issue or PR, and replacement link when available.
- `docs/project/website-compatibility.md` records the pre-cutover route
  inventory and explicit mappings for root, stable, dev, version, `.html`, and
  asset URLs.
- Historical documentation must import its own release source/package in an
  isolated environment. Builds remain warnings-as-errors; the temporary
  historical compatibility overlay may suppress only the documented legacy
  `docutils` warning category, while current and development builds keep the
  unsuppressed strict policy. Build manifests record source SHAs and package
  provenance, and failed versions must not produce deployable partial output.
- Existing version paths, resolving `.html` pages, and pre-cutover root or
  `/stable/` URLs require a tested compatibility mapping before removal or
  redirection.
- The Pages artifact contains only deployable files plus public-safe
  `/_meta/catalog.json` and `/_meta/build-manifest.json`. It excludes caches,
  build scripts, private paths, credentials, raw workflow data, and unneeded
  generated sources. The inventoried root `/_sources/index.md.txt` entry is a
  documented compatibility exception; channel source trees remain excluded.
- Catalog, build, deployment, and post-deployment smoke checks use separate
  least-privilege workflow boundaries. Release source code and demos never
  receive GitHub, Pages, PyPI, OIDC, or repository-write credentials.
- The catalog job compares the current immutable release set with the last
  public build manifest; removing a deployed release requires a reviewed
  policy entry. Pull requests use a local fixture, and workflow dispatch can
  run a non-deploying exact-tag release-candidate build.
- Strict Sphinx, demo, metadata, link, artifact, dependency, workflow, and
  accessibility checks are required; skipped checks are reported as skipped.
- Historical Mermaid diagrams are rendered to self-contained SVG assets during
  the build; published documentation must not load Mermaid, tooltip, or other
  documentation runtimes from floating external URLs.
- The first clean site artifact records file count and deterministic compressed
  and uncompressed sizes. Later builds fail on unexplained growth greater than
  20% against the tracked baseline.

## Structural reform target contract

The following target contract is approved by
[Issue #165](https://github.com/SoichiroYamane/gsplot/issues/165). It becomes
the implementation contract for the 0.4.x compatibility line and the 1.x
stabilization line. The current 0.3.x behavior remains the baseline until the
corresponding implementation slices are merged.

### Ownership and package boundary

- New code uses `import gsplot as gs` and receives every `Figure` and `Axes`
  object it operates on explicitly.
- `subplots()` returns `(Figure, axes)`, where `axes` follows ordinary
  Matplotlib squeeze behavior or is a validated mosaic mapping. The old
  `axes()` flat-list/current-object contract is a compatibility adapter.
- No canonical function uses caller-frame inspection, a figure/axes singleton,
  a color or range singleton, hidden counters, or implicit storage ordering.
- The canonical implementation lives under `src/gsplot/` with private
  `_core`, `_config`, `_figure`, `_plot`, `_style`, `_io`, and `_compat`
  packages. Historical documented module paths may remain as forwarding-only
  shims during the compatibility window.
- `py.typed` is shipped. `__version__` reads installed distribution metadata
  with a safe source-tree fallback; `gsplot.version` is a tiny compatibility
  shim and is not generated by a workflow.

### Canonical API and lifecycle

The canonical root functions are:

```text
subplots, inset_axes, line, scatter, cmap_line, cmap_dash, cmap_scatter,
sample_cmap, style_axes, title, suptitle, minor_ticks, box_aspect,
panel_labels, fig_facecolor, legend, legends, legend_entries, cmap_legend,
set_theme, savefig, show, load_config, read_array, write_meta, build_info,
use_backend
```

`savefig(fig, ..., show=True)` saves all requested formats before displaying
the explicit figure. `show(fig)` is display-only and never saves or closes.
`close=True` is explicit and cannot be combined with display. Output paths,
parent-directory creation, overwrite behavior, supported formats, and output
errors are validated before mutation.

Plotting functions accept an explicit `Axes`, return ordinary Matplotlib
artists, use closed typed property schemas, and reject unknown or duplicate
controls before mutating the target. Colored plotting validates finite,
non-empty data and its segment/color requirements. Styling functions use
typed `AxisSpec`, `Theme`, and related values and never rely on a global
`rcParams` mutation for ordinary operation.

The default-value contract is explicit:

- `subplots()` defaults to one ordinary Matplotlib subplot, the Matplotlib
  default figure size, `squeeze=True`, `clear=False`, and no layout engine
  unless a direct argument or `Config` enables one.
- Canonical colored helpers use `cmap_line(..., linewidths=1.0)`,
  `cmap_dash(..., dash=(10.0, 10.0), linewidths=1.0)`, and
  `cmap_scatter(..., s=1.0, alpha=1.0)`.
- The root compatibility facade preserves the historical viridis automatic
  color sequence for otherwise option-free `line` and `scatter` calls.
  Supplying `props` or an explicit `Config` selects the canonical explicit
  behavior.
- The legacy `axes()` adapter retains its 5-by-5 inch, `mosaic="A"`,
  `clear=True`, and tight-layout behavior. Its `store` flag controls whether
  legacy `show()` writes files; this state is isolated to the compatibility
  boundary.

Removing import-time `rcParams` mutation is intentional. Consequently,
canonical imports use Matplotlib's ambient defaults rather than the historical
0.x values for margins, tick direction, tick placement, legend framing, and
related global settings. Applications that need those global values must use
Matplotlib's explicit `rc_context` or set the corresponding Figure/Axes
properties.

### Configuration and dependencies

- `Config` is an immutable value with schema version 1 and only `figure` and
  `plotting` sections. `Config.from_file()`, `Config.from_mapping()`, and
  `Config()` are explicit entry points.
- JSON is the only canonical configuration format. Duplicate keys, trailing
  content, non-finite numbers, unknown keys, oversized files, and invalid
  values fail with typed configuration errors. Configuration discovery is
  explicit and does not run during import.
- The target configuration precedence is explicit function arguments, then
  the supplied `Config`, then validated defaults. It has no backend, logging,
  Rich, YAML, output, or metadata section.
- The reform target removes Rich, PyYAML, and `types-PyYAML` from direct
  runtime dependencies and does not parse legacy YAML after the cutover. No
  unrelated dependency is introduced to replace them.
- `read_array()` never changes the working directory. `write_meta()` writes a
  typed snapshot using stable JSON and explicit atomic/exclusive policies.

### Compatibility and documentation

All legacy root forms and every module/symbol in the pre-cutover API reference
have a reviewed mapping in
[`api-migration.md`](api-migration.md). They remain forwarding-only adapters
through 0.4.x and 1.x unless a separate Issue changes that decision. The
candidate removal point is no earlier than 2.0 and requires downstream audit
and migration documentation.

Public functions and classes use NumPy-style docstrings. Sphinx uses
autodoc/autosummary/napoleon with type-hint descriptions and does not expose
undocumented canonical members. Existing demo URL paths and literal includes
remain stable during the first cutover; new guides explain the canonical API
and migration from legacy calls.

### Import and security boundary

Importing `gsplot` must not select a backend, import pyplot eagerly, mutate
`rcParams`, load configuration, create project files, configure the root
logger, or write metadata. A `NullHandler` is permitted. `use_backend()` is
explicit and is valid only before a figure/backend lock. These rules reduce
surprising process-wide effects and are covered by isolated-process tests.

The package remains safe for a public repository: no credentials, private
paths, machine-specific logs, or generated local artifacts are accepted in
source, documentation, tests, Issues, PRs, or built distributions.

## Non-functional requirements

### NFR-1: Supported environment and dependencies

- The supported Python range is Python 3.10 or newer, subject to the support
  policy of declared dependencies.
- Runtime dependencies are Matplotlib and NumPy. Rich, PyYAML, and
  `types-PyYAML` are not required by the canonical package or its compatibility
  shims; legacy YAML/Rich settings are ignored with a deprecation warning.
- `pyproject.toml` is authoritative for package metadata and dependency
  declarations. `poetry.lock` is the reproducibility record for development
  and validation.
- Dependency updates must be intentional, reviewable, and checked for
  compatibility and supply-chain risk.

### NFR-2: Determinism and state safety

- Tests and demos must use deterministic inputs and fixed random seeds when
  randomness is necessary.
- Tests must restore or isolate process-global state, including Matplotlib
  `rcParams`, the current figure, gsplot configuration, singleton stores,
  axes-range state, and the current working directory.
- Figures created by tests must be closed.
- Functions must not mutate caller-owned arrays, dictionaries, or lists unless
  mutation is explicitly documented.

### NFR-3: Quality gates

Relevant changes must pass focused tests and then the applicable broad checks:

- pytest behavior tests with `MPLBACKEND=Agg`;
- Black and isort checks;
- mypy, Pyright, and Python bytecode compilation;
- strict Sphinx documentation builds;
- demo and multiversion documentation builds when documentation paths change;
- Poetry package builds with inspection of both artifacts;
- local dependency auditing and available secret/workflow scanners; and
- coverage reporting with at least 85 percent across canonical implementation
  modules and at least 95 percent across the pure `_core` modules; and
- `git diff --check` plus a complete manual diff review.

Skipped or unavailable checks must be reported as blocked or skipped, never as
passing.

### NFR-4: Security and public disclosure

The repository, Issues, PRs, CI logs, generated documentation, and release
artifacts are public. They must not contain secrets, private keys, tokens,
credentials, personal data, private SSH details, internal hostnames,
unredacted logs, or machine-specific absolute paths.

GitHub Actions must use least-privilege permissions. Untrusted pull requests
must not receive secrets or privileged write access. Workflow actions must be
pinned and reviewed for supply-chain risk where practical. PyPI publishing
must use GitHub OIDC trusted publishing through the pinned PyPA publish action.
The publishing workflow must build distributions without OIDC permissions,
transfer them as a reviewable artifact, and grant `id-token: write` only to
the separate publish job. The publish job must use the dedicated `pypi`
environment and retain only `contents: read` alongside the OIDC permission.
The repository must not depend on a long-lived PyPI API token for normal
publishing.

Security findings must use the private disclosure process in `SECURITY.md`.
Public records should contain only safe advisory identifiers, affected and
fixed versions, impact, remediation, validation evidence, and residual risk.

### NFR-4a: Dependabot and repository controls

- `.github/dependabot.yml` must monitor the Poetry/pip and GitHub Actions
  ecosystems on a weekly schedule with bounded pull-request volume and stable
  labels.
- Routine minor and patch version updates may be grouped per ecosystem.
  Security updates and major updates must remain independently reviewable
  unless a later Issue explicitly changes that policy.
- Repository-level Dependabot alerts, automated security fixes, secret
  scanning, push protection, generic secret-pattern scanning, and private
  vulnerability reporting must remain enabled where GitHub makes the feature
  available to this public repository.
- GitHub Actions must default to read-only `GITHUB_TOKEN` permissions, must not
  approve pull request reviews, must require full-length action SHAs, and must
  allow only GitHub-owned actions and explicitly reviewed third-party action
  namespaces.
- Workflows triggered by untrusted pull requests must not receive secrets or
  privileged write access. Fork pull request execution must require maintainer
  approval for external contributors.
- The `main` branch must require a pull request, the named CI and security
  checks, resolved conversations, linear history, stale-review dismissal, and
  approval of the latest push when an independent reviewer is available.
  Force-pushes and branch deletion must be blocked. When at least two
  maintainers are available, require at least one independent GitHub approval
  and latest-push approval. With one maintainer, the required approval count
  and latest-push approval may both be disabled; self-approval and
  administrative bypass are prohibited, and the public maintenance protocol
  still requires Review 1 and Review 2 before handoff. Restore both approval
  settings when a second maintainer becomes available.
- Generated version metadata must enter `main` through the same reviewable
  pull-request path as other changes. With the restricted Actions token, the
  workflow may update only the fixed `automation/version-metadata` topic branch
  and must expose a public-safe manual PR link in the job summary. A maintainer
  opens a normal PR and follows Review 1 / Review 2; eligible generated
  metadata may enable GitHub auto-merge after the required checks pass. The
  workflow must never use a privileged direct push, pull-request approval, or
  auto-merge bypass to circumvent branch protection.
- Repository settings are external state. A settings change must be defined
  in a public Issue, implemented or recorded in its linked PR (Draft optional), verified
  through the GitHub UI or API, and documented with public-safe evidence.
- A linked PR is required for active implementation, but Draft status is
  optional. Review 1 and Review 2 remain mandatory public records before any
  merge. GitHub auto-merge may be enabled only for generated metadata and
  explicitly classified low-risk routine maintenance after the review and
  required-check gate. Workflow, Actions permission, repository-settings,
  branch-protection, release, publish, secret, major-update, breaking
  API/configuration, and judgment-heavy security changes require manual merge.
- Auto-merge must not approve its own PR, bypass protected `main`, expose
  secrets to untrusted code, or replace Issue requirements, review records, or
  required CI/security checks.
- CodeQL default setup must analyze the supported `python` and `actions`
  targets with the default query suite on standard GitHub-hosted runners.
  Initial findings must be reviewed and resolved or justified; findings must
  not be silently dismissed or replaced by AI-generated suggestions.
- The CodeQL result may become a required `main` check only after a successful
  baseline analysis, exact check-name verification, and a review of the
  generated or dynamic workflow's permissions and action provenance.
- Copilot Autofix, AI findings Preview, and third-party code-scanning tools are
  optional and are not enabled by default. They require a separate Issue when
  their privacy, cost, noise, or maintenance trade-offs are accepted.

### NFR-5: Contributor experience

- A new contributor must be able to install the locked development environment,
  run the tests, build the docs, and build the package using the developer
  documentation.
- Source organization, public API lists, tests, demos, docs, packaging, and CI
  must be updated together when a contract changes.
- Internal implementation classes may change freely when the public contract
  and migration behavior remain clear.

## Architecture constraints

The current implementation uses a shared parameter-resolution flow:

`@bind_passed_params()` -> `ParamsGetter` -> `CreateClassParams` ->
implementation class.

This flow may be redesigned, but a replacement must preserve or explicitly
replace the following observable behavior:

- explicit arguments override configuration and defaults;
- aliases and unknown pass-through keyword arguments keep their documented
  behavior;
- public wrappers and module `__all__` declarations remain synchronized; and
- configuration and Matplotlib state do not leak across isolated operations
  beyond documented process-wide behavior.

Import-time configuration, logging, and metadata behavior are currently part
of the implementation. Any change to those side effects requires a migration
note, tests for scripts and demos, and a clear user-facing explanation.

## Compatibility and reform policy

Compatibility is valuable but is not an absolute constraint. Fundamental
reform of code, public APIs, configuration semantics, or directory structure
is allowed when it materially improves correctness, security,
maintainability, or usability.

Every substantial change must:

1. identify affected imports, configuration keys, consumers, tests, demos,
   docs, packaging, and workflows;
2. classify each changed contract as compatible, deprecating, or breaking;
3. provide a migration path for breaking behavior when practical;
4. remove stale references and misleading compatibility shims when the new
   contract is intentional; and
5. record the decision, alternatives, validation, and residual risks in the
   linked Issue and PR.

The following are candidate directions for a future redesign and are not
implicit permission to change behavior without an Issue-level decision:

- make configuration and metadata side effects more explicit and easier to
  isolate;
- define a clearer lifecycle for figure storage and shared state;
- formalize configuration validation and error messages;
- reduce duplication between plotting wrappers and implementation classes; and
- make the supported root API and deprecation policy easier to discover.

## Acceptance criteria for a requirement-changing release

A requirement-changing release is ready only when all applicable criteria are
met:

- the linked Issue contains the problem, scope, non-goals, acceptance
  criteria, compatibility position, security impact, and public references;
- the linked PR describes status, changed surfaces, validation, blockers,
  residual risks, and the next action;
- implementation, tests, demos, docs, API reference, packaging, and workflows
  agree with the new contract;
- compatible paths are tested and breaking paths have migration guidance;
- the relevant Python versions and headless environment pass the validation
  matrix;
- dependency and workflow changes have been reviewed for supply-chain risk;
- built artifacts contain the intended files and metadata only; and
- no secrets, private operational details, or unintended generated files are
  present in the final diff.

## Public work tracking

The repository adopts a four-layer work model:

- `docs/project/requirements.md` is the stable product and engineering
  contract. It must not become a task status log or a chronological diary.
- One public GitHub Issue is the source of truth for each durable user-facing
  goal. It contains the problem, scope, non-goals, acceptance criteria,
  compatibility position, security impact, decisions, and public references.
- One linked PR is the source of truth for active implementation. Draft status
  is optional. Its description contains current status, changed surfaces,
  validation results, blockers, residual risks, screenshots when relevant, and
  the next action.
- An optional GitHub Project is a dashboard for prioritization and visibility
  across Issues and PRs. It is not a second requirements database and does not
  replace either the Issue or the linked PR.

Use Issue comments for durable decisions and evidence. Use the linked PR body
and review comments for implementation progress and code-review context. Keep
both records concise, factual, reproducible, and safe to quote.

For a related security or Dependabot batch, use one parent maintenance Issue,
link the individual PRs, and record advisory IDs, fixed versions,
classification, validation, and residual risk. Keep confidential vulnerability
details in the private reporting channel described by `SECURITY.md`.

The normal lifecycle is Issue intake -> acceptance criteria -> linked PR (Draft
optional) -> Review 1 (requirements and risk) -> Review 2 (complete diff and
checks) -> required checks -> enable auto-merge or merge manually -> close.
Temporary notes, private deliberation,
raw terminal output, credentials, and local environment details remain outside
the repository.
