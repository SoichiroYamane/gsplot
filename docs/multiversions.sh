#!/bin/bash

# Define the directory containing conf.py
DOCS_DIR="docs"

# Build documentation for the main branch
echo "Building documentation for main (dev)"
git checkout main
poetry run sphinx-build -c "$DOCS_DIR" "$DOCS_DIR" "$DOCS_DIR/_build/html/dev"

# Get all tags
TAGS=$(git tag)

# Loop through each tag and build documentation
for TAG in $TAGS; do
  echo "Building documentation for tag: $TAG"

  # Create a new branch for the tag
  git checkout "$TAG" -b "build-$TAG"

  # Build the documentation
  poetry run sphinx-build -c "$DOCS_DIR" "$DOCS_DIR" "$DOCS_DIR/_build/html/$TAG"

  # Return to the main branch and delete the temporary branch
  git checkout main
  git branch -D "build-$TAG"
done
