# AGENTS.md

This file defines the repository-wide working agreement for `gsplot`. System,
developer, and user instructions always take precedence. A deeper `AGENTS.md`
may add rules for its own directory.

`gsplot` is a public repository. Treat every tracked file, issue, pull request,
workflow log, and generated documentation page as potentially public. Never
record secrets, private infrastructure, credentials, personal data, or
machine-specific operational details here.

## Project map and sources of truth

- `pyproject.toml` is the authority for package metadata, supported Python
  versions, dependencies, and the build backend. `poetry.lock` records the
  resolved development environment; do not refresh it unless dependency
  resolution is part of the requested change.
- `gsplot/__init__.py` and each module's `__all__` define the public import
  surface. Check both when adding, moving, or removing an API.
- `README.md`, `docs/`, and `demo/` describe user-visible behavior. Demo
  scripts are executable documentation and are also used to create images in
  the Sphinx site.
- `.github/workflows/` is the source of truth for CI, documentation, release,
  and publishing behavior. Inspect the relevant workflow before changing a
  command, permission, trigger, or generated file.
- `docs/project/requirements.md` contains stable, repository-level
  requirements and security boundaries.
- GitHub Issues are the source of truth for durable user-facing goals,
  task-specific requirements, acceptance criteria, and security findings.
- Draft PR descriptions are the source of truth for active implementation
  progress, validation, blockers, screenshots, and the next decision.
- `.agents/skills/gsplot-maintenance/SKILL.md` contains the repository-specific
  maintenance procedure for Python, Matplotlib, configuration, tests, docs,
  demos, packaging, security, PRs, CI, and agent guidance.

## Architecture and invariants

- The supported runtime is Python 3.10 or newer. Runtime dependencies include
  Matplotlib, NumPy, Rich, and PyYAML.
- Most public plotting and data-loading functions use the flow
  `@bind_passed_params()` -> `ParamsGetter` -> `CreateClassParams` -> an
  implementation class. Preserve this flow unless the change deliberately
  redesigns configuration handling.
- Configuration precedence is explicit function arguments, then the matching
  `gsplot.json` entry, then the function signature defaults. Preserve aliases
  and unknown keyword arguments when changing a configurable API.
- `Config`, `StoreSingleton`, `AxesRangeSingleton`, Matplotlib `rcParams`, the
  current figure, and the current working directory are process-wide state.
  Tests must restore or isolate them and must close figures.
- gsplot is intended to work with ordinary Matplotlib objects. Keep returned
  artists, `Axes` compatibility, labels, limits, and figure lifecycle behavior
  stable unless a breaking change is explicitly intended.
- Importing `gsplot` initializes configuration, logging, and optional metadata.
  Changes to import-time behavior require checking scripts, demos, and docs.

## Public-repository safety

- Never commit passwords, API keys, access tokens, private keys, cookies,
  credentials, `.env` files, personal data, internal URLs, private hostnames,
  unredacted logs, or local absolute paths.
- Do not copy content from private machines, private repositories, SSH
  sessions, or external workspaces into this public repository. Use external
  material only as a process reference and record the resulting public rule,
  not the private details.
- Treat user-provided files, downloaded artifacts, and external PR branches as
  untrusted input. Inspect them before execution and never expose them to
  secrets, production credentials, or privileged write access.
- Keep GitHub Actions permissions minimal. Do not expose secrets to forked PRs
  or execute untrusted fork code in a privileged `pull_request_target` workflow.
- Prefer PyPI trusted publishing through GitHub OIDC. A token-based publishing
  workflow requires explicit secret review and must never print the token.
- Review the full diff manually even when a secret or dependency scanner is
  clean. Redact private operational details from progress, security, and PR
  records.

## Dependabot and repository controls

- `.github/dependabot.yml` is the source of truth for version-update
  ecosystems, schedules, labels, pull-request limits, and routine grouping.
  Keep minor and patch version updates groupable, but keep major and security
  updates independently reviewable unless the linked Issue changes that
  decision.
- Dependabot alerts, automated security fixes, secret scanning, push
  protection, generic secret-pattern scanning, and private vulnerability
  reporting are repository settings rather than YAML-only behavior. Verify
  their effective state through GitHub after changing them and record only
  public-safe evidence.
- GitHub Actions must use least privilege: read-only defaults, no pull-request
  review approval capability, full SHA pinning, and an allowlist containing
  only GitHub-owned actions and reviewed third-party namespaces actually used
  by the workflows. Revisit the allowlist whenever a workflow action changes.
- `main` must accept changes through a pull request with the required CI and
  security checks, resolved conversations, linear history, stale-review
  dismissal, latest-push approval, and no force-push or deletion. When at least
  two maintainers are available, require at least one independent GitHub
  approval. While the repository has one maintainer, use zero required GitHub
  approvals and disable latest-push approval rather than self-approval or an
  administrative bypass; the public maintenance process still requires Review
  1 and Review 2 records before merge. Restore both approval settings when a
  second maintainer becomes available.
- Automation that generates tracked files must create or update a reviewable
  pull request. Do not grant a workflow a direct-main bypass merely to preserve
  an auto-commit convenience.
