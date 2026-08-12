# Build the versioned website

The repository-owned Python orchestrator is the source of truth for a
multi-version documentation build. `docs/multiversions.sh` and the Make
multiversion target are compatibility wrappers only; they must not be used by
deployment workflows.

## Generate a local fixture catalog

Catalog generation can run without GitHub access or credentials by using the
tracked fixture:

```bash
poetry run python -m tools.maintenance.build_docs_catalog \
  --repo-root . \
  --fixture tests/fixtures/docs_site/releases.json \
  --output /tmp/gsplot-catalog.json \
  --switcher-output /tmp/gsplot-switcher.json \
  --base-url https://example.test/gsplot
```

The live catalog job reads public GitHub Release metadata and writes the same
schema. It does not execute release source code.

## Build the site outside the checkout

The site builder creates detached worktrees and isolated cache/home
directories, imports each historical package from its own source tree, and
promotes the complete site only after all versions pass validation. Keep the
output outside the repository because the builder intentionally replaces that
explicit directory:

```bash
poetry run python -m tools.maintenance.build_docs_site \
  --repo-root . \
  --catalog /tmp/gsplot-catalog.json \
  --output /tmp/gsplot-site
```

The result contains `dev/`, one immutable directory per included release,
`stable/`, and public-safe `_meta/catalog.json` and
`_meta/build-manifest.json` files. The manifest records source commits,
package provenance, generated paths, output checks, exclusions, and artifact
size. A failed version removes the temporary worktree and does not publish a
partial output tree.

The builder uses the pinned Poetry documentation environment and an explicit
source-path compatibility strategy for historical packages. It never passes
GitHub, Pages, PyPI, OIDC, or repository-write credentials to release source,
demo, or Sphinx processes.
