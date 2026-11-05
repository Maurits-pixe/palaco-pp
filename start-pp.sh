#!/bin/sh
# Run with: sh start-pp.sh
set -eu
pp_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Python ontbreekt. Installeer Python 3.11 of hoger.' >&2
  exit 1
fi
exec python3 "$pp_root/start_pp.py" "$@"
