#!/data/data/com.termux/files/usr/bin/bash
# VoiceStudio setup. System packages come from apt (Depends); this does the rest.
# Safe to re-run: updates the checkout and skips what is installed.
set -euo pipefail
REPO_URL="${VS_REPO_URL:-https://github.com/termux-learn-crypto/VoiceStudio.git}"
BRANCH="${VS_BRANCH:-termux}"
APP_DIR="${VS_DIR:-$HOME/VoiceStudio}"
WEBUI_URL="${VS_WEBUI_URL:-https://github.com/termux-learn-crypto/VoiceStudio/releases/download/termux-webui/voicestudio-webui.tar.gz}"
say()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m[!] %s\033[0m\n' "$*"; }

python -c 'import torch' 2>/dev/null || { echo "[x] torch missing: pkg install python-torch python-torchaudio"; exit 1; }

export MATHLIB=m
export CFLAGS="${CFLAGS:-} -Wno-error=incompatible-function-pointer-types"
export LDFLAGS="${LDFLAGS:-} -lm"
export ANDROID_API_LEVEL="$(getprop ro.build.version.sdk 2>/dev/null || echo 24)"
export CARGO_BUILD_TARGET=aarch64-linux-android
export CARGO_BUILD_JOBS="${CARGO_BUILD_JOBS:-2}"
export MAKEFLAGS="-j2"

say "Getting VoiceStudio ($BRANCH) into $APP_DIR"
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" fetch --depth 1 origin "$BRANCH"
  git -C "$APP_DIR" checkout -q -B "$BRANCH" FETCH_HEAD
else
  GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR"

say "Python venv"
[ -d .venv-termux ] || python -m venv --system-site-packages .venv-termux
. .venv-termux/bin/activate
pip install -q --upgrade pip wheel

say "Python requirements"
if ! python -c 'import pydantic_core' 2>/dev/null; then
  warn "pydantic-core compiles with Rust: 10-25 min lagenge. Phone charge pe rakho, Termux band mat karo."
  command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock || true
fi
pip install --prefer-binary -r termux/requirements-termux.txt
pip install --prefer-binary --no-deps "huggingface_hub>=1.7"

say "Light TTS engine (Supertonic, ONNX)"
if python -c 'import onnxruntime' 2>/dev/null; then
  pip install --prefer-binary --no-deps "supertonic>=1.3" && echo "  + supertonic"
else
  warn "onnxruntime missing (pkg install python-onnxruntime); light engines disabled."
fi

say "Web UI"
if [ ! -f frontend/dist/index.html ]; then
  mkdir -p frontend/dist
  curl -fsSL "$WEBUI_URL" | tar xz -C frontend/dist && echo "  + web UI" || warn "Web UI download failed; API still runs (/docs)."
fi
chmod +x termux/run.sh
mkdir -p "$HOME/.shortcuts" 2>/dev/null && ln -sf "$APP_DIR/termux/run.sh" "$HOME/.shortcuts/VoiceStudio" 2>/dev/null || true
command -v termux-wake-unlock >/dev/null 2>&1 && termux-wake-unlock || true
say "VoiceStudio ready. Start: voicestudio  ->  http://127.0.0.1:3900"
