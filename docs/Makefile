# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
PYTHON        ?= python
SOURCEDIR     = .
BUILDDIR      = _build
CATALOG       ?=
SITE_OUTPUT   ?=

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Clean target: remove the generated files
clean:
	@echo "Removing generated files..."
	rm -rf $(BUILDDIR)/html $(BUILDDIR)/doctrees

# Clear target: clean all build artifacts, including doctrees and cache
clear:
	@echo "Removing all build artifacts..."
	rm -rf $(BUILDDIR)

# Autobuild target: run sphinx-autobuild with specific options
autobuild:
	sphinx-autobuild "$(SOURCEDIR)" "$(BUILDDIR)/html" --watch "../src/gsplot" --watch "../examples" --watch "reference" --watch "api_reference" --host 127.0.0.1 -d "$(BUILDDIR)/doctrees" --pre-build "make clean html" --ignore "$(BUILDDIR)/*" --re-ignore "^\..*" --re-ignore "__pycache__" --re-ignore "\.DS_Store" --re-ignore "./api_reference/apis" --re-ignore "./api_reference/apis.rst"

# Run all example scripts explicitly. The Sphinx configuration also performs this
# step for normal builds so that generated image assets are never stale.
build-images:
	cd .. && MPLBACKEND=Agg $(PYTHON) -m tools.maintenance.build_example_images

# Multiversion target: thin compatibility wrapper around the repository tool.
multiversion:
	@test -n "$(CATALOG)" || (echo "Set CATALOG to a validated catalog JSON path." >&2; exit 2)
	@test -n "$(SITE_OUTPUT)" || (echo "Set SITE_OUTPUT outside the checkout." >&2; exit 2)
	PYTHONPATH=.. $(PYTHON) -m tools.maintenance.build_docs_site --repo-root .. --catalog "$(CATALOG)" --output "$(SITE_OUTPUT)"

html-dev-deploy:
	@echo "Building HTML documentation..."
	MPLBACKEND=Agg $(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html"

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
