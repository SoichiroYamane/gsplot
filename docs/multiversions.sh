#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/_build/html"
MAIN_WORKTREE="$REPO_ROOT/.worktree-main"

run_sphinx() {
  local source_dir="$1"
  local output_dir="$2"
  python -c '
import multiprocessing as mp
import sys

try:
    mp.set_start_method("fork")
except (AttributeError, RuntimeError):
    pass

from sphinx.cmd.build import main

sys.exit(main())
' "$source_dir" "$output_dir"
}

cd "$REPO_ROOT"
mkdir -p "$OUTPUT_DIR"

echo "Building documentation for main (dev)"
rm -rf "$MAIN_WORKTREE"
rsync -a --exclude=".git" --exclude=".worktree-*" "$REPO_ROOT/" "$MAIN_WORKTREE/"

sed -i "s/^__version__ = .*/__version__ = 'dev'/" \
  "$MAIN_WORKTREE/gsplot/version.py"
(
  cd "$MAIN_WORKTREE/docs"
  MPLBACKEND=Agg run_sphinx . "$OUTPUT_DIR/dev"
)
rm -rf "$MAIN_WORKTREE"

if [[ ! -f "$SCRIPT_DIR/versions" ]]; then
  echo "Error: versions file not found at $SCRIPT_DIR/versions" >&2
  exit 1
fi

while IFS= read -r tag; do
  [[ -z "$tag" ]] && continue
  echo "Building documentation for tag: $tag"
  worktree_dir="$REPO_ROOT/.worktree-$tag"
  rm -rf "$worktree_dir"
  git worktree add --detach "$worktree_dir" "$tag"
  (
    cd "$worktree_dir/docs"
    MPLBACKEND=Agg run_sphinx . "$OUTPUT_DIR/$tag"
  )
  git worktree remove "$worktree_dir" --force
done < "$SCRIPT_DIR/versions"

echo "Documentation build complete. Output available at $OUTPUT_DIR."
