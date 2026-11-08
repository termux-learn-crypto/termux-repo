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

### Machine learning (ML) packages

```bash
apt install termux-ml        # sab ek saath / everything below, then: ml-check

# short names bhi chalte hain / short names work too:
apt install numpy torch scikit-learn tokenizers transformers
apt install scipy soundfile librosa matplotlib
```

Short names: `numpy`, `scipy`, `torch` / `pytorch`, `scikit-learn` / `sklearn`, `tokenizers`, `transformers`, `soundfile`, `librosa` (each installs its `*-termux` package). `matplotlib` is Termux's own package; `matplotlib-termux` adds `plot-training`.

`plot-training log.csv` reads a CSV with a header like `epoch,loss,val_loss,acc,val_acc`, saves `~/plots/training.png` and opens it.

| Package | Kya hai / What | apt installs | Setup during install | Commands |
| :--- | :--- | :--- | :--- | :--- |
| `numpy-termux` | NumPy: गणित और डेटा प्रोसेसिंग | `python-numpy` (prebuilt) | none | `numpy-check` |
| `pytorch-termux` | PyTorch: Neural Network (CPU) | `python-torch` (prebuilt), torchaudio recommended | none | `torch-check` |
| `scikit-learn-termux` | Scikit-learn: छोटे ML मॉडल | numpy, scipy, clang, ninja, openblas | pip builds scikit-learn (20-40 min, no Android wheel) | `sklearn-check`, `sklearn-setup` |
| `tokenizers-termux` | Tokenizers: टेक्स्ट को tokens में बदलना | `python-tokenizers` (prebuilt, tur-repo) | none | `tokenizers-check` |
| `transformers-termux` | Transformers: छोटे भाषा मॉडल | torch, numpy, tokenizers, rust | pip installs transformers 5.x + safetensors (Rust compile 5-15 min) | `transformers-check`, `tiny-llm "prompt"` |
| `scipy-termux` | SciPy: Signal processing | `python-scipy` (prebuilt) | none | `scipy-check` |
| `soundfile-termux` | SoundFile: Audio files (wav/flac/ogg) | `libsndfile`, clang | pip installs cffi + soundfile, patched for Android | `soundfile-check`, `soundfile-setup` |
| `librosa-termux` | librosa: Audio features (MFCC, mel, pitch, tempo) | scipy, llvmlite, soxr, scikit-learn, soundfile, ffmpeg | pip builds numba (10-20 min) + librosa | `librosa-check [file.wav]`, `librosa-setup` |
| `matplotlib-termux` | Matplotlib: Training graphs | `matplotlib` (prebuilt) | none | `plot-training [log.csv]`, `matplotlib-check` |
| `termux-ml` | Bundle of everything above | all of the above | - | `ml-check` |

`tiny-llm` runs HuggingFaceTB/SmolLM2-135M-Instruct on CPU (~270 MB download once). Another model: `tiny-llm "Hi" Qwen/Qwen2.5-0.5B-Instruct`.
`install.sh` enables **tur-repo** too (needed for prebuilt tokenizers). Skip builds: `SKLEARN_SKIP_SETUP=1`, `TRANSFORMERS_SKIP_SETUP=1`, `SOUNDFILE_SKIP_SETUP=1`, `LIBROSA_SKIP_SETUP=1`.

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