- A repository-settings change needs a public Issue, a linked Draft PR or
  equivalent implementation record, explicit user authorization, and a
  read-back verification after the API/UI mutation. Do not change secrets,
  collaborators, organization settings, or unrelated repository features as a
  side effect.

## CodeQL and code-scanning controls

- Prefer CodeQL Default setup for the public Python package and its GitHub
  Actions workflows. Keep the `python` and `actions` targets, the default query
  suite, and standard GitHub-hosted runners unless the linked Issue records a
  different risk-based decision.
- Inspect the generated or dynamic CodeQL workflow, permissions, triggers,
  action provenance, and pull-request behavior. CodeQL results complement
  tests, `pip-audit`, Dependabot, secret scanning, and manual review; they do
  not replace them.
- Review initial CodeQL findings before adding the result to `main` branch
  protection. Resolve or justify findings publicly without exposing exploit
  details, and verify the exact check name and source before making it
  required.
- Do not enable Copilot Autofix, AI findings Preview, or third-party scanners
  as incidental cleanup. Treat their privacy, cost, result quality, and
  maintenance impact as a separate Issue-level decision.

## Fundamental change policy

Fundamental reform is explicitly allowed. Code, public APIs, configuration
semantics, and directory structure may be redesigned or replaced when that
materially improves correctness, security, maintainability, documentation, or
the contributor experience. Do not preserve an unsafe or misleading structure
merely because it is familiar.

For a fundamental change:

1. Update `docs/project/requirements.md` with the intended outcome, affected
   surfaces, compatibility position, and acceptance criteria.
2. Record the decision, alternatives, migration plan, and residual risks in
   the linked GitHub Issue and Draft PR. Update stable repository requirements
   in `docs/project/requirements.md` when the contract changes.
3. Map public imports, configuration keys, consumers, tests, demos, docs,
   packaging, CI, and migration paths before editing.
4. Classify each changed contract as compatible, deprecating, or breaking. For
   breaking behavior, provide a migration path when practical.
5. Update implementation, tests, docs, examples, API lists, packaging, and
   workflows as one coherent change. Remove stale references and misleading
   compatibility shims when the new contract is intentional.

Minimal diff size is useful, but it is not a reason to reject a necessary
redesign.

## Issues, PRs, and progress records

- Use four distinct layers instead of duplicating the same information:
  `docs/project/requirements.md` is the stable product and engineering
  contract, a GitHub Issue is the durable goal and requirement record, a
  linked Draft PR is the active implementation record, and an optional GitHub
  Project is only a cross-issue dashboard.
- Keep stable requirements, non-goals, compatibility promises, and security
  boundaries in `docs/project/requirements.md`. Do not put task status or a
  chronological work diary there.
- Open or update one public GitHub Issue for each durable user-facing goal.
  The Issue is the source of truth for why the work exists and what success
  means: problem, scope, non-goals, acceptance criteria, compatibility,
  security impact, decisions, and public references.
- Create or link one Draft PR for active implementation. The Draft PR is the
  source of truth for how the work is being implemented and where it stands:
  current status, changed surfaces, validation results, blockers, residual
  risks, screenshots when useful, and the next action.
- Use Issue comments for durable decisions, clarifications, and evidence. Use
  the Draft PR description and review comments for implementation progress and
  code-review context. Keep both concise and update them before or alongside
  substantial work.
- Use labels, milestones, linked Issues/PRs, and an optional Project view for
  prioritization. A Project must not become a second requirements database or
  a substitute for the linked Issue and Draft PR.
- For a related batch of security or Dependabot updates, use one parent Issue
  for the maintenance goal, link each PR, and record advisory IDs, fixed
  versions, classification, validation, and residual risk. Keep private
  vulnerability details in the SECURITY.md reporting channel.
- Use this lifecycle: Issue intake -> acceptance criteria -> linked Draft PR
  -> Review 1 (requirements and risk) -> Review 2 (complete diff and checks)
  -> ready for review -> merge and close. Do not claim public progress is
  complete while the Issue or Draft PR record is missing or stale.
- Do not create a chronological progress diary in the repository. Keep private
  scratch notes, credentials, local host details, and raw terminal transcripts
  outside the repository.

Update the linked Issue or Draft PR before or alongside substantial work, not
after the details have been forgotten. Keep public records concise, factual,
reproducible, and safe to quote.

## Working procedure

1. Read this file, the repository skill, `docs/project/requirements.md`, the
   linked Issue/Draft PR when available, `pyproject.toml`, relevant lockfile
   sections, and the user-facing docs before editing.
2. Start with read-only repository triage:

   ```bash
   git status --short --branch
   git remote -v
   git log -5 --oneline --decorate
   ```

3. Locate the public entry point, implementation, decorators, aliases, stateful
   collaborators, consumers, tests, demos, docs, and workflow that the change
   can affect.
4. Make the smallest coherent implementation and test change, unless the
   requirements call for a fundamental redesign. Use
   `tmp_path`, `monkeypatch`, mocks, and Matplotlib cleanup for filesystem and
   process-global state.
