#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CATALOG_PATH="${1:-}"
OUTPUT_DIR="${2:-}"

if [[ -z "$CATALOG_PATH" || -z "$OUTPUT_DIR" ]]; then
  echo "Usage: docs/multiversions.sh CATALOG_JSON OUTPUT_DIR" >&2
  echo "Use a validated catalog and an output directory outside the checkout." >&2
  exit 2
fi

cd "$REPO_ROOT"
exec python -m tools.maintenance.build_docs_site \
  --repo-root "$REPO_ROOT" \
  --catalog "$CATALOG_PATH" \
  --output "$OUTPUT_DIR"
