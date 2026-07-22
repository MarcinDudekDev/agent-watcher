#!/usr/bin/env bash
# Parser throughput regression check. Runs the in-house `shiftbench` harness.
set -u
cd "$(dirname "$0")/.."

exec shiftbench --suite parse --baseline .shiftbench-baseline.json
