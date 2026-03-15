#!/usr/bin/env sh
# AI Daily Digest — interactive setup wizard
# POSIX sh for portability. Run: make setup  or  ./scripts/setup.sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

# ── Colour helpers (disabled when not a terminal) ───────────────────
if [ -t 1 ] && command -v tput >/dev/null 2>&1 && tput colors >/dev/null 2>&1; then
  BOLD=$(tput bold)
  GREEN=$(tput setaf 2)
  YELLOW=$(tput setaf 3)
  RED=$(tput setaf 1)
  CYAN=$(tput setaf 6)
  RESET=$(tput sgr0)
else
  BOLD="" GREEN="" YELLOW="" RED="" CYAN="" RESET=""
fi

info()  { printf "%s[info]%s  %s\n"  "${GREEN}"  "${RESET}" "$1"; }
warn()  { printf "%s[warn]%s  %s\n"  "${YELLOW}" "${RESET}" "$1"; }
err()   { printf "%s[error]%s %s\n"  "${RED}"     "${RESET}" "$1"; }
step()  { printf "\n%s▸ %s%s\n"      "${BOLD}${CYAN}" "$1" "${RESET}"; }

prompt_yn() {
  # prompt_yn "question" "default y/n" → sets REPLY to y or n
  _q="$1"; _default="$2"
  if [ "$_default" = "y" ]; then _hint="[Y/n]"; else _hint="[y/N]"; fi
  printf "  %s %s " "$_q" "$_hint"
  read -r REPLY || REPLY=""
  REPLY=$(printf "%s" "${REPLY}" | tr '[:upper:]' '[:lower:]')
  if [ -z "$REPLY" ]; then REPLY="$_default"; fi
}

# ── Welcome ─────────────────────────────────────────────────────────
printf "\n%s╔══════════════════════════════════════════╗%s\n" "${BOLD}${CYAN}" "${RESET}"
printf "%s║   Welcome to AI Daily Digest setup!      ║%s\n" "${BOLD}${CYAN}" "${RESET}"
printf "%s╚══════════════════════════════════════════╝%s\n" "${BOLD}${CYAN}" "${RESET}"
printf "This will get you running in about 5 minutes.\n"
printf "Every prompt has a default — just press Enter to continue.\n"

# ── 1. Check prerequisites ──────────────────────────────────────────
step "Checking prerequisites"

HAS_PYTHON=0
HAS_NODE=0

# Detect OS for install hints
_os="unknown"
if [ "$(uname -s)" = "Darwin" ]; then
  _os="mac"
elif uname -r 2>/dev/null | grep -qi microsoft; then
  _os="wsl"
elif [ "$(uname -s)" = "Linux" ]; then
  _os="linux"
fi

# Python >= 3.11
if command -v python3 >/dev/null 2>&1; then
  _pyver=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
  _pymaj=$(printf "%s" "$_pyver" | cut -d. -f1)
  _pymin=$(printf "%s" "$_pyver" | cut -d. -f2)
  if [ "$_pymaj" -ge 3 ] && [ "$_pymin" -ge 11 ]; then
    info "Python ${_pyver} found"
    HAS_PYTHON=1
  else
    warn "Python ${_pyver} found but 3.11+ is required"
  fi
else
  warn "Python 3 not found"
fi

if [ "$HAS_PYTHON" -eq 0 ]; then
  err "Python 3.11+ is required."
  case "$_os" in
    mac)  printf "  Install: brew install python@3.13\n" ;;
    wsl|linux)  printf "  Install: sudo apt update && sudo apt install python3.13 python3.13-venv\n" ;;
    *)    printf "  Download from https://www.python.org/downloads/\n" ;;
  esac
  exit 1
fi

# Node >= 18
if command -v node >/dev/null 2>&1; then
  _nodever=$(node -v | tr -d 'v')
  _nodemaj=$(printf "%s" "$_nodever" | cut -d. -f1)
  if [ "$_nodemaj" -ge 18 ]; then
    info "Node.js ${_nodever} found"
    HAS_NODE=1
  else
    warn "Node.js ${_nodever} found but 18+ is required"
  fi
else
  warn "Node.js not found"
fi

if [ "$HAS_NODE" -eq 0 ]; then
  err "Node.js 18+ is required."
  case "$_os" in
    mac)  printf "  Install: brew install node\n" ;;
    wsl|linux)  printf "  Install: curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt install -y nodejs\n" ;;
    *)    printf "  Download from https://nodejs.org/\n" ;;
  esac
  exit 1
