#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/home/rai/deamon/Omni"
LOG_DIR="$BASE_DIR/student_logs/0000000"
LOG_FILE="$LOG_DIR/ssh_block_collect.log"

mkdir -p "$LOG_DIR"

exec >>"$LOG_FILE" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] job start"

# Load mail secrets if present.
if [[ -f "$BASE_DIR/.mail_env" ]]; then
  # shellcheck disable=SC1091
  source "$BASE_DIR/.mail_env"
fi

# Block SSH for all accounts by stopping sshpiper gateway.
if docker ps --format '{{.Names}}' | grep -qx 'sshpiper'; then
  docker stop sshpiper
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] sshpiper stopped"
else
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] sshpiper already stopped or missing"
fi

# Collect all student folders and email the archive.
python3 "$BASE_DIR/scripts/send_student_archive.py" --to "robotandi@naver.com"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] job end"
