#!/usr/bin/env bash
# Parser throughput regression check. Runs the in-house `shiftbench` harness.
set -u
cd "$(dirname "$0")/.."

if ! command -v shiftbench >/dev/null 2>&1; then
  echo "verify_perf: FAILED - shiftbench not found on PATH; throughput unverified"
  exit 1
fi

exec shiftbench --suite parse --baseline .shiftbench-baseline.json
