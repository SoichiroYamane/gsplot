# Set up gsplot for development

This guide describes the supported local development workflow. The repository
uses Poetry for dependency resolution and targets Python 3.10 or newer. Python
3.12 is recommended for the locked development environment and for CI.

```{important}
Use a virtual environment and run plotting tests with `MPLBACKEND=Agg` on
headless machines. Do not commit `.venv`, build output, example images, or local
`.gsplot` metadata.
```

## 1. Fork and clone

Fork [the repository on GitHub](https://github.com/SoichiroYamane/gsplot), then
clone your fork:

```bash
git clone https://github.com/<your-account>/gsplot.git
cd gsplot
git remote add upstream git@github.com:SoichiroYamane/gsplot.git
```

## 2. Poetry environment

Install [Poetry](https://python-poetry.org/docs/) 2.4.1 and select a compatible
interpreter:

```bash
python -m pip install "poetry==2.4.1"
poetry env use python3.12
poetry install
```

Run commands inside the environment with `poetry run`; there is no need to
activate a shell:

```bash
MPLBACKEND=Agg poetry run pytest -q
poetry run black --check src/gsplot tests examples tools/maintenance
poetry run isort --check-only src/gsplot tests examples tools/maintenance
poetry run pyright src/gsplot
poetry run pip-audit --local
```

## 3. Install only the package locally

If you need an editable runtime install without the full development group,
create a virtual environment and install the package with pip:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

The Poetry workflow is preferred when running tests, type checkers, or docs
because those tools are development dependencies.

## 4. Docker (optional)

The repository includes a Compose service for users who prefer an isolated
Linux environment. Start it from the repository root:

```bash
docker compose up --build -d
docker compose exec gsplot bash
cd /root/opt
MPLBACKEND=Agg poetry run pytest -q
```

Interactive GUI plots require a host display configuration. For headless CI or
documentation builds, use the `Agg` backend and do not rely on an X11 display.

## 5. Run an example

Example scripts use paths relative to their own directories. Run them from the
matching semantic directory:

```bash
cd examples/publication
MPLBACKEND=Agg python publication.py
```

The example writes its figures next to the script. PNG and PDF output are
intentionally ignored by Git. From the repository root, validate the manifest
and rebuild every example with:

```bash
MPLBACKEND=Agg poetry run python -m tools.maintenance.build_example_images
```

## 6. Build documentation and the package

The Sphinx configuration runs example scripts to refresh image assets. Build the
HTML site with:

```bash
MPLBACKEND=Agg poetry run sphinx-build -b html docs docs/_build/html
```

For a strict CI-equivalent build, treat warnings as errors:

```bash
MPLBACKEND=Agg poetry run sphinx-build -W -b html docs docs/_build/html
```

Build distribution artifacts without publishing them:

```bash
poetry check --lock
poetry build
python tools/maintenance/check_dist.py dist
```

The artifact checker validates the exact wheel and source-distribution
contents, metadata, record hashes, path safety, and size limits without
extracting either archive. CI and the publishing workflow additionally install
the wheel in a clean environment outside the checkout and run
`tools/maintenance/smoke_dist.py` before accepting the artifact.

Check that the complete reviewed API and compatibility fixture still matches
the runtime:

```bash
PYTHONPATH=src poetry run python \
  tools/maintenance/check_public_api_contract.py
```

An intentional API change requires the same command with `--update`, followed
by review of the complete JSON diff.

For a performance-sensitive reform, compare two already reviewed commits from
a clean tracked working tree:

```bash
poetry run python tools/maintenance/benchmark_reform.py \
  --baseline 782117f --candidate HEAD
```

The benchmark executes both revisions, including their examples, from isolated
temporary exports with a credential-free process environment. Inspect any
commit before selecting it: a benchmark is not a sandbox for untrusted code.
The JSON contains aggregate medians and generic toolchain information only. A
nonzero `investigate` result must be fixed or explicitly accepted in the
linked Issue with its cause and residual impact.

Before submitting a change, also run:

```bash
python -m compileall -q src/gsplot tests examples tools/maintenance
PYTHONPATH=src poetry run python tools/maintenance/check_architecture.py
PYTHONPATH=src poetry run python tools/maintenance/check_docstrings.py
git diff --check
git status --short
```
