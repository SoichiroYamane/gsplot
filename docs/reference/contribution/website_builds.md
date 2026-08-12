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
  --output /tmp/gsplot-site \
  --base-url https://example.test/gsplot
```

The result contains `dev/`, one immutable directory per included release,
`stable/`, and public-safe `_meta/catalog.json`, `_meta/switcher.json`, and
`_meta/build-manifest.json` files. The switcher is generated and validated
from the same catalog as the build matrix. The manifest records source
commits, package provenance, generated paths, output checks, exclusions, and
artifact size. The artifact size is the file count and uncompressed and
deterministic per-file compressed byte totals; the manifest file itself is
excluded so recording its size cannot change the recorded budget. A failed
version removes the temporary worktree and does not publish a partial output
tree.

The final site has a small root entry, a custom `404.html`, `robots.txt`, and
an immutable-release sitemap. Existing root HTML routes are generated as
no-JavaScript compatibility pages pointing into `/dev/`. Root assets are
copied from the selected stable release before channel cleanup, while source
copies, demo media, build caches, and extension-generated runtime data are
removed from version directories. The small set of inventoried legacy asset
paths is retained only at the root and is never used as a build input.

The builder uses the pinned Poetry documentation environment and an explicit
source-path compatibility strategy for historical packages. It never passes
GitHub, Pages, PyPI, OIDC, or repository-write credentials to release source,
demo, or Sphinx processes. Historical Mermaid directives are rendered to SVG
at build time with the pinned `mmdc` CLI; the published HTML does not load a
Mermaid or other documentation runtime from a CDN. Historical source is still
built with warnings as errors; only the documented legacy `docutils` warning
category is isolated in the temporary compatibility overlay. A full local
catalog build therefore requires a compatible `mmdc` executable on `PATH`.

## Workflow boundaries

`.github/workflows/gh-pages-sphinx.yml` has four independently permissioned
jobs:

1. `catalog` reads the public GitHub Releases API and uploads only the typed
   catalog and switcher. Pull requests use the tracked fixture and do not need
   GitHub API access. A workflow-dispatch `candidate_tag` may add an existing
   unpublished tag for a build-only release-candidate check.
2. `build` downloads the catalog artifact, checks out `main` and all tags,
   installs the locked Poetry and npm toolchains, and builds outside the
   checkout. It receives no GitHub, Pages, PyPI, or OIDC credential.
3. `deploy` receives only Pages write and OIDC identity permissions and runs
   only for a published catalog, never for a pull request or candidate build.
4. `smoke` downloads the public-safe catalog and manifest and performs bounded
   read-only HTTP checks for the deployed root, aliases, immutable pages,
   metadata, representative assets, crawler files, and custom 404 response.

The catalog job also compares the candidate release set with the previously
published `_meta/build-manifest.json`. An immutable release cannot disappear
without a reviewed entry in `website-release-policy.json`. The artifact
baseline records the first clean build's file count and deterministic
compressed/uncompressed sizes; a later build fails when any metric grows by
more than 20% without a baseline update and linked review.

The old `docs/multiversions.sh` and Make target are thin wrappers around the
same orchestrator and require an explicit catalog and output path. They do not
read the historical `docs/versions` list and are not used by CI or deployment.
