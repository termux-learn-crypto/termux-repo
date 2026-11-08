#!/data/data/com.termux/files/usr/bin/bash
set -u
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
export CFLAGS="${CFLAGS:-} -I$PREFIX/include" LDFLAGS="${LDFLAGS:-} -L$PREFIX/lib" MAKEFLAGS=-j2 NPY_NUM_BUILD_JOBS=2 TMPDIR="${TMPDIR:-$PREFIX/tmp}"
if python -c 'import librosa' >/dev/null 2>&1 && [ "${FORCE_REBUILD:-0}" != 1 ]; then echo "[+] librosa already installed"; exit 0; fi
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock || true
unlock() { command -v termux-wake-unlock >/dev/null 2>&1 && termux-wake-unlock || true; }
if ! python -c 'import numba' >/dev/null 2>&1; then
  echo "[*] Building numba (10-20 min, uses Termux llvmlite). Phone charge pe rakho."
  python -m pip install --no-cache-dir -q setuptools wheel
  python -m pip install --no-cache-dir --no-build-isolation numba || { unlock; echo "[x] numba build failed"; exit 1; }
fi
echo "[*] Installing librosa..."
python -m pip install --no-cache-dir joblib "decorator>=5.2.1" pooch lazy_loader platformdirs requests packaging typing-extensions || { unlock; exit 1; }
python -m pip install --no-cache-dir --no-deps librosa || { unlock; exit 1; }
unlock
python -c 'import librosa; print("[+] librosa", librosa.__version__)'
