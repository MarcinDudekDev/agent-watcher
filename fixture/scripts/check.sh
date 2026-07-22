#!/usr/bin/env bash
# Static checks. Ruff is optional; skipped when it is not installed.
set -u
cd "$(dirname "$0")/.."

status=0

if command -v ruff >/dev/null 2>&1; then
  ruff check shiftlog tests || status=1
else
  echo "check: ruff not installed, skipping lint"
fi

python3 -c "import ast,sys,pathlib
bad=0
for p in list(pathlib.Path('shiftlog').rglob('*.py'))+list(pathlib.Path('tests').rglob('*.py')):
    try: ast.parse(p.read_text())
    except SyntaxError as e:
        print(f'check: syntax error in {p}: {e}'); bad=1
sys.exit(bad)" || status=1

if [ "$status" -eq 0 ]; then echo "check: ok"; fi
exit "$status"
