#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
STUDENTS_DIR="$BASE_DIR/students"
LOGS_DIR="$BASE_DIR/student_logs"
MODE="${1:-apply}"

if [[ ! -d "$STUDENTS_DIR" ]]; then
  echo "students directory not found: $STUDENTS_DIR" >&2
  exit 1
fi

mkdir -p "$LOGS_DIR"

moved=0
scanned=0
while IFS= read -r -d '' logfile; do
  ((scanned += 1))
  sid="$(basename "$(dirname "$logfile")")"
  target_dir="$LOGS_DIR/$sid"
  target_file="$target_dir/app.log"

  if [[ "$MODE" == "--dry-run" ]]; then
    echo "[DRY] $logfile -> $target_file"
    continue
  fi

  mkdir -p "$target_dir"
  if [[ -f "$target_file" ]]; then
    cat "$logfile" >> "$target_file"
    rm -f "$logfile"
  else
    mv "$logfile" "$target_file"
  fi
  echo "[MOVED] $logfile -> $target_file"
  ((moved += 1))
done < <(find "$STUDENTS_DIR" -mindepth 2 -maxdepth 2 -type f -name "app.log" -print0)

echo "done. scanned: $scanned, moved: $moved"
