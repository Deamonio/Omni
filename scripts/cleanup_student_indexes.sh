#!/usr/bin/env bash
set -euo pipefail
BASE="/home/rai/deamon/Omni/students"
MODE="${1:-apply}"
[[ -d "$BASE" ]] || { echo "students directory not found: $BASE" >&2; exit 1; }
count=0
while IFS= read -r -d '' f; do
  ((count++))
  if [[ "$MODE" == "--dry-run" ]]; then
    echo "[DRY] $f"
  else
    rm -f "$f"
    echo "[DEL] $f"
  fi
done < <(find "$BASE" -mindepth 2 -maxdepth 2 -type f -name "index.html" -print0)
echo "done. files: $count"
