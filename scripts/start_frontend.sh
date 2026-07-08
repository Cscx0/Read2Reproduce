#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../frontend"

if command -v npm >/dev/null 2>&1; then
  npm run dev -- --host 127.0.0.1
elif command -v pnpm >/dev/null 2>&1; then
  pnpm run dev -- --host 127.0.0.1
else
  echo "Neither npm nor pnpm was found in PATH." >&2
  exit 1
fi
