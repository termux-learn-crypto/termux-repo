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
- enables **tur-repo** (needed for tokenizers) and **termux-glibc** (needed for tensorflow-termux)
- installs the signing key to `$PREFIX/etc/apt/trusted.gpg.d/termux-learn-crypto.gpg`
- runs `apt update`

Manual setup (bina script ke):

```bash
echo "deb [arch=all] https://termux-learn-crypto.github.io/termux-repo termux-learn-crypto main" > $PREFIX/etc/apt/sources.list.d/termux-learn-crypto.list
curl -sL https://github.com/termux-learn-crypto/termux-repo/raw/main/assets/termux-learn-crypto.gpg -o $PREFIX/etc/apt/trusted.gpg.d/termux-learn-crypto.gpg
apt install -y tur-repo glibc-repo   # tokenizers / tensorflow-termux need these
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
apt install termux-ml        # sab ek saath / everything below (incl. PEFT + Accelerate + TRL + Datasets), then: ml-check
apt install bitsandbytes     # k-bit quantization via glibc, CPU-only

# short names bhi chalte hain / short names work too:
apt install numpy torch scikit-learn tokenizers transformers peft accelerate trl datasets
apt install scipy soundfile librosa matplotlib tensorflow
```

Short names: `numpy`, `scipy`, `torch` / `pytorch`, `scikit-learn` / `sklearn`, `tokenizers`, `transformers`, `peft`, `accelerate`, `trl`, `datasets`, `soundfile`, `librosa`, `tensorflow`, `bitsandbytes` (each installs its `*-termux` package). `matplotlib` is Termux's own package; `matplotlib-termux` adds `plot-training`.

`plot-training log.csv` reads a CSV with a header like `epoch,loss,val_loss,acc,val_acc`, saves `~/plots/training.png` and opens it.

| Package | Kya hai / What | apt installs | Setup during install | Commands |
| :--- | :--- | :--- | :--- | :--- |
| `numpy-termux` | NumPy: गणित और डेटा प्रोसेसिंग | `python-numpy` (prebuilt) | none | `numpy-check` |
| `pytorch-termux` | PyTorch: Neural Network (CPU) | `python-torch` (prebuilt), torchaudio recommended | none | `torch-check` |
| `scikit-learn-termux` | Scikit-learn: छोटे ML मॉडल | numpy, scipy, clang, ninja, openblas | pip builds scikit-learn (20-40 min, no Android wheel) | `sklearn-check`, `sklearn-setup` |
| `tokenizers-termux` | Tokenizers: टेक्स्ट को tokens में बदलना | `python-tokenizers` (prebuilt, tur-repo) | none | `tokenizers-check` |
| `transformers-termux` | Transformers: छोटे भाषा मॉडल | torch, numpy, tokenizers, rust | pip installs transformers 5.x + safetensors (Rust compile 5-15 min) | `transformers-check`, `tiny-llm "prompt"` |
| `peft-termux` | PEFT: LoRA / parameter-efficient fine-tuning | torch, transformers, rust, python-psutil, accelerate-termux | pip installs peft; safetensors already built by transformers-termux | `peft-check`, `peft-setup` |
| `accelerate-termux` | Accelerate: CPU-only PyTorch training on phone (GPU/CUDA नहीं) | torch, numpy, python-psutil, rust (safetensors fallback) | pip installs accelerate | `accelerate-check`, `accelerate-setup`, upstream `accelerate` CLI |
| `datasets-termux` | Datasets: training data management (load, stream, cache) | torch not needed | pip installs datasets + small pure-Python deps (xxhash has Android wheels; pyarrow from apt prebuilt) | `datasets-check`, `datasets-setup` |
| `trl-termux` | TRL: SFT / DPO / PPO / GRPO training | torch, transformers, `datasets-termux`, `accelerate-termux`, `python-pyarrow` (prebuilt), python-pandas | pip installs trl (datasets + accelerate come from datasets-termux / accelerate-termux; pydantic-core compiles with Rust, ~10-20 min) | `trl-check`, `trl-setup` |
| `scipy-termux` | SciPy: Signal processing | `python-scipy` (prebuilt) | none | `scipy-check` |
| `soundfile-termux` | SoundFile: Audio files (wav/flac/ogg) | `libsndfile`, clang | pip installs cffi + soundfile, patched for Android | `soundfile-check`, `soundfile-setup` |
| `librosa-termux` | librosa: Audio features (MFCC, mel, pitch, tempo) | scipy, llvmlite, soxr, scikit-learn, soundfile, ffmpeg | pip builds numba (10-20 min) + librosa | `librosa-check [file.wav]`, `librosa-setup` |
| `matplotlib-termux` | Matplotlib: Training graphs | `matplotlib` (prebuilt) | none | `plot-training [log.csv]`, `matplotlib-check` |
| `tensorflow-termux` | TensorFlow: Neural Network (CPU) | `glibc-repo`, `glibc-runner`, `python-glibc` (Python 3.12), `python-pip-glibc` | pip installs TensorFlow into glibc python (~300 MB, chai peete wait karo) | `tensorflow-check`, `tensorflow-setup`, `tf-python` |
| `bitsandbytes-termux` | bitsandbytes: k-bit model quantization (LLM.int8/NF4), CPU | `glibc-repo`, `glibc-runner`, `python-glibc` (3.12), torch (CPU) | pip installs torch + bitsandbytes into glibc python (~700 MB) | `bnb-check`, `bnb-setup`, `bnb-python` |
| `termux-ml` | Bundle of everything above | all of the above | - | `ml-check` |

