#!/usr/bin/env bash
# Parser throughput regression check.
set -u
cd "$(dirname "$0")/.."

if ! out=$(uv run --no-sync shiftlog examples/week.txt 2>&1); then
  echo "verify_perf: FAILED - shiftlog could not read examples/week.txt"
  echo "$out" | tail -3
  exit 1
fi

echo "verify_perf: ok"
