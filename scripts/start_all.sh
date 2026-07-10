#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  trap - EXIT INT TERM

  for pid in "$BACKEND_PID" "$FRONTEND_PID"; do
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done

  for pid in "$BACKEND_PID" "$FRONTEND_PID"; do
    if [ -n "$pid" ]; then
      wait "$pid" 2>/dev/null || true
    fi
  done
}

trap cleanup EXIT
trap 'exit 130' INT TERM

"$ROOT_DIR/scripts/start_backend.sh" &
BACKEND_PID=$!

"$ROOT_DIR/scripts/start_frontend.sh" &
FRONTEND_PID=$!

echo "Read2Reproduce is starting:"
echo "  frontend  http://127.0.0.1:5173"
echo "  backend   http://127.0.0.1:8000"
echo "Press Ctrl+C to stop both services."

while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$FRONTEND_PID" 2>/dev/null; do
  sleep 1
done

set +e
if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
  wait "$BACKEND_PID"
  status=$?
  echo "Backend stopped (exit $status)." >&2
else
  wait "$FRONTEND_PID"
  status=$?
  echo "Frontend stopped (exit $status)." >&2
fi
set -e

exit "$status"
