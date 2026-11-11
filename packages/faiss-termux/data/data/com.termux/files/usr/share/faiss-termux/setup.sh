#!/data/data/com.termux/files/usr/bin/bash
set -u
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
GLIBCPY="${GLIBC_PYTHON:-$PREFIX/glibc/bin/python3}"
GRUN="$PREFIX/bin/grun"
FAISS_VERSION="${FAISS_VERSION:-}"
export TMPDIR="${TMPDIR:-$PREFIX/tmp}"
if [ "${FORCE_REINSTALL:-0}" != 1 ] && "$GRUN" "$GLIBCPY" -m pip show faiss-cpu >/dev/null 2>&1; then
  echo "[+] faiss-cpu already installed"
  exit 0
fi
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock || true
unlock() { command -v termux-wake-unlock >/dev/null 2>&1 && termux-wake-unlock || true; }
[ -x "$GRUN" ] || { unlock; echo "[x] grun missing - run: apt install glibc-runner"; exit 1; }
[ -x "$GLIBCPY" ] || { unlock; echo "[x] glibc python missing - run: apt install python-glibc python-pip-glibc"; exit 1; }
if [ -n "$FAISS_VERSION" ]; then
  SPEC="faiss-cpu==$FAISS_VERSION"
else
  SPEC="faiss-cpu"
fi
echo "[*] Installing $SPEC into glibc python (~10 MB) ..."
"$GRUN" "$GLIBCPY" -m pip install --no-cache-dir --prefer-binary "$SPEC" || { unlock; echo "[x] faiss-cpu install failed"; exit 1; }
unlock
echo "[*] Verifying..."
faiss-check