`tensorflow-termux` bionic `python3` me **import nahi hota** — bionic ke liye TensorFlow wheels hain hi nahi, aur PyPI wala aarch64 wheel glibc chahta hai. `install.sh` **termux-glibc** repo enable karta hai (jaise tur-repo); apt glibc Python 3.12 laata hai, aur `pip install tensorflow` wahan chalta hai. Use: `tf-python my_model.py` (`python3` ki jagah) — ya apne scripts me glibc python path. Note: `grun` arguments ko spaces pe split karta hai, isliye `-c '...'` ke bajaye script file do. Skip the download: `TF_SKIP_SETUP=1 apt install tensorflow-termux`, fir baad me `tensorflow-setup` (pin version: `TF_VERSION=2.21.0 tensorflow-setup`).

`bitsandbytes-termux` bionic `python3` me kaam nahi karta — bionic ke liye bitsandbytes wheels hain hi nahi aur CPU support 0.46+ Linux-glibc CPU par hai. `install.sh` **termux-glibc** enable karta hai; apt glibc Python 3.12 aur torch (CPU) laata hai, aur bitsandbytes wahan pip se aata hai. Use: `bnb-python my_quant_script.py`. CPU par LLM.int8(), NF4 4-bit quantization aur 8-bit optimizers kaam karte hain (GPU wale fast CUDA kernels nahi). Skip the download: `BNB_SKIP_SETUP=1 apt install bitsandbytes-termux`, fir `bnb-setup` (pin: `BNB_VERSION=0.50.2 bnb-setup`).

`tiny-llm` runs HuggingFaceTB/SmolLM2-135M-Instruct on CPU (~270 MB download once). Another model: `tiny-llm "Hi" Qwen/Qwen2.5-0.5B-Instruct`.
`install.sh` enables **tur-repo** (prebuilt tokenizers) and **termux-glibc** (tensorflow-termux) too. Skip builds: `SKLEARN_SKIP_SETUP=1`, `TRANSFORMERS_SKIP_SETUP=1`, `SOUNDFILE_SKIP_SETUP=1`, `LIBROSA_SKIP_SETUP=1`, `TF_SKIP_SETUP=1`, `PEFT_SKIP_SETUP=1`, `TRL_SKIP_SETUP=1`, `DATASETS_SKIP_SETUP=1`, `ACCELERATE_SKIP_SETUP=1`, `BNB_SKIP_SETUP=1`.

Update: `apt update && apt upgrade`. Remove: `apt remove <name>` (`apt purge` also deletes `~/VoiceStudio` / `~/dvwa-android`).
Skip the heavy setup during install (do it later with `*-setup`): `VS_SKIP_SETUP=1 apt install voicestudio`, `PYAUDIO_SKIP_SETUP=1 apt install pyaudio-termux`.


## Apna AI train karo / Train your own AI (termux-train)

```bash
apt install termux-train
my-ai init        # samples: ~/my-ai/samples (qa.jsonl, spam.csv, mood.csv, kahani.txt)
my-ai help
```

| Command | Kya seekhta hai / What it learns | Your data |
|---|---|---|
| `train-chat qa.jsonl` | SmolLM2-135M ko apne sawal-jawab (LoRA) | `{"q": "...", "a": "..."}` per line, or CSV `question,answer`, or `Q:`/`A:` text |
| `train-gpt my.txt --size tiny/small/medium` | Zero se chhota GPT, apne text ke style me | any `.txt` |
| `train-classifier data.csv` | Spam / mood / category | CSV with `text,label` (or number columns + `label`) |
| `voice-record LABEL` then `train-voice` | Apni awaz / sounds pehchanna | `~/my-ai/data/voice/<label>/*.wav` |

Use: `my-ai chat NAME`, `my-ai ask NAME "sawal"`, `my-ai gen NAME "shuru"`, `my-ai predict NAME "text"`, `my-ai voice NAME clip.wav` (or `--record`), `my-ai plot NAME`, `my-ai list`.
Models stay in `~/my-ai/models/` and run offline. Ctrl+C during training saves what is learned so far.

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
