# Website compatibility inventory

This document is the pre-cutover route inventory for the versioned website
delivery work tracked in [Issue #174](https://github.com/SoichiroYamane/gsplot/issues/174).
It is a compatibility contract, not a generated sitemap. The first migration
must preserve these routes or provide the explicit target shown below.

## Canonical targets

| Existing route family | First-cutover target | Compatibility rule |
| --- | --- | --- |
| `/` and `/index.html` | `/` | Keep a small no-JavaScript landing page. Its stable link targets `/stable/`. |
| Root HTML pages such as `/api_reference/index.html` | `/dev/<same path>` | Keep a no-JavaScript HTML redirect page at the old path. The target must resolve. |
| Root assets such as `/_static/*` and `/_images/*` | `/dev/<same path>` | Keep a compatibility copy when an old page or external consumer requests the asset directly. Do not replace an image or script with HTML. |
| `/stable/` and `/stable/<existing path>` | `/stable/<same path>` | Keep the stable alias and its existing `.html` paths, but update the copied source to the selected immutable release. |
| `/v0.1.1/` through `/v0.2.0/` | `/v0.1.1/` through `/v0.2.0/` | Preserve existing version directories and `.html` pages. |
| New `/vX.Y.Z/` release paths | `/vX.Y.Z/` | Build only from the catalog commit SHA and publish only after the complete version succeeds. |
| `/dev/` and `/dev/<path>` | `/dev/<same path>` | Build from the selected `main` commit and mark the HTML `noindex`. |

The redirect files must be relative-path safe, work with JavaScript disabled,
and be covered by the route smoke test. A compatibility page may use a
canonical link and a visible link in addition to its meta refresh, but it must
not depend on client-side JavaScript.

## Observed pre-cutover root routes

The following routes returned HTTP 200 from the published root during the
inventory pass on 2026-08-12. The list includes the root page's linked
documentation pages and assets; external links are intentionally omitted.

### Documentation pages

- `/`
- `/index.html`
- `/api_reference/index.html`
- `/guides/index.html`
- `/guides/demo/index.html`
- `/guides/start/getting_started.html`
- `/project/api-migration.html`
- `/project/reform-baseline.html`
- `/project/requirements.html`
- `/reference/index.html`
- `/genindex.html`
- `/search.html`

### Generated data and assets

- `/searchindex.js`
- `/_sources/index.md.txt`
- `/_images/SC_cal.png`
- `/_static/logo_gsplot.svg`
- `/_static/logo/logo_title_gsplot.png`
- `/_static/clipboard.min.js`
- `/_static/copybutton.css`
- `/_static/copybutton.js`
- `/_static/design-tabs.js`
- `/_static/doctools.js`
- `/_static/documentation_options.js`
- `/_static/language_data.js`
- `/_static/pygments.css`
- `/_static/scripts/bootstrap.js`
- `/_static/scripts/fontawesome.js`
- `/_static/scripts/pydata-sphinx-theme.js`
- `/_static/searchtools.js`
- `/_static/sphinx-design.min.css`
- `/_static/sphinx_highlight.js`
- `/_static/styles/pydata-sphinx-theme.css`
- `/_static/styles/theme.css`
- `/_static/tippy/index.e4541f43-c3c4-4f8e-910e-1cc2b87bf3db.js`
- `/_static/togglebutton.css`
- `/_static/togglebutton.js`

The inventory is intentionally limited to routes observed from the published
root entry. The implementation must also derive and test the complete source
HTML and asset route set before changing the root layout; a newly discovered
route is a compatibility failure until it has an approved target.

## Verification rules

Before cutover, the website checks must:

1. fetch every inventory route and record its status and content type;
2. build the compatibility target with JavaScript disabled;
3. verify every preserved version path and existing `.html` page;
4. verify the root entry, stable alias, dev tree, and every generated redirect;
5. fail if a route silently falls back to a stale version or a GitHub Pages
   custom 404 document.

The compatibility inventory is updated in the same pull request as any
intentional route removal, with a public Issue or PR reference explaining the
decision.
