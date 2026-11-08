#!/data/data/com.termux/files/usr/bin/bash
set -u
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
export CFLAGS="${CFLAGS:-} -I$PREFIX/include" LDFLAGS="${LDFLAGS:-} -L$PREFIX/lib" TMPDIR="${TMPDIR:-$PREFIX/tmp}"
if ! python -c 'import soundfile' >/dev/null 2>&1 || [ "${FORCE_REBUILD:-0}" = 1 ]; then
  echo "[*] Installing cffi + soundfile..."
  python -m pip install --no-cache-dir cffi typing-extensions || exit 1
  python -m pip install --no-cache-dir --no-deps soundfile || exit 1
fi
# Termux patch: find libsndfile on Android
python - <<'PY'
import importlib.util, re
spec = importlib.util.find_spec("soundfile"); p = spec.origin
s = open(p).read()
if "TERMUX-PATCH" not in s:
    s = s.replace("elif _sys.platform == 'linux':", "elif _sys.platform in ('linux', 'android'):  # TERMUX-PATCH", 1)
    s = s.replace("_libname = _find_library('sndfile')",
                  "_libname = _find_library('sndfile') or (__import__('os').environ.get('PREFIX', '/data/data/com.termux/files/usr') + '/lib/libsndfile.so')  # TERMUX-PATCH", 1)
    open(p, "w").write(s); print("[+] patched", p)
PY
python -c 'import soundfile as sf; print("[+] soundfile", sf.__version__, "| libsndfile", sf.__libsndfile_version__)'
