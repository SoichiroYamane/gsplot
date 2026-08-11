---
name: gsplot-maintenance
description: Maintain, redesign, secure, and review the public gsplot Python scientific-plotting repository, including Matplotlib behavior, configuration precedence, public APIs, directory migrations, tests, demos, Sphinx documentation, Poetry dependencies, security advisories, pull requests, GitHub Actions, packaging, and repository guidance. Use when Codex changes or validates this repository's code, architecture, dependencies, workflows, docs, demos, AGENTS.md, linked Issue/PR records, or repository-scoped skills.
---

# gsplot Maintenance

Maintain gsplot as a public repository. Preserve verified behavior where it is
valuable, but allow fundamental reform when it improves correctness, security,
maintainability, documentation, or the contributor experience. Keep
project-specific procedure here and leave generic Python knowledge to the
model. Repository guidance, this skill, and project documentation are written
in English.

## Start with repository context

Read, in this order, before editing:

1. `AGENTS.md`
2. `docs/project/requirements.md` and the linked GitHub Issue/Draft PR when available
3. `pyproject.toml` and the relevant sections of `poetry.lock`
4. `README.md` and the relevant `docs/` guide or API page
5. the target implementation, its imports/consumers, related tests, and related demo
6. the relevant `.github/workflows/*.yml` file when CI, release, security, or docs behavior is in scope

Run the read-only triage before implementation:

```bash
git status --short --branch
git remote -v
git log -5 --oneline --decorate
```

Record whether the change affects public API, global Matplotlib state, configuration, generated docs, packaging, or CI. Do not infer behavior from filenames alone: verify the actual import path and current consumer.

## Issues, PRs, and public progress

- Use a four-layer public work model:
  `docs/project/requirements.md` contains stable requirements, the GitHub Issue
  contains the durable goal, the linked Draft PR contains active implementation
  progress, and an optional GitHub Project provides dashboard views only.
- Keep one durable user-facing goal per public GitHub Issue. The Issue must
  state the problem, scope, non-goals, acceptance criteria, compatibility,
  security impact, decisions, and public evidence.
- Use one linked Draft PR for active implementation. Its description must
  state current status, changed surfaces, validation, blockers, residual risks,
  screenshots when relevant, and the next action.
- Use Issue comments for decisions and durable evidence. Use the Draft PR body
  and review comments for implementation progress and code-review context.
  Update the appropriate record before or alongside substantial work.
- Use labels, milestones, linked Issues/PRs, and an optional Project for
  prioritization and visibility. Never duplicate the requirements database in
  a Project or use it as a replacement for the Issue and Draft PR.
- For a related security or Dependabot batch, use a parent maintenance Issue,
  link the individual PRs, and record advisory IDs, fixed versions,
  classification, validation, and residual risk. Keep vulnerability details
  that require confidentiality in the SECURITY.md reporting channel.
- Follow this lifecycle: Issue intake -> acceptance criteria -> linked Draft
  PR -> Review 1 (requirements and risk) -> Review 2 (complete diff and checks)
  -> ready for review -> merge and close.
- Do not create a chronological progress diary, private deliberation, raw
  terminal transcript, credential, or machine-specific path in the repository.
- Redact secrets, private infrastructure, credentials, personal data, raw
  logs, and machine-specific paths from Issues, PRs, commits, and handoffs.

Update the linked Issue or Draft PR before or alongside substantial work. If
the requirements change, update `docs/project/requirements.md` and explain the
compatibility position in the Issue/PR.

## Public-repository security gate

Treat all repository content, CI output, and PR branches as public or untrusted:

- Do not add secrets, private keys, tokens, `.env` files, personal data,
  internal hostnames, SSH details, unredacted logs, or local absolute paths.
- Inspect downloaded artifacts and external PR code before execution. Never
  expose untrusted code to secrets, production credentials, or privileged write
  access.
- Keep workflow permissions minimal. Do not add broad tokens, convenient
  `contents: write`, or unsafe `pull_request_target` execution for fork code.
- Prefer PyPI trusted publishing through GitHub OIDC. The publishing workflow
  should use the PyPA publish action pinned to a full commit SHA, separate
  unprivileged building from publishing, and grant `id-token: write` only to
  the publish job in a dedicated environment. Treat token publishing as a
  temporary, reviewed rollback path and never expose the token.