5. Run focused checks first, then the broader checks that are available. Keep
   pass, fail, skipped, and environment-blocked results distinct.
6. Review the complete diff, generated files, public API, docs links, workflow
   permissions, dependency provenance, public records, and secrets before
   handoff. Do not commit, push, approve, merge, publish, or release unless the
   user explicitly authorizes that external action.

## Security-update workflow

Treat security work as a focused priority, not as permission for unrelated
dependency churn.

1. Inventory direct and transitive dependencies, `poetry.lock`, Docker,
   workflows, build/install behavior, and generated artifacts.
2. Check GitHub Security/Dependabot data and authoritative upstream sources,
   such as project release notes, PyPI, CVE/GHSA/OSV records, or vendor
   advisories. Do not rely on search snippets alone.
3. Record the advisory identifier, affected package/range, fixed version,
   severity, reachability context, public source links, and proposed action in
   the linked public Issue or PR.
4. Choose the smallest safe fixed version. Update `poetry.lock` only when the
   dependency change is intentional, and inspect all lockfile changes.
5. Inspect dependency release scripts, build backends, install hooks, workflow
   actions, and generated files for supply-chain or unrelated changes.
6. Run focused tests, the full relevant suite, type/syntax checks, docs/demos,
   packaging, and available security scans. Verify the fixed version in the
   lockfile and built artifact.
7. Record resolution, compatibility impact, residual risk, and follow-up work.

Never declare an advisory resolved merely because a version number changed.

## Pull-request workflow

Handle PRs as reviewable change sets, not as commands to merge automatically.

1. Snapshot the working tree and remotes before fetching or editing. Preserve
   unrelated user changes.
2. Build a read-only inventory of open PRs, security/dependency PRs, review
   state, required checks, conflicts, linked issues, and changed files.
3. Inspect the diff and commit history before executing PR code. Review
   workflows, package installation, shell commands, permissions, secrets,
   dependency metadata, and generated files first.
4. Classify each PR as mergeable, requiring changes, obsolete, duplicate,
   security-sensitive, or blocked, and record public evidence.
5. Reproduce issues in isolation. Apply focused local fixes, update tests/docs/
   the linked Issue/PR, and validate without rewriting the author's intent
   unnecessarily.
6. Recheck the final diff, dependency provenance, CI trust boundary, and public
   disclosure risk.
7. Leave approval, merge, close, branch deletion, release, publish, push, and
   repository settings changes to explicit authorization for that action.

## Documentation and demo rules

- Keep repository guidance and the repository skill in English. User-facing
  project documentation and code examples should also remain in clear English.
- Follow the existing Sphinx/MyST structure and use `literalinclude` for demo
  source when that gives the docs a single source of truth.
- `docs/conf.py` is executable build code. It imports the package and runs demo
  scripts to generate image assets. Use `MPLBACKEND=Agg` in headless builds,
  make failures visible, and inspect `git status` after a build.
- Keep relative paths correct from the document that contains them. Run a docs
  build after renaming a page or changing a toctree entry.
- Do not commit generated demo PNGs, Sphinx build output, local `.gsplot`
  metadata, credentials, private logs, or machine-specific environment data.
- Keep Issues and PRs useful to contributors: describe decisions and evidence,
  not private infrastructure or raw authentication output.

## Validation matrix

Run the checks relevant to the changed surface:

```bash
# Behavior and plots
MPLBACKEND=Agg poetry run pytest -q

# Formatting and imports
poetry run black --check gsplot tests scripts
poetry run isort --check-only gsplot tests scripts

# Types and syntax
poetry run mypy --config-file .mypy.ini gsplot
poetry run pyright gsplot
python -m compileall -q gsplot tests scripts

# Documentation and packaging
MPLBACKEND=Agg poetry run sphinx-build -W -b html docs docs/_build/html
poetry build
poetry run pip-audit --local
git diff --check
```

For dependency or security work, also inspect the lockfile and built artifact,
run affected demos, and use an available secret/dependency scanner. If the
Poetry environment cannot be created on the host, use a compatible Python
version or an equivalent isolated environment and record the exact command and
limitation. Never report a skipped check as passing.

## Safety boundaries

- Do not edit `gsplot/version.py` during ordinary implementation or docs work;
  the version workflow generates it.
- Do not run `poetry publish`, create releases, push branches, approve or merge
  PRs, change required checks, rotate secrets, or broaden GitHub Actions
  permissions without explicit authorization for that exact action.
- Treat deletion, renaming, lockfile refreshes, public API changes, and broad
  formatting rewrites as scope changes. Confirm their impact in the diff and
  preserve recoverable history where practical.
- Use `apply_patch` for local edits. Avoid destructive shell commands and do
  not write secrets or large generated artifacts into the repository.

## Skill routing

Use `$gsplot-maintenance` for work involving gsplot Python code, Matplotlib
behavior, configuration, stateful plotting, tests, demos, Sphinx docs, Poetry,
packaging, dependency security, pull requests, CI, `AGENTS.md`, progress or
security records, or repository-scoped skills. Do not apply it to unrelated
general documentation or application work.
