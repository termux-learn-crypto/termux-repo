#!/data/data/com.termux/files/usr/bin/bash
set -u
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
export TMPDIR="${TMPDIR:-$PREFIX/tmp}"
export ANDROID_API_LEVEL="${ANDROID_API_LEVEL:-$(getprop ro.build.version.sdk 2>/dev/null || echo 24)}"
export CARGO_BUILD_TARGET="${CARGO_BUILD_TARGET:-aarch64-linux-android}" CARGO_BUILD_JOBS="${CARGO_BUILD_JOBS:-2}" MAKEFLAGS=-j2
export CFLAGS="${CFLAGS:-} -I$PREFIX/include" LDFLAGS="${LDFLAGS:-} -L$PREFIX/lib"
if python -c 'import accelerate' >/dev/null 2>&1 && [ "${FORCE_REINSTALL:-0}" != 1 ]; then
  echo "[+] accelerate already installed"
  exit 0
fi
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock || true
unlock() { command -v termux-wake-unlock >/dev/null 2>&1 && termux-wake-unlock || true; }
echo "[*] Installing accelerate (pure wheel; safetensors already built has Rust if missing)..."
python -m pip install --no-cache-dir --prefer-binary "safetensors>=0.4.3" accelerate || { unlock; echo "[x] accelerate install failed"; exit 1; }
unlock
echo "[*] Verifying..."
accelerate-check