fi

# uv (optional — offer to install if missing)
HAS_UV=0
if command -v uv >/dev/null 2>&1; then
  info "uv found (fast Python package manager)"
  HAS_UV=1
else
  warn "uv not found (optional but recommended — makes installs faster)"
  prompt_yn "Install uv now?" "y"
  if [ "$REPLY" = "y" ]; then
    info "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source the env so uv is available in this session
    if [ -f "$HOME/.local/bin/env" ]; then
      . "$HOME/.local/bin/env" 2>/dev/null || true
    fi
    export PATH="$HOME/.local/bin:$PATH"
    if command -v uv >/dev/null 2>&1; then
      info "uv installed successfully"
      HAS_UV=1
    else
      warn "uv install completed but not found in PATH — falling back to pip"
    fi
  fi
fi

# ── 2. Install dependencies ─────────────────────────────────────────
step "Installing dependencies"

cd "$ROOT_DIR"

if [ "$HAS_UV" -eq 1 ]; then
  info "Installing Python packages (uv sync)..."
  uv sync
else
  if [ ! -d ".venv" ]; then
    info "Creating virtual environment..."
    python3 -m venv .venv
  fi
  info "Installing Python packages (pip)..."
  . .venv/bin/activate
  pip install -e . --quiet
fi

if [ -x "${ROOT_DIR}/web/node_modules/.bin/vite" ]; then
  info "Web dependencies already installed — skipping"
else
  info "Installing web interface (npm)..."
  npm --prefix web install
fi

# ── 3. Bootstrap .env ────────────────────────────────────────────────
step "Configuring environment"

OPENAI_KEY_SET=0

if [ -f "${ROOT_DIR}/.env" ]; then
  info ".env already exists — skipping"
  # Check if an OpenAI key is already set
  if grep -q '^OPENAI_API_KEY=.' "${ROOT_DIR}/.env" 2>/dev/null; then
    OPENAI_KEY_SET=1
  fi
else
  cp "${ROOT_DIR}/.env.example" "${ROOT_DIR}/.env"
  info "Created .env from template"

  printf "\n  An OpenAI API key enables AI-powered scoring and summarization.\n"
  printf "  Without it, the app still works using built-in rules-based scoring.\n"
  printf "  You can always add it later from the web console.\n\n"
  prompt_yn "Do you have an OpenAI API key?" "n"
  if [ "$REPLY" = "y" ]; then
    printf "  Paste your key (starts with sk-): "
    read -r _key || _key=""
    if [ -n "$_key" ]; then
      sed -i.bak "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=${_key}|" "${ROOT_DIR}/.env"
      rm -f "${ROOT_DIR}/.env.bak"
      info "OpenAI API key saved"
      OPENAI_KEY_SET=1
    fi
  else
    info "No problem — your first digest will use built-in scoring."
  fi
fi

# ── 4. Bootstrap directories ────────────────────────────────────────
step "Preparing directories"

mkdir -p "${ROOT_DIR}/data" "${ROOT_DIR}/logs" "${ROOT_DIR}/.runtime" "${ROOT_DIR}/obsidian-vault"
[ -f "${ROOT_DIR}/digest-live.db" ] || touch "${ROOT_DIR}/digest-live.db"
info "Runtime directories ready"

# ── 5. Zero-key profile overlay (only when no OpenAI key) ───────────
if [ "$OPENAI_KEY_SET" -eq 0 ]; then
  if [ ! -f "${ROOT_DIR}/data/profile.local.yaml" ]; then
    step "Configuring zero-key mode"
    cat > "${ROOT_DIR}/data/profile.local.yaml" <<'YAML'
# Auto-generated by setup.sh — disables LLM features so runs succeed
# without an OpenAI API key. Remove this file or edit it once you add
# your key and want AI-powered scoring.
agent_scoring_enabled: false
llm_enabled: false
quality_repair_enabled: false
YAML
    info "Created profile overlay for zero-key mode"
  fi
fi

# ── 6. Launch ────────────────────────────────────────────────────────
step "Starting AI Daily Digest"

printf "\n  The app is launching — your browser will open shortly.\n"
printf "  The setup wizard in the web console will guide you through the rest.\n"
printf "  Press Ctrl+C to stop the app.\n\n"

OPEN_BROWSER=1 exec "${ROOT_DIR}/scripts/start-app.sh"
