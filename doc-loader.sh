#!/usr/bin/env bash
# Usage: ./doc-loader.sh <extract|transform|load> [arguments]
# Runs the chosen stage with the project's Python environment.
set -euo pipefail
cd "$(dirname "$0")"

stage="${1:-}"
if [[ -z "$stage" || ! -f "src/$stage/$stage.py" ]]; then
  echo "Usage: ./doc-loader.sh <extract|transform|load> [arguments]" >&2
  exit 1
fi
shift

if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi

exec .venv/bin/python "src/$stage/$stage.py" "$@"
