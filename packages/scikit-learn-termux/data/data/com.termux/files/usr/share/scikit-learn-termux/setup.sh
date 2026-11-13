#!/data/data/com.termux/files/usr/bin/bash
set -u
if python -c 'import sklearn' >/dev/null 2>&1 && [ "${FORCE_REBUILD:-0}" != 1 ]; then echo "[+] scikit-learn already installed"; exit 0; fi
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
SK_VER="${SK_VER:-1.9.1}"
export MATHLIB=m LDFLAGS="${LDFLAGS:-} -lm -L$PREFIX/lib" CFLAGS="${CFLAGS:-} -I$PREFIX/include" \
       NPY_NUM_BUILD_JOBS=2 MAKEFLAGS=-j2 TMPDIR="${TMPDIR:-$PREFIX/tmp}"
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock || true
echo "[*] Building scikit-learn $SK_VER (20-40 min). Phone charge pe rakho, Termux band mat karo."
python -m pip install --no-cache-dir -q "cython>=3" meson-python meson joblib threadpoolctl || { command -v termux-wake-unlock >/dev/null 2>&1 && termux-wake-unlock; exit 1; }
# pip ka sdist seedha install nahi hota: PyPI sdist ke build scripts #!/usr/bin/env shebang
# use karte hain, aur Termux me /usr/bin/env nahi hota (meson: "Could not execute command version.py").
# Isliye sdist download karke shebang patch karke install karte hain.
# Note: -Dopenmp=disabled hataya — sklearn >= 1.9 me ye option exist nahi karta (meson: Unknown option).
WORK="$PREFIX/tmp/scikit-learn-build.$$"
mkdir -p "$WORK" || exit 1
python - "$SK_VER" "$WORK" <<'PY' || { rm -rf "$WORK"; command -v termux-wake-unlock >/dev/null 2>&1 && termux-wake-unlock; exit 1; }
import json, os, sys, urllib.request
ver, work = sys.argv[1], sys.argv[2]
with urllib.request.urlopen(f"https://pypi.org/pypi/scikit-learn/{ver}/json") as r:
    data = json.load(r)
url = next(u["url"] for u in data["urls"] if u["packagetype"] == "sdist")
urllib.request.urlretrieve(url, os.path.join(work, "scikit-learn.tar.gz"))
PY
tar xzf "$WORK/scikit-learn.tar.gz" -C "$WORK" || { rm -rf "$WORK"; command -v termux-wake-unlock >/dev/null 2>&1 && termux-wake-unlock; exit 1; }
SRC="$WORK/scikit_learn-$SK_VER"
sed -i "1s|^#!/usr/bin/env python3|#!$PREFIX/bin/python3|" "$SRC/sklearn/_build_utils/version.py" "$SRC/sklearn/_build_utils/tempita.py"
python -m pip install --no-cache-dir --no-build-isolation "$SRC"
RC=$?
rm -rf "$WORK"
command -v termux-wake-unlock >/dev/null 2>&1 && termux-wake-unlock
[ $RC -ne 0 ] && exit 1
python -c 'import sklearn; print("[+] scikit-learn", sklearn.__version__)'
