#!/data/data/com.termux/files/usr/bin/bash
set -u
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
export TMPDIR="${TMPDIR:-$PREFIX/tmp}"
if python -c 'import peft, accelerate' >/dev/null 2>&1 && [ "${FORCE_REINSTALL:-0}" != 1 ]; then
  echo "[+] peft already installed"
  exit 0
fi
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock || true
unlock() { command -v termux-wake-unlock >/dev/null 2>&1 && termux-wake-unlock || true; }
# transformers-termux normally does this; do it here too if it was skipped
if ! python -c 'import transformers' >/dev/null 2>&1; then
  echo "[*] transformers missing — installing it first (safetensors compiles with Rust, ~5-15 min)..."
  export ANDROID_API_LEVEL="$(getprop ro.build.version.sdk 2>/dev/null || echo 24)"
  export CARGO_BUILD_TARGET=aarch64-linux-android CARGO_BUILD_JOBS="${CARGO_BUILD_JOBS:-2}" MAKEFLAGS=-j2
  export CFLAGS="${CFLAGS:-} -I$PREFIX/include" LDFLAGS="${LDFLAGS:-} -L$PREFIX/lib"
  python -m pip install --no-cache-dir --prefer-binary safetensors regex pyyaml "huggingface_hub" tqdm requests packaging filelock || { unlock; echo "[x] deps install failed"; exit 1; }
  python -m pip install --no-cache-dir --no-deps "transformers>=5,<6" || { unlock; echo "[x] transformers install failed"; exit 1; }
fi
echo "[*] Installing accelerate + peft..."
python -m pip install --no-cache-dir --prefer-binary "accelerate>=0.21.0" || { unlock; echo "[x] accelerate install failed"; exit 1; }
python -m pip install --no-cache-dir --prefer-binary --no-deps peft || { unlock; echo "[x] peft install failed"; exit 1; }
unlock
echo "[*] Verifying..."
peft-check
