#!/bin/bash

OUTPUT_DIR="_build/html"

echo "Building documentation for main (dev)"
MAIN_WORKTREE=".worktree-main"

# Remove existing worktree-main directory if it exists
rm -rf "$MAIN_WORKTREE"

# Create the destination directory for the worktree
mkdir -p "$MAIN_WORKTREE"

# Use rsync to copy the parent directory (one level up) to the worktree
rsync -a --exclude "$MAIN_WORKTREE" --exclude ".git" ../ "$MAIN_WORKTREE/"

# Navigate to the copied directory
cd "$MAIN_WORKTREE" || exit 1

# Check if gsplot/version.py exists
if [ ! -f "gsplot/version.py" ]; then
  echo "Error: gsplot/version.py does not exist in $MAIN_WORKTREE."
  exit 1
fi

# Replace only the __version__ line with 'dev'
sed -i "s/^__version__ = .*/__version__ = 'dev'/" gsplot/version.py

# Check the content of gsplot/version.py
cat gsplot/version.py

# Navigate to the docs directory
if [ ! -d "docs" ]; then
  echo "Error: docs directory does not exist in $MAIN_WORKTREE."
  exit 1
fi
cd docs || exit 1

# Build the documentation for the main branch
sphinx-build . "../../_build/html/dev"

# Return to the original directory
cd ../.. || exit 1

# Remove the main branch worktree
rm -rf "$MAIN_WORKTREE"

# Build documentation for each tag
# TAGS=$(git tag)
VERSIONS_FILE="versions"

# Check if the versions file exists
if [ ! -f "$VERSIONS_FILE" ]; then
  echo "Error: Versions file '$VERSIONS_FILE' not found."
  exit 1
fi

# Read versions from the file
TAGS=$(cat "$VERSIONS_FILE")
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
