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

Sab kuch `apt` se install hota hai: dependencies apt laata hai, aur setup install ke time hi ho jata hai.
Everything installs through `apt`: dependencies come from the Termux repos and the setup runs during install.

```bash
apt update
apt install voicestudio      # then: voicestudio  -> http://127.0.0.1:3900
apt install pyaudio-termux   # then: start-audio ; pyaudio-test
apt install dvwa-android     # then: dvwa-android (opens the APK installer)
```

| Package | Version | Commands | Kya karta hai / What it does |
| :--- | :--- | :--- | :--- |
| `voicestudio` | 1.1.0 | `voicestudio`, `voicestudio-setup` | apt installs python, torch, torchaudio, ffmpeg, rust etc.; install step clones [VoiceStudio](https://github.com/termux-learn-crypto/VoiceStudio) (termux branch) into `~/VoiceStudio` with venv + web UI. First install 15-30 min (pydantic-core Rust compile) - phone charge pe rakho. |
| `pyaudio-termux` | 1.1.0 | `start-audio`, `pyaudio-test`, `pyaudio-setup` | apt installs portaudio, pulseaudio, clang, python; install step builds PyAudio ([pyaudio-termux](https://github.com/termux-learn-crypto/pyaudio-termux)). |
| `dvwa-android` | 2.1.1-1 | `dvwa-android` | Install step downloads the [DVWA Android](https://github.com/termux-learn-crypto/dvwa-android) v2.1.1 APK to `~/dvwa-android`; `dvwa-android` opens the Android installer. |

Update: `apt update && apt upgrade`. Remove: `apt remove <name>` (`apt purge` also deletes `~/VoiceStudio` / `~/dvwa-android`).
Skip the heavy setup during install (do it later with `*-setup`): `VS_SKIP_SETUP=1 apt install voicestudio`, `PYAUDIO_SKIP_SETUP=1 apt install pyaudio-termux`.

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
