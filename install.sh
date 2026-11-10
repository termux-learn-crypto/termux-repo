#!/data/data/com.termux/files/usr/bin/bash
# termux-learn-crypto APT repo installer
#   curl -sL https://github.com/termux-learn-crypto/termux-repo/raw/main/install.sh | bash
set -e
NAME="termux-learn-crypto"
REPO_URL="https://termux-learn-crypto.github.io/termux-repo"
KEY_URL="https://github.com/termux-learn-crypto/termux-repo/raw/main/assets/${NAME}.gpg"
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"

G="\e[32m"; Y="\e[33m"; R="\e[31m"; C="\e[36m"; N="\e[0m"
step() { echo -e "${Y}>> $*${N}"; }
ok()   { echo -e "${G}[+] $*${N}"; }
die()  { echo -e "${R}[x] $*${N}" >&2; exit 1; }

[ -d "$PREFIX" ] || die "Termux PREFIX not found. Ye script sirf Termux ke liye hai."
command -v curl >/dev/null 2>&1 || { step "Installing curl"; pkg install -y curl; }

echo -e "${C}termux-learn-crypto repository installer${N}"

step "Enabling tur-repo (Termux User Repository: prebuilt tokenizers etc.)"
if [ ! -f "$PREFIX/etc/apt/sources.list.d/tur.list" ]; then
  apt update -y >/dev/null 2>&1 || true
  apt install -y tur-repo >/dev/null 2>&1 && ok "tur-repo enabled" || echo -e "${Y}[!] tur-repo install failed (tokenizers/transformers need it). Later: apt install tur-repo${N}"
else
  ok "tur-repo already enabled"
fi

step "Enabling termux-glibc repo (needed for tensorflow-termux)"
if [ ! -f "$PREFIX/etc/apt/sources.list.d/glibc.list" ]; then
  apt install -y glibc-repo >/dev/null 2>&1 && ok "termux-glibc repo enabled" || echo -e "${Y}[!] glibc-repo install failed (tensorflow-termux needs it). Later: apt install glibc-repo${N}"
else
  ok "termux-glibc repo already enabled"
fi

step "Adding repository / repo add ho raha hai"
mkdir -p "$PREFIX/etc/apt/sources.list.d" "$PREFIX/etc/apt/trusted.gpg.d"
echo "deb [arch=all] ${REPO_URL} ${NAME} main" > "$PREFIX/etc/apt/sources.list.d/${NAME}.list"
ok "Wrote $PREFIX/etc/apt/sources.list.d/${NAME}.list"

step "Installing GPG key / signing key install ho rahi hai"
curl -fsSL "$KEY_URL" -o "$PREFIX/etc/apt/trusted.gpg.d/${NAME}.gpg" || die "Key download failed"
ok "Key saved to $PREFIX/etc/apt/trusted.gpg.d/${NAME}.gpg"

step "apt update"
apt update -y || die "apt update failed"

ok "Done! Ab install karo:"
echo -e "${C}  apt install voicestudio${N}"
echo -e "${C}  apt install pyaudio-termux${N}"
echo -e "${C}  apt install dvwa-android${N}"
echo -e "${C}  apt install termux-ml        # numpy, torch, scikit-learn, tokenizers, transformers${N}"
echo -e "${C}  apt install tensorflow       # CPU TensorFlow via termux-glibc${N}"
