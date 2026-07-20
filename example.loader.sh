#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_BIN="$VENV_DIR/bin/python"

if [ ! -x "$PYTHON_BIN" ]; then
  echo "Virtualenv not found at $VENV_DIR" >&2
  exit 1
fi

if ! "$PYTHON_BIN" "$ROOT_DIR/healthcheck.py" --host 127.0.0.1 --port 25121 >/dev/null 2>&1; then
  echo "Starting d3v-skyman"
  nohup "$PYTHON_BIN" "$ROOT_DIR/d3vskyman.py" > "$ROOT_DIR/d3vskyman.log" 2>&1 &
fi

echo "d3v-skyman is running or was started successfully"