#!/data/data/com.termux/files/usr/bin/bash
set -u
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
export TMPDIR="${TMPDIR:-$PREFIX/tmp}"
# pydantic-core (via typer from transformers) compiles with Rust too and needs the API level
export ANDROID_API_LEVEL="${ANDROID_API_LEVEL:-$(getprop ro.build.version.sdk 2>/dev/null || echo 24)}"
export CARGO_BUILD_TARGET="${CARGO_BUILD_TARGET:-aarch64-linux-android}" CARGO_BUILD_JOBS="${CARGO_BUILD_JOBS:-2}" MAKEFLAGS=-j2
export CFLAGS="${CFLAGS:-} -I$PREFIX/include" LDFLAGS="${LDFLAGS:-} -L$PREFIX/lib"
if python -c 'import trl, datasets' >/dev/null 2>&1 && [ "${FORCE_REINSTALL:-0}" != 1 ]; then
  echo "[+] trl already installed"
  exit 0
fi
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock || true
unlock() { command -v termux-wake-unlock >/dev/null 2>&1 && termux-wake-unlock || true; }
echo "[*] Installing datasets + trl (pip) ..."
python -m pip install --no-cache-dir --prefer-binary datasets trl || { unlock; echo "[x] trl install failed"; exit 1; }
unlock
echo "[*] Verifying..."
trl-check
