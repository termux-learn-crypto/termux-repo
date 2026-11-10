#!/data/data/com.termux/files/usr/bin/bash
set -u
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
export TMPDIR="${TMPDIR:-$PREFIX/tmp}"
if python -c 'import datasets' >/dev/null 2>&1 && [ "${FORCE_REINSTALL:-0}" != 1 ]; then
  echo "[+] datasets already installed"
  exit 0
fi
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock || true
unlock() { command -v termux-wake-unlock >/dev/null 2>&1 && termux-wake-unlock || true; }
echo "[*] Installing datasets (pip, small downloads)..."
python -m pip install --no-cache-dir --prefer-binary datasets || { unlock; echo "[x] datasets install failed"; exit 1; }
unlock
echo "[*] Verifying..."
datasets-check
