#!/usr/bin/env bash
set -euo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# shellcheck disable=SC1091
source .venv/bin/activate

export DEMO_AUTH_REQUIRED="${DEMO_AUTH_REQUIRED:-true}"
export PUBLIC_PASSWORD="${PUBLIC_PASSWORD:-demo}"
export ADMIN_PASSWORD="${ADMIN_PASSWORD:-302@Labs}"
export VITE_API_BASE_URL=http://127.0.0.1:8001

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  if [[ -n "${FRONTEND_PID}" ]] && kill -0 "${FRONTEND_PID}" 2>/dev/null; then
    kill "${FRONTEND_PID}" 2>/dev/null || true
    wait "${FRONTEND_PID}" 2>/dev/null || true
  fi
  if [[ -n "${BACKEND_PID}" ]] && kill -0 "${BACKEND_PID}" 2>/dev/null; then
    kill "${BACKEND_PID}" 2>/dev/null || true
    wait "${BACKEND_PID}" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

echo "Starting backend (uvicorn) on 127.0.0.1:8001..."
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload &
BACKEND_PID=$!

echo "Waiting for backend health..."
for i in $(seq 1 60); do
  if curl -sf "http://127.0.0.1:8001/api/v1/health" >/dev/null 2>&1; then
    echo "Backend is healthy."
    break
  fi
  if ! kill -0 "${BACKEND_PID}" 2>/dev/null; then
    echo "Backend process exited unexpectedly." >&2
    exit 1
  fi
  if [[ "$i" -eq 60 ]]; then
    echo "Timed out waiting for /api/v1/health" >&2
    exit 1
  fi
  sleep 1
done

echo "Starting frontend (Vite) on 127.0.0.1:5173..."
(cd frontend && npm run dev -- --port 5173 --host 127.0.0.1) &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "  Arabic Editorial Proofreading (demo)"
echo "========================================"
echo "  Frontend:   http://127.0.0.1:5173"
echo "  API:        http://127.0.0.1:8001"
echo "  Health:     http://127.0.0.1:8001/api/v1/health"
echo "  Admin logs: http://127.0.0.1:5173/admin/logs"
echo ""
echo "  Login hints:"
echo "    Public password: ${PUBLIC_PASSWORD}"
echo "    Admin password:  ${ADMIN_PASSWORD}"
echo "    DEMO_AUTH_REQUIRED=${DEMO_AUTH_REQUIRED}"
echo "========================================"
echo "Press Ctrl+C to stop."
echo ""

wait
