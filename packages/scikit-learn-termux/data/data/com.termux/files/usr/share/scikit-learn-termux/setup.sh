#!/data/data/com.termux/files/usr/bin/bash
set -u
if python -c 'import sklearn' >/dev/null 2>&1 && [ "${FORCE_REBUILD:-0}" != 1 ]; then echo "[+] scikit-learn already installed"; exit 0; fi
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
export MATHLIB=m LDFLAGS="${LDFLAGS:-} -lm -L$PREFIX/lib" CFLAGS="${CFLAGS:-} -I$PREFIX/include" \
       NPY_NUM_BUILD_JOBS=2 MAKEFLAGS=-j2 TMPDIR="${TMPDIR:-$PREFIX/tmp}"
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock || true
echo "[*] Building scikit-learn (20-40 min). Phone charge pe rakho, Termux band mat karo."
python -m pip install --no-cache-dir -q "cython>=3" meson-python meson joblib threadpoolctl || exit 1
python -m pip install --no-cache-dir --no-build-isolation scikit-learn -Csetup-args=-Dopenmp=disabled \
  || python -m pip install --no-cache-dir --no-build-isolation scikit-learn || { termux-wake-unlock 2>/dev/null; exit 1; }
command -v termux-wake-unlock >/dev/null 2>&1 && termux-wake-unlock || true
python -c 'import sklearn; print("[+] scikit-learn", sklearn.__version__)'
