#!/bin/bash

OUTPUT_DIR="_build/html"

echo "Building documentation for main (dev)"
MAIN_WORKTREE=".worktree-main"

# Create a detached worktree for the main branch
git worktree add --detach "$MAIN_WORKTREE" main

# Navigate to the docs/ directory within the worktree
cd "$MAIN_WORKTREE"/docs || exit 1

# Replace only the __version__ line with 'dev'
sed -i "s/^__version__ = .*/__version__ = 'dev'/" ../gsplot/version.py

# Check the content of ../gsplot/version.py
cat ../gsplot/version.py

# Build the documentation for the main branch
sphinx-build . "../../$OUTPUT_DIR/dev"

# Return to the original directory
cd - || exit 1

# Remove the main branch worktree
git worktree remove "$MAIN_WORKTREE" --force

# Build documentation for each tag
TAGS=$(git tag)
for TAG in $TAGS; do
  echo "Building documentation for tag: $TAG"
  WORKTREE_DIR=".worktree-$TAG"

  # Create a detached worktree for the tag
  git worktree add --detach "$WORKTREE_DIR" "$TAG"

  # Navigate to the docs/ directory within the worktree
  cd "$WORKTREE_DIR"/docs || exit 1

  # Build the documentation for the tag
  sphinx-build . "../../$OUTPUT_DIR/$TAG"

  # Return to the original directory
  cd - || exit 1

  # Remove the tag worktree
  git worktree remove "$WORKTREE_DIR" --force
done

echo "Documentation build complete. Output available in $OUTPUT_DIR."
