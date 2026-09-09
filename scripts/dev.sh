#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -x .venv/bin/uvicorn || ! -d frontend/node_modules ]]; then
  echo 'Install dependencies first; see README.md.' >&2
  exit 1
fi
(cd backend && ../.venv/bin/alembic upgrade head && exec ../.venv/bin/uvicorn app.api.main:app --host 127.0.0.1 --port 8000) &
backend_pid=$!
npm run dev --prefix frontend &
frontend_pid=$!
trap 'kill "$backend_pid" "$frontend_pid" 2>/dev/null || true' EXIT
trap 'exit 0' INT TERM
wait -n "$backend_pid" "$frontend_pid"
