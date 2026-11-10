#!/data/data/com.termux/files/usr/bin/bash
set -u
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
GLIBCPY="${GLIBC_PYTHON:-$PREFIX/glibc/bin/python3}"
GRUN="$PREFIX/bin/grun"
TF_VERSION="${TF_VERSION:-}"
export TMPDIR="${TMPDIR:-$PREFIX/tmp}"
if [ "${FORCE_REINSTALL:-0}" != 1 ] && "$GRUN" "$GLIBCPY" -m pip show tensorflow >/dev/null 2>&1; then
  echo "[+] tensorflow already installed"
  exit 0
fi
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock || true
unlock() { command -v termux-wake-unlock >/dev/null 2>&1 && termux-wake-unlock || true; }
[ -x "$GRUN" ] || { unlock; echo "[x] grun missing - run: apt install glibc-runner"; exit 1; }
[ -x "$GLIBCPY" ] || { unlock; echo "[x] glibc python missing - run: apt install python-glibc python-pip-glibc"; exit 1; }
if [ -n "$TF_VERSION" ]; then
  SPEC="tensorflow==$TF_VERSION"
else
  SPEC="tensorflow"
fi
echo "[*] Installing $SPEC into glibc python (one ~300 MB wheel + deps, slow on a phone). Charge pe rakho."
"$GRUN" "$GLIBCPY" -m pip install "$SPEC" || { unlock; echo "[x] tensorflow install failed"; exit 1; }
unlock
echo "[*] Verifying..."
tensorflow-check
