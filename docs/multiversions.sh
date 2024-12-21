#!/bin/bash

# Directory to store the build artifacts
OUTPUT_DIR="docs/_build/html"

# Build documentation for the main branch as "dev"
echo "Building documentation for main (dev)"
git checkout main
sphinx-build . "$OUTPUT_DIR/dev"

# Get all tags
TAGS=$(git tag)

# Process each tag
for TAG in $TAGS; do
  echo "Building documentation for tag: $TAG"

  # Checkout the tag and create a temporary branch
  git checkout tags/$TAG -b build-$TAG

  # Build the documentation for the tag
  sphinx-build . "$OUTPUT_DIR/$TAG"

  # Delete the temporary branch and switch back to main
  git checkout main
  git branch -D build-$TAG
done

echo "Documentation build complete. Output available in $OUTPUT_DIR."
