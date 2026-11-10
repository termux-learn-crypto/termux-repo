#!/data/data/com.termux/files/usr/bin/bash
set -u
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
GLIBCPY="${GLIBC_PYTHON:-$PREFIX/glibc/bin/python3}"
GRUN="$PREFIX/bin/grun"
BNB_VERSION="${BNB_VERSION:-}"
export TMPDIR="${TMPDIR:-$PREFIX/tmp}"
if [ "${FORCE_REINSTALL:-0}" != 1 ] && "$GRUN" "$GLIBCPY" -m pip show bitsandbytes >/dev/null 2>&1; then
  echo "[+] bitsandbytes already installed"
  exit 0
fi
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock || true
unlock() { command -v termux-wake-unlock >/dev/null 2>&1 && termux-wake-unlock || true; }
[ -x "$GRUN" ] || { unlock; echo "[x] grun missing - run: apt install glibc-runner"; exit 1; }
[ -x "$GLIBCPY" ] || { unlock; echo "[x] glibc python missing - run: apt install python-glibc python-pip-glibc"; exit 1; }
if [ -n "$BNB_VERSION" ]; then
  SPEC="bitsandbytes==$BNB_VERSION"
else
  SPEC="bitsandbytes"
fi
echo "[*] Installing torch (CPU, ~480 MB) + $SPEC into glibc python ..."
echo "[*] Slow connection pe ye 30-60 min le sakta hai. Charge pe rakho."
"$GRUN" "$GLIBCPY" -m pip install --no-cache-dir --prefer-binary torch || { unlock; echo "[x] torch install failed"; exit 1; }
"$GRUN" "$GLIBCPY" -m pip install --no-cache-dir --prefer-binary "$SPEC" || { unlock; echo "[x] bitsandbytes install failed"; exit 1; }
unlock
echo "[*] Verifying..."
bnb-check
