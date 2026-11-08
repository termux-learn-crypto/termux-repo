#!/data/data/com.termux/files/usr/bin/bash
set -u
if python -c 'import transformers, safetensors' >/dev/null 2>&1 && [ "${FORCE_REBUILD:-0}" != 1 ]; then echo "[+] transformers already installed"; exit 0; fi
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
export ANDROID_API_LEVEL="$(getprop ro.build.version.sdk 2>/dev/null || echo 24)"
export CARGO_BUILD_TARGET=aarch64-linux-android CARGO_BUILD_JOBS="${CARGO_BUILD_JOBS:-2}" MAKEFLAGS=-j2 \
       CFLAGS="${CFLAGS:-} -I$PREFIX/include" LDFLAGS="${LDFLAGS:-} -L$PREFIX/lib" TMPDIR="${TMPDIR:-$PREFIX/tmp}"
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock || true
echo "[*] Installing transformers (safetensors compiles with Rust, ~5-15 min)..."
# tokenizers + torch come from apt; keep pip from replacing them
python -m pip install --no-cache-dir --prefer-binary safetensors regex pyyaml "huggingface_hub" tqdm requests packaging filelock || { termux-wake-unlock 2>/dev/null; exit 1; }
python -m pip install --no-cache-dir --no-deps "transformers>=5,<6" || { termux-wake-unlock 2>/dev/null; exit 1; }
command -v termux-wake-unlock >/dev/null 2>&1 && termux-wake-unlock || true
python -c 'import transformers; print("[+] transformers", transformers.__version__)'