- Review dependency release scripts, build backends, install hooks, workflow
  actions, Docker changes, generated files, and copied assets as supply-chain
  sensitive.
- Use available secret/dependency scanners, then manually review the complete
  diff even when scanners are clean.

Use private channels for coordinated disclosure details. Record only public
identifiers, evidence, impact, remediation, and residual risk in Issues/PRs.

## Dependabot and repository-settings workflow

Treat Dependabot configuration and GitHub repository settings as one public
maintenance surface, while keeping repository settings separate from the
tracked YAML source:

1. Read `.github/dependabot.yml`, every workflow that uses an action or writes
   a tracked file, the current default branch checks, and the current GitHub
   settings before editing.
2. Create or update the durable Issue before substantial work. Record the
   intended schedule, ecosystem coverage, grouping boundary, security features,
   Actions policy, merge policy, branch-protection policy, compatibility,
   non-goals, and safe public evidence.
3. Keep routine minor/patch version updates groupable, but keep major and
   security updates independently reviewable unless the Issue explicitly
   changes that policy. Do not treat enabling repository security updates as a
   substitute for inspecting each generated PR.
4. Inspect every workflow action and permission before narrowing the Actions
   allowlist. Require full commit-SHA pins and permit only GitHub-owned actions
   plus reviewed third-party namespaces actually present in the workflows.
   Re-run actionlint and a workflow security scanner after changes.
5. Do not protect `main` until tracked-file automation is compatible with the
   protection rule. Replace direct privileged commits with a bounded,
   loop-safe pull-request workflow. If the restricted Actions token cannot
   create a pull request, allow only a fixed topic-branch push plus a
   public-safe manual PR handoff in the job summary; record that fallback in
   the Issue and never add approval or direct-main bypass capability.
6. Prefer a reviewable main-branch policy: required pull request, required CI
   and security checks, resolved conversations, linear history, stale-review
   dismissal, latest-push approval, and no force-push or deletion. Require at
   least one independent GitHub approval when at least two maintainers are
   available. With one maintainer, set the required approval count and
   latest-push approval to zero/off rather than using self-approval or an
   administrative bypass; the repository's separate public protocol still
   requires Review 1 and Review 2. Restore both approval settings when a
   second maintainer becomes available.
7. Apply GitHub settings only after the Issue and implementation record are
   current and the user has authorized the settings change. Read back every
   mutated endpoint, compare it with the requested policy, and record the
   result without exposing secrets, private host details, or raw credentials.

The GitHub API/UI is the source of truth for effective repository settings;
`.github/dependabot.yml`, workflows, and the stable requirements document are
the source of truth for the intended tracked policy. Never silently widen
workflow permissions, allow arbitrary actions, enable direct-main bypasses, or
change collaborators and secrets as incidental cleanup.

For CodeQL default setup:

- Prefer the default setup for public Python and GitHub Actions coverage on
  standard GitHub-hosted runners. Keep the default query suite unless a
  documented risk decision justifies the extended suite.
- Inspect the default-setup configuration and the initial analysis before
  changing branch protection. Verify whether the result is a dynamic GitHub
  workflow or a generated workflow file, and check its triggers, permissions,
  action provenance, secrets exposure, and selected-action compatibility.
- Review every initial finding. Resolve or justify findings without exposing
  exploit details or using blanket dismissals. CodeQL is additive to tests,
  dependency auditing, Dependabot, secret scanning, and manual workflow review.
- Add the exact CodeQL check to protected `main` only after a successful
  baseline and a public Review 1 / Review 2 record. Keep Copilot Autofix, AI
  findings Preview, and third-party scanners out of scope unless a separate
  Issue accepts their cost, privacy, noise, and maintenance trade-offs.

## Fundamental reform workflow

Allow fundamental code, public API, configuration, or directory reform when it
materially improves the project. Do not preserve an unsafe or misleading
structure merely to minimize the diff.

1. Define the outcome and acceptance criteria in the linked Issue.
2. Map public imports, configuration keys, consumers, tests, demos, docs,
   packaging, CI, and migration impact.
