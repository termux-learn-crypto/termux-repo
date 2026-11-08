#!/data/data/com.termux/files/usr/bin/bash
# Builds PyAudio against Termux portaudio. Dependencies come from apt (Depends).
set -u
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
export CC="${CC:-clang}" CFLAGS="${CFLAGS:-} -I$PREFIX/include" CPPFLAGS="${CPPFLAGS:-} -I$PREFIX/include" \
       LDFLAGS="${LDFLAGS:-} -L$PREFIX/lib" PKG_CONFIG_PATH="$PREFIX/lib/pkgconfig" TMPDIR="${TMPDIR:-$PREFIX/tmp}"
if python -c 'import pyaudio' >/dev/null 2>&1 && [ "${FORCE_REBUILD:-0}" != 1 ]; then
  echo "[+] PyAudio already installed"; exit 0
fi
echo "[*] Building PyAudio (~1 min)..."
python -m pip install --no-cache-dir --no-binary pyaudio pyaudio \
 || { python -m pip install --no-cache-dir setuptools wheel >/dev/null 2>&1; \
      python -m pip install --no-cache-dir --no-build-isolation --no-binary pyaudio pyaudio; } || exit 1
python -c 'import pyaudio; print("[+] PyAudio", pyaudio.__version__, "|", pyaudio.get_portaudio_version_text())'
