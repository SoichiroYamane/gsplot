## Summary

Describe the user-visible outcome and link the durable goal:

<!-- Closes #000 -->

Current status: <!-- Draft, blocked, ready for review, or awaiting decision. -->

Keep the durable requirements and acceptance criteria in the linked Issue.

## Changed surfaces

- [ ] Public Python API or behavior
- [ ] Configuration or global Matplotlib state
- [ ] Tests or demos
- [ ] Documentation or examples
- [ ] Dependencies, packaging, or generated artifacts
- [ ] CI or repository guidance

List the affected files or contracts and explain any intentional breaking
change or migration path.

## Validation

List exact commands and results. Do not mark skipped checks as passing.

- [ ] Focused tests
- [ ] Full test suite
- [ ] Formatting, types, and syntax
- [ ] Documentation and demos
- [ ] Packaging or lockfile checks

## Security and supply chain

Explain dependency provenance, workflow permissions, generated-file changes,
secret handling, and any advisory or residual risk. Do not include credentials,
private paths, raw logs, or unreleased vulnerability details.

## Blockers and next action

Record reproducible blockers, residual risks, and the next decision needed for
review. Keep chronological scratch notes outside the repository.

The Draft PR is the active progress record. Update this section and the
validation section as the implementation changes.

## Review checklist

- [ ] The linked Issue contains scope and acceptance criteria.
- [ ] The complete diff and generated files were manually reviewed.
- [ ] Public imports, configuration precedence, docs, demos, and packaging are coherent.
- [ ] No secrets or private operational details are present.
- [ ] Remote approval, merge, release, or publish actions are not assumed.
