<div align="center">
  <h1>termux-learn-crypto APT Repository</h1>
  <p><b>Apni Termux repo: ek command se add karo, phir <code>pkg install</code> karo.</b><br>
  Unofficial APT repository for Termux by termux-learn-crypto.</p>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-BSD_3--Clause-blue?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/termux-learn-crypto/termux-repo/actions"><img src="https://img.shields.io/github/actions/workflow/status/termux-learn-crypto/termux-repo/build_repo.yml?style=for-the-badge&label=build" alt="Build"></a>
</div>

## Install (repo add karo)

```bash
curl -sL https://github.com/termux-learn-crypto/termux-repo/raw/main/install.sh | bash
```

> Piping a script to `bash` runs it immediately. Pehle padhna ho to download karke dekh lo: `curl -sLO https://github.com/termux-learn-crypto/termux-repo/raw/main/install.sh && cat install.sh`

Ye script / This script:
- writes `$PREFIX/etc/apt/sources.list.d/termux-learn-crypto.list`
  (`deb [arch=all] https://termux-learn-crypto.github.io/termux-repo termux-learn-crypto main`)
- installs the signing key to `$PREFIX/etc/apt/trusted.gpg.d/termux-learn-crypto.gpg`
- runs `apt update`

Manual setup (bina script ke):

```bash
echo "deb [arch=all] https://termux-learn-crypto.github.io/termux-repo termux-learn-crypto main" > $PREFIX/etc/apt/sources.list.d/termux-learn-crypto.list
curl -sL https://github.com/termux-learn-crypto/termux-repo/raw/main/assets/termux-learn-crypto.gpg -o $PREFIX/etc/apt/trusted.gpg.d/termux-learn-crypto.gpg
apt update
```

## Packages install karo / Install packages

```bash
pkg update
pkg install voicestudio      # then: voicestudio
pkg install pyaudio-termux   # then: start-audio ; pyaudio-test
pkg install dvwa-android     # then: dvwa-android
```

| Package | Commands | Kya karta hai / What it does |
| :--- | :--- | :--- |
| `voicestudio` | `voicestudio`, `voicestudio-update` | First run installs [VoiceStudio](https://github.com/termux-learn-crypto/VoiceStudio) (termux branch) into `~/VoiceStudio`, then starts it. UI: http://127.0.0.1:3900 |
| `pyaudio-termux` | `pyaudio-setup`, `start-audio`, `pyaudio-test` | Builds PyAudio on Termux (no root) with [pyaudio-termux](https://github.com/termux-learn-crypto/pyaudio-termux); PulseAudio speaker + mic helper and test |
| `dvwa-android` | `dvwa-android` | Downloads the [DVWA Android](https://github.com/termux-learn-crypto/dvwa-android) v2.1.1 APK and opens the installer via `termux-open` |

Packages are light wrappers: `apt install` is instant, the heavy download/build happens the first time you run the command.

## Remove repo / Repo hatao

```bash
curl -sL https://github.com/termux-learn-crypto/termux-repo/raw/main/uninstall.sh | bash
```

Sirf repo source aur key hatati hai; installed packages rehte hain (`pkg uninstall <name>`).

## Kaise kaam karta hai / How it works

- `packages/<name>/DEBIAN/control` + `packages/<name>/data/data/com.termux/files/usr/...`
- On every push to `main`, [GitHub Actions](.github/workflows/build_repo.yml) runs `scripts/build-repo.sh`:
  `dpkg-deb --build --root-owner-group` → `pool/main/*.deb` → `dists/termux-learn-crypto/main/binary-all/Packages(.gz)` → `Release` → signed `InRelease` + `Release.gpg` → GitHub Pages.
- Public key: [`assets/termux-learn-crypto.gpg`](assets/termux-learn-crypto.gpg) (binary) and [`assets/termux-learn-crypto.asc`](assets/termux-learn-crypto.asc) (armored).

## Naya package / Add a package

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

Unofficial, independently maintained. Package scripts run with your Termux user's permissions and download code from the linked GitHub repos; read them before installing. `dvwa-android` is a deliberately vulnerable app for security practice only.

Inspired by [TermuxVoid](https://github.com/termuxvoid/repo).
