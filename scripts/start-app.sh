#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
API_BIND_HOST=${API_BIND_HOST:-127.0.0.1}
API_PUBLIC_HOST=${API_PUBLIC_HOST:-127.0.0.1}
API_PORT=${API_PORT:-8787}
UI_HOST=${UI_HOST:-127.0.0.1}
UI_PORT=${UI_PORT:-5173}
VITE_API_BASE=${VITE_API_BASE:-http://${API_PUBLIC_HOST}:${API_PORT}}
API_HEALTH_URL=${API_HEALTH_URL:-http://${API_PUBLIC_HOST}:${API_PORT}/api/health}
API_AUTH_MODE=${DIGEST_WEB_API_AUTH_MODE:-required}
API_TOKEN=${DIGEST_WEB_API_TOKEN:-}
API_TOKEN_HEADER=${DIGEST_WEB_API_TOKEN_HEADER:-X-Digest-Api-Token}
API_LOG=${API_LOG:-${ROOT_DIR}/.runtime/app-api.log}
UI_LOG=${UI_LOG:-${ROOT_DIR}/.runtime/app-ui.log}
API_PID=""
UI_PID=""

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf "Missing required command: %s\n" "$1" >&2
    exit 1
  fi
}

generate_token() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 24
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    python3 - <<'PY'
import secrets
print(secrets.token_hex(24))
PY
    return
  fi
  date +%s | tr -d '\n'
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

if [ "${API_AUTH_MODE}" = "required" ] && [ -z "${API_TOKEN}" ]; then
  API_TOKEN=$(generate_token)
  printf "Generated local API auth token for this session.\n"
fi

printf "Starting API at http://%s:%s (bind=%s) ...\n" "${API_PUBLIC_HOST}" "${API_PORT}" "${API_BIND_HOST}"
if command -v uv >/dev/null 2>&1; then
  (
    cd "${ROOT_DIR}"
    DIGEST_WEB_API_AUTH_MODE="${API_AUTH_MODE}" \
    DIGEST_WEB_API_TOKEN="${API_TOKEN}" \
    DIGEST_WEB_API_TOKEN_HEADER="${API_TOKEN_HEADER}" \
    uv run digest \
      --sources config/sources.yaml \
      --sources-overlay data/sources.local.yaml \
      --profile config/profile.yaml \
      --profile-overlay data/profile.local.yaml \
      --db digest-live.db \
      web --host "${API_BIND_HOST}" --port "${API_PORT}" >>"${API_LOG}" 2>&1
  ) &
else
  (
    cd "${ROOT_DIR}"
    DIGEST_WEB_API_AUTH_MODE="${API_AUTH_MODE}" \
    DIGEST_WEB_API_TOKEN="${API_TOKEN}" \
    DIGEST_WEB_API_TOKEN_HEADER="${API_TOKEN_HEADER}" \
    PYTHONPATH=src ./bin/digest \
      --sources config/sources.yaml \
      --sources-overlay data/sources.local.yaml \
      --profile config/profile.yaml \
      --profile-overlay data/profile.local.yaml \
      --db digest-live.db \
      web --host "${API_BIND_HOST}" --port "${API_PORT}" >>"${API_LOG}" 2>&1
  ) &
fi
API_PID=$!

READY=0
ATTEMPT=0
while [ "${ATTEMPT}" -lt 80 ]; do
  if curl -fsS "${API_HEALTH_URL}" >/dev/null 2>&1; then
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
  printf "API did not become healthy in time (%s).\n" "${API_HEALTH_URL}" >&2
  printf "See API log: %s\n" "${API_LOG}" >&2
  exit 1
fi

printf "API is ready.\n"
printf "Starting UI at http://%s:%s ...\n" "${UI_HOST}" "${UI_PORT}"
printf "Tip: Press Ctrl+C to stop both API and UI.\n"

(
  cd "${ROOT_DIR}/web"
  VITE_API_BASE="${VITE_API_BASE}" \
  VITE_DEV_API_PROXY_TARGET="http://${API_PUBLIC_HOST}:${API_PORT}" \
  VITE_WEB_API_TOKEN="${API_TOKEN}" \
  VITE_WEB_API_TOKEN_HEADER="${API_TOKEN_HEADER}" \
  ./node_modules/.bin/vite --host "${UI_HOST}" --port "${UI_PORT}" --strictPort >>"${UI_LOG}" 2>&1
) &
UI_PID=$!

sleep 1
if ! kill -0 "${UI_PID}" >/dev/null 2>&1; then
  printf "UI failed to start. See UI log: %s\n" "${UI_LOG}" >&2
  exit 1
fi

printf "API log: %s\n" "${API_LOG}"
printf "UI log: %s\n" "${UI_LOG}"

wait "${UI_PID}"
