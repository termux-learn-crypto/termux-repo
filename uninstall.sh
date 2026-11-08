#!/data/data/com.termux/files/usr/bin/bash
# Removes the termux-learn-crypto repo source and key (installed packages stay).
NAME="termux-learn-crypto"
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
rm -f "$PREFIX/etc/apt/sources.list.d/${NAME}.list" "$PREFIX/etc/apt/trusted.gpg.d/${NAME}.gpg"
echo "[+] Repo removed. Installed packages are kept (remove with: pkg uninstall <name>)."
apt update -y >/dev/null 2>&1 || true