3. Classify each affected contract as compatible, deprecating, or breaking.
4. Record alternatives, migration/deprecation behavior, and residual risks in
   the Issue and Draft PR.
5. Implement the coherent change across source, tests, docs, examples, API
   lists, packaging, and workflows.
6. Remove stale references and misleading compatibility shims when the new
   contract is intentional.
7. Validate old and new paths wherever compatibility is promised, then update
   the Issue/PR with evidence.

## Preserve the project model

Follow these invariants when changing code:

- Keep the public wrapper in `gsplot/__init__.py` and the module's `__all__` synchronized with any API change.
- Preserve the common wrapper flow: `@bind_passed_params()` captures explicit arguments, `ParamsGetter` reads them, and `CreateClassParams` merges defaults, config, and passed values.
- Treat configuration precedence as direct arguments > the matching `gsplot.json` entry > function defaults. Check both alias names and canonical names when modifying a configurable function.
- Keep Matplotlib `Axes` compatibility. A gsplot plot function should cooperate with regular `Axes.plot`, `Axes.scatter`, `plt.sca`, and existing figure lifecycle behavior.
- Treat `Config`, `StoreSingleton`, `AxesRangeSingleton`, `rcParams`, current figure, and current working directory as shared state. Reset or restore state in tests and avoid leaking it between cases.
- Prefer assertions about returned artists, labels, limits, colors, collections, and axis state. Add image comparisons only when a visual regression cannot be expressed structurally.
- Keep scientific data and demo examples deterministic. Use small explicit arrays, fixed random seeds when randomness is necessary, and `MPLBACKEND=Agg` for headless checks.

## Choose the task workflow

### Code or behavior change

1. Locate the public entry point, implementation class/function, decorators, aliases, and stateful collaborators.
2. Add or update a focused test beside the relevant test area. Use `tmp_path`, `monkeypatch`, `unittest.mock`, or explicit Matplotlib cleanup for external files and global state.
3. Exercise both the normal path and the relevant boundary: invalid unit, empty mosaic, missing config, alias conflict, array shape, or no-display backend as applicable.
4. Run the narrow test first, then the full available suite. Separate failures
   caused by the patch from pre-existing collection or environment failures.
   If the linked Issue calls for a fundamental redesign, validate the new
   contract and its migration path rather than optimizing only for diff size.

### Configuration change

1. Inspect `Config`, `ConfigLoad`, `config_load`, the target function signature, and a representative `demo/*/gsplot.json`.
2. Confirm the key is the function name expected by `CreateClassParams`; preserve the handling of unknown keys passed through `kwargs`.
3. Test direct arguments, config-only values, defaults, and invalid values. Do not mutate a shared config dictionary or `rcParams` unintentionally.

## Security-update workflow

Treat security fixes as a focused workstream, not as permission for unrelated
dependency churn:

1. Inventory direct/transitive dependencies, `poetry.lock`, Docker, workflows,
   install/build behavior, and generated artifacts.
2. Check GitHub Security/Dependabot data and authoritative upstream sources:
   project release notes, PyPI, CVE/GHSA/OSV records, or vendor advisories.
   Do not rely on search snippets alone.
3. Record the advisory ID, affected/fixed ranges, severity, reachability
   context, public links, and proposed action in the linked Issue/PR.
4. Choose the smallest safe fixed version. Update `poetry.lock` only when the
   dependency change is intentional and inspect every lockfile change.
5. Inspect the dependency diff for unrelated or malicious changes.
6. Run focused tests, the full relevant suite, types, syntax, docs/demos,
   packaging, and available security scans. Verify the fixed version in the
   lockfile and built artifact.
7. Record resolution, compatibility impact, residual risk, and follow-up work.

Do not declare an advisory resolved solely because a version string changed.

## Pull-request workflow

Treat PR handling as review and preparation unless the user separately
authorizes a remote mutation:

1. Snapshot the working tree and remotes; preserve unrelated changes.
2. Confirm the PR links to the correct durable Issue. If no Issue exists,
   define the Issue content before substantial implementation and do not use a
   PR as the only requirements record.
3. Build a read-only inventory of open PRs, security/dependency PRs, reviews,
   required checks, conflicts, linked Issues, and changed files.
4. Inspect the diff and commit history before executing PR code. Review
   workflows, package installation, shell commands, permissions, secrets,
   dependency metadata, and generated files first.
