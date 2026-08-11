# Security and secure contribution

The repository's canonical vulnerability-reporting process is defined in
[`SECURITY.md`](https://github.com/SoichiroYamane/gsplot/blob/main/SECURITY.md).
This page explains what contributors can expect from the public maintenance
workflow.

## Report vulnerabilities privately

Use the [private security advisory form](https://github.com/SoichiroYamane/gsplot/security/advisories/new)
for suspected vulnerabilities. Do not open a public Issue, put exploit
details in a pull request, or include credentials and private data in public
comments. A reproducible report should identify the affected version or
commit, describe the impact briefly, and use reproduction steps that contain
no secrets.

## Public maintenance controls

The repository uses layered safeguards:

- Dependabot alerts and security updates for dependency vulnerabilities;
- locked-environment auditing and `pip-audit` in CI;
- secret scanning and push protection where supported by the repository plan;
- CodeQL Default setup for Python and GitHub Actions, using the default query
  suite on standard GitHub-hosted runners;
- protected `main` with required CI and security checks, resolved review
  conversations, linear history, and an independent approval when a second
  maintainer is available. A single-maintainer repository uses the public
  Review 1 / Review 2 protocol instead of self-approval or an admin bypass.

These controls complement one another. A passing check does not replace
maintainer review, and a new alert is reviewed before it is resolved or
classified.

## Plan and implement changes safely

Security and dependency work is tracked in a public Issue before substantial
changes begin. The Issue records scope, non-goals, acceptance criteria, and
public-safe residual risk; the linked pull request records implementation
status and validation evidence. Maintainers use a requirements/risk review
and a complete-diff/verification review before merging.

Contributors should keep workflow permissions least-privileged, avoid secrets
in pull-request jobs, preserve full action references, and disclose only the
configuration and evidence needed to review the change.
