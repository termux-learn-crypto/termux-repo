#!/usr/bin/env bash
# Build all packages/* into .deb files and generate a signed APT repo in ./public
#   SUITE (default termux-learn-crypto), COMPONENT (main), GPG_KEY_ID (optional; signs if set)
set -euo pipefail
SUITE="${SUITE:-termux-learn-crypto}"
COMP="${COMPONENT:-main}"
OUT="${OUT:-public}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
rm -rf "$OUT"; mkdir -p "$OUT/pool/$COMP" "$OUT/dists/$SUITE/$COMP/binary-all" "$OUT/dists/$SUITE/$COMP/binary-aarch64"

for dir in packages/*/; do
  [ -f "$dir/DEBIAN/control" ] || continue
  find "$dir" -type d -exec chmod 755 {} +
  find "$dir/data" -type f -path '*/bin/*' -exec chmod 755 {} + 2>/dev/null || true
  for s in postinst preinst postrm prerm; do [ -f "$dir/DEBIAN/$s" ] && chmod 755 "$dir/DEBIAN/$s"; done
  dpkg-deb --build --root-owner-group -Zxz "$dir" "$OUT/pool/$COMP/" >/dev/null
done

( cd "$OUT"
  dpkg-scanpackages --multiversion "pool/$COMP" /dev/null > "dists/$SUITE/$COMP/Packages"
  # Architecture ke hisaab se split karo (mawk-compatible: line-based, regex RS nahi)
  for arch in all aarch64; do
    awk -v want="$arch" '
      BEGIN { buf = ""; cur = "" }
      /^$/ { if (cur == want && buf != "") printf "%s\n", buf; buf = ""; cur = ""; next }
      { buf = buf $0 "\n"; if (index($0, "Architecture: ") == 1) cur = substr($0, 15) }
      END { if (cur == want && buf != "") printf "%s\n", buf }
    ' "dists/$SUITE/$COMP/Packages" > "dists/$SUITE/$COMP/binary-$arch/Packages"
  done
  rm "dists/$SUITE/$COMP/Packages"
  gzip -9nk "dists/$SUITE/$COMP/binary-all/Packages"
  gzip -9nk "dists/$SUITE/$COMP/binary-aarch64/Packages"
  for arch in all aarch64; do
    cat > "dists/$SUITE/$COMP/binary-$arch/Release" <<R
Archive: $SUITE
Component: $COMP
Origin: termux-learn-crypto
Label: termux-learn-crypto
Architecture: $arch
R
  done
  apt-ftparchive \
    -o APT::FTPArchive::Release::Origin="termux-learn-crypto" \
    -o APT::FTPArchive::Release::Label="termux-learn-crypto" \
    -o APT::FTPArchive::Release::Suite="$SUITE" \
    -o APT::FTPArchive::Release::Codename="$SUITE" \
    -o APT::FTPArchive::Release::Architectures="all aarch64" \
    -o APT::FTPArchive::Release::Components="$COMP" \
    -o APT::FTPArchive::Release::Description="termux-learn-crypto Termux APT repository" \
    release "dists/$SUITE" > /tmp/Release
  mv /tmp/Release "dists/$SUITE/Release"
  if [ -n "${GPG_KEY_ID:-}" ]; then
    gpg --batch --yes --pinentry-mode loopback --default-key "$GPG_KEY_ID" --clearsign -o "dists/$SUITE/InRelease" "dists/$SUITE/Release"
    gpg --batch --yes --pinentry-mode loopback --default-key "$GPG_KEY_ID" -abs -o "dists/$SUITE/Release.gpg" "dists/$SUITE/Release"
  fi
)
cp assets/*.gpg assets/*.asc install.sh uninstall.sh index.html "$OUT/" 2>/dev/null || true
touch "$OUT/.nojekyll"
echo "Built repo in $OUT:"; find "$OUT" -type f | sort
