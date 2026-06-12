#!/usr/bin/env sh
set -eu

PROJECT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
python3 "$PROJECT_DIR/build/generate.py" --target 7500 --project "$PROJECT_DIR"
