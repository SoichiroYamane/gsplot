# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SPHINXMULTI   ?= sphinx-multiversion
SOURCEDIR     = .
BUILDDIR      = _build

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
	sphinx-autobuild "$(SOURCEDIR)" "$(BUILDDIR)/html" --watch "../gsplot" --watch "reference" --watch "api_reference" --host 0.0.0.0 -d "$(BUILDDIR)/doctrees" --pre-build "make clean html" --ignore "$(BUILDDIR)/*" --re-ignore "^\..*" --re-ignore "__pycache__" --re-ignore "\.DS_Store" --re-ignore "./api_reference/apis" --re-ignore "./api_reference/apis.rst"

# Multiversion target: build documentation for multiple versions
multiversion:
	$(SPHINXMULTI) "$(SOURCEDIR)" "$(BUILDDIR)/html"

html-dev-deploy:
	@echo "Setting __version__ to 'dev' in gsplot/version.py"
	sed -i "s/^__version__ = .*/__version__ = 'dev'/" gsplot/version.py
	@echo "Building HTML documentation..."
	$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html"

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
