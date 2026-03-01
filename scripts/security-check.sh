#!/usr/bin/env sh
set -eu

MODE=${1:-local}
ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf "Missing required command: %s\n" "$1" >&2
    exit 1
  fi
}

run_detect_secrets() {
  if [ ! -f "${ROOT_DIR}/.secrets.baseline" ]; then
    printf "Missing .secrets.baseline; generate it before running security checks.\n" >&2
    exit 1
  fi

  printf "[security] detect-secrets baseline check...\n"
  # shellcheck disable=SC2046
  uvx --from detect-secrets detect-secrets-hook --baseline "${ROOT_DIR}/.secrets.baseline" $(git ls-files)
}

run_bandit() {
  printf "[security] bandit high-severity scan...\n"
  uvx --from bandit bandit -q -r "${ROOT_DIR}/src" -lll
}

run_ruff_policy() {
  printf "[security] ruff syntax/runtime checks...\n"
  uvx --from ruff ruff check "${ROOT_DIR}/src" "${ROOT_DIR}/tests" --select E9,F63,F7,F82
}

run_semgrep_advisory() {
  printf "[security] semgrep advisory scan...\n"
  uvx --from semgrep semgrep scan \
    --config p/secrets \
    --config p/python \
    --exclude "${ROOT_DIR}/.venv" \
    --exclude "${ROOT_DIR}/web/node_modules" \
    "${ROOT_DIR}/src" "${ROOT_DIR}/tests"
}

require_cmd git
require_cmd uvx

cd "${ROOT_DIR}"
run_detect_secrets
run_bandit
run_ruff_policy

if [ "${MODE}" = "extended" ]; then
  run_semgrep_advisory
fi

printf "[security] checks completed (%s mode).\n" "${MODE}"
