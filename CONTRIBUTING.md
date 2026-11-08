# Naya package kaise add karein / How to add a new package

1. Folder banao / Create a folder:

```
packages/<name>/
├── DEBIAN/
│   ├── control          # required
│   └── postinst         # optional, keep it light (sirf message)
└── data/data/com.termux/files/usr/bin/<command>   # your script, chmod 755
```

2. `DEBIAN/control` example:

```
Package: mytool
Version: 1.0.0
Architecture: all
Maintainer: termux-learn-crypto <vilasrmeshram400@gmail.com>
Depends: bash, curl
Homepage: https://github.com/termux-learn-crypto/mytool
Section: utils
Priority: optional
Description: One-line summary
 Longer description, every line starts with a space.
```

3. Rules / Niyam:
   - Script packages use `Architecture: all`.
   - Shebang: `#!/data/data/com.termux/files/usr/bin/bash`.
   - System deps go in `Depends:` (apt installs them). Never call `pkg`/`apt` inside `postinst` (apt lock is held).
   - Extra setup (git clone, pip build, downloads) goes in `usr/share/<name>/setup.sh`, called from `postinst` (`[ "$1" = configure ]`), non-fatal (`|| echo retry with <name>-setup`; `exit 0`).
   - Update ho to `Version` badhao (e.g. 1.0.0 -> 1.0.1), warna users ko update nahi milega.

4. Local test (Linux/WSL with dpkg-dev, apt-utils):

```bash
./scripts/build-repo.sh        # builds public/ (unsigned without GPG_KEY_ID)
```

5. Commit/push to `main`. GitHub Actions builds every `.deb`, signs
   `InRelease`/`Release.gpg` with the `PRIVATE_GPG_KEY` secret and deploys to
   https://termux-learn-crypto.github.io/termux-repo . Users get it with `pkg update`.
