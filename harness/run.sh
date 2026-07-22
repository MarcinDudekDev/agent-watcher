#!/usr/bin/env bash
# Thin wrapper: ./harness/run.sh [--watcher on|off] [--model sonnet] [--id NAME]
set -euo pipefail
exec python3 "$(dirname "$0")/run.py" "$@"
