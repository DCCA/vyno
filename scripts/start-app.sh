#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
API_HOST=${API_HOST:-127.0.0.1}
API_PORT=${API_PORT:-8787}
UI_HOST=${UI_HOST:-127.0.0.1}
UI_PORT=${UI_PORT:-5173}
VITE_API_BASE=${VITE_API_BASE:-http://${API_HOST}:${API_PORT}}
API_PID=""
UI_PID=""

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf "Missing required command: %s\n" "$1" >&2
    exit 1
  fi
}

cleanup() {
  if [ -n "${UI_PID}" ] && kill -0 "${UI_PID}" >/dev/null 2>&1; then
    kill "${UI_PID}" >/dev/null 2>&1 || true
    wait "${UI_PID}" >/dev/null 2>&1 || true
  fi
  if [ -n "${API_PID}" ] && kill -0 "${API_PID}" >/dev/null 2>&1; then
    kill "${API_PID}" >/dev/null 2>&1 || true
    wait "${API_PID}" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

require_cmd curl
require_cmd npm

if ! command -v uv >/dev/null 2>&1 && [ ! -x "${ROOT_DIR}/bin/digest" ]; then
  printf "Missing runtime launcher: install uv or make %s executable.\n" "${ROOT_DIR}/bin/digest" >&2
  exit 1
fi

mkdir -p "${ROOT_DIR}/logs" "${ROOT_DIR}/.runtime"

if [ ! -d "${ROOT_DIR}/web/node_modules" ]; then
  printf "Installing web dependencies...\n"
  npm --prefix "${ROOT_DIR}/web" install
fi

printf "Starting API at http://%s:%s ...\n" "${API_HOST}" "${API_PORT}"
if command -v uv >/dev/null 2>&1; then
  (
    cd "${ROOT_DIR}"
    uv run digest \
      --sources config/sources.yaml \
      --sources-overlay data/sources.local.yaml \
      --profile config/profile.yaml \
      --profile-overlay data/profile.local.yaml \
      --db digest-live.db \
      web --host "${API_HOST}" --port "${API_PORT}" >/dev/null 2>&1
  ) &
else
  (
    cd "${ROOT_DIR}"
    PYTHONPATH=src ./bin/digest \
      --sources config/sources.yaml \
      --sources-overlay data/sources.local.yaml \
      --profile config/profile.yaml \
      --profile-overlay data/profile.local.yaml \
      --db digest-live.db \
      web --host "${API_HOST}" --port "${API_PORT}" >/dev/null 2>&1
  ) &
fi
API_PID=$!

READY=0
ATTEMPT=0
while [ "${ATTEMPT}" -lt 80 ]; do
  if curl -fsS "http://${API_HOST}:${API_PORT}/api/health" >/dev/null 2>&1; then
    READY=1
    break
  fi
  if ! kill -0 "${API_PID}" >/dev/null 2>&1; then
    printf "API exited before becoming ready.\n" >&2
    exit 1
  fi
  ATTEMPT=$((ATTEMPT + 1))
  sleep 0.25
done

if [ "${READY}" -ne 1 ]; then
  printf "API did not become healthy in time (http://%s:%s/api/health).\n" "${API_HOST}" "${API_PORT}" >&2
  exit 1
fi

printf "API is ready.\n"
printf "Starting UI at http://%s:%s ...\n" "${UI_HOST}" "${UI_PORT}"
printf "Tip: Press Ctrl+C to stop both API and UI.\n"

(
  cd "${ROOT_DIR}/web"
  VITE_API_BASE="${VITE_API_BASE}" ./node_modules/.bin/vite --host "${UI_HOST}" --port "${UI_PORT}"
) &
UI_PID=$!

wait "${UI_PID}"
