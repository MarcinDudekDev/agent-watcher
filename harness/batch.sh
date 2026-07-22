#!/usr/bin/env bash
# Run one arm of the experiment: N passes at the current commit, C at a time.
#
#   harness/batch.sh <arm> <watcher> <n> [concurrency]
#   harness/batch.sh seeded off 8
#   harness/batch.sh control on 8 4
#
# Run ids are <short-sha>-<arm><watcher>-<i>, so a result can never be read
# without knowing which committed state produced it.
set -euo pipefail
cd "$(dirname "$0")/.."

arm="${1:?arm: seeded|control}"
watcher="${2:?watcher: on|off}"
n="${3:?number of runs}"
concurrency="${4:-3}"

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "refusing to measure a dirty tree: commit first, results attach to a SHA" >&2
  exit 1
fi

sha="$(git rev-parse --short HEAD)"
logs="${WATCHER_EVAL_LOGS:-$HOME/claude-tmp/watcher-eval/logs}"
mkdir -p "$logs"
echo "arm=$arm watcher=$watcher n=$n at $sha -> $logs"

pids=()
for i in $(seq 1 "$n"); do
  id="$sha-$arm$watcher-$i"
  python3 harness/run.py --arm "$arm" --watcher "$watcher" --id "$id" \
    --model sonnet --max-turns 400 --timeout 5400 > "$logs/$id.log" 2>&1 &
  pids+=($!)
  if (( ${#pids[@]} >= concurrency )); then
    wait "${pids[0]}" || echo "run failed (continuing): ${pids[0]}" >&2
    pids=("${pids[@]:1}")
  fi
done
for pid in "${pids[@]}"; do
  wait "$pid" || echo "run failed (continuing): $pid" >&2
done

echo "arm $arm/$watcher complete at $sha"