5. Classify each PR as mergeable, requiring changes, obsolete, duplicate,
   security-sensitive, or blocked, and record public evidence.
6. Reproduce issues in isolation. Apply focused local fixes, update tests/docs
   and the linked Issue/PR, and validate without rewriting intent unnecessarily.
7. Recheck the final diff, dependency provenance, CI trust boundary, and public
   disclosure risk.
8. Do not approve, merge, close, delete branches, publish, release, push, or
   modify repository settings without explicit authorization for that action.

### Plot or visual change

1. Use `MPLBACKEND=Agg` for non-interactive validation and avoid forcing a backend in library code unless the feature explicitly requires it.
2. Verify the returned Matplotlib artist type and important properties before relying on a screenshot.
3. If a demo is the canonical example, run only that demo first and check for newly generated images, data files, `version.py`, and API documentation changes.

### Documentation or demo change

1. Follow the existing MyST/Sphinx structure and use `literalinclude` for demo source when appropriate.
2. Check relative paths from the document, demo working directory assumptions, and the static `docs/api_reference/apis.rst` module list.
3. Treat `docs/conf.py` as executable build code: it runs every demo in a fresh headless subprocess. The standalone `scripts/docs/build_demo_images.py` helper can refresh demo assets without starting Sphinx.
4. Inspect and revert unrelated generated changes after a build. Demo image files and `.gsplot` metadata are ignored local output, not documentation source.

### Packaging or CI change

1. Treat `pyproject.toml` as the dependency/build authority and `poetry.lock` as the reproducibility record. Update the lock only when the dependency change is intentional.
2. For package changes, run `poetry build` and inspect both artifacts. Never run `poetry publish` unless explicitly requested.
3. For workflow changes, inspect permissions, triggers, secrets, branch filters, and auto-commit behavior. Do not broaden permissions or add release/publish behavior as a side effect.

## Validation matrix

Run the smallest relevant set, then expand for the affected surface:

```bash
# Unit and behavior tests in a display-less environment
MPLBACKEND=Agg poetry run pytest -q

# Formatting and imports
poetry run black --check gsplot tests scripts docs/conf.py
poetry run isort --profile black --check-only gsplot tests scripts docs/conf.py

# Types and syntax
poetry run mypy --config-file .mypy.ini gsplot
poetry run pyright gsplot
python -m compileall -q gsplot tests scripts

# Documentation and packaging, only when relevant
MPLBACKEND=Agg poetry run sphinx-build -W -b html docs docs/_build/html
poetry build
poetry run pip-audit --local
git diff --check
```

For security or PR work, also inspect the dependency graph/lockfile, workflow
permissions, built artifact, affected demos, and available scanners. If the
Poetry environment is absent, use a compatible Python version or an equivalent
isolated environment and record the exact limitation. Do not claim a check
passed when a command was skipped because a tool or dependency was unavailable.
Do not treat an interactive `plt.show()` window as evidence of a successful
headless build.

## Environment caveats

Re-check these conditions instead of hiding them:

- Use Python 3.12 for the locked Poetry environment. On Python 3.14, some locked versions may fall back to source builds or fail their supported-Python checks even when the project itself supports Python 3.10+.
- Documentation builds execute demos and may create ignored PNG files and user-level logs. Always use `MPLBACKEND=Agg` in CI or headless environments and review `git status` after the build.
- `gsplot/version.py` is generated by the version workflow and is excluded from Black checks; do not hand-format or hand-edit it during ordinary maintenance.

## Review and handoff

Perform two passes before handoff:

1. Review 1: check the linked Issue requirements, public API, configuration
   precedence, global state, test coverage, docs/CI side effects, dependency
   provenance, generated files, and secrets.
2. Review 2: inspect the staged diff with `git diff --cached --check`,
   `git diff --cached --stat`, `git diff --cached`, and final
   `git status --short --branch`; verify that only intended files changed and
   every reported validation result is reproducible.

If Review 1 or Review 2 finds a problem, fix it and repeat both reviews.
Report blockers explicitly. Leave commit, push, approve, merge, close, publish,
release, secret rotation, repository settings, and branch-protection changes to
an explicit user request.
