#!/usr/bin/env python3
"""termux-train: train your own small AI models on your phone, then use them.

  train-gpt FILE.txt        tiny GPT from scratch on your own text
  train-chat FILE.jsonl     teach SmolLM2-135M your own Q&A (LoRA fine-tune)
  train-classifier FILE.csv text/number classifier (spam, mood, category...)
  train-voice DIR/          sound/voice classifier (one folder per label)
  voice-record LABEL        record voice samples for train-voice
  my-ai ...                 list / chat / gen / predict / voice / plot / delete
"""
import argparse, csv, json, os, random, shutil, subprocess, sys, tempfile, time

HOME = os.path.expanduser("~")
ROOT = os.environ.get("MY_AI_HOME", os.path.join(HOME, "my-ai"))
MODELS = os.path.join(ROOT, "models")
DATA = os.path.join(ROOT, "data")
PREFIX = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
SHARE = os.path.join(PREFIX, "share", "termux-train")
if not os.path.isdir(SHARE):
    SHARE = os.path.dirname(os.path.abspath(__file__))


# ----------------------------------------------------------------- helpers
def say(msg):
    print(msg, flush=True)


def die(msg):
    print("[x] " + msg, file=sys.stderr)
    sys.exit(1)


def model_dir(name, create=False):
    d = os.path.join(MODELS, name)
    if create:
        os.makedirs(d, exist_ok=True)
    return d


def save_meta(d, meta):
    meta["created"] = time.strftime("%Y-%m-%d %H:%M")
    with open(os.path.join(d, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


def load_meta(name):
    p = os.path.join(model_dir(name), "meta.json")
    if not os.path.exists(p):
        die(f"model '{name}' not found. Dekho: my-ai list")
    with open(p) as f:
        return json.load(f)


def default_name(path, kind):
    base = os.path.splitext(os.path.basename(os.path.normpath(path)))[0] or kind
    if base.lower() == kind:
        return f"my-{kind}"
    return f"{kind}-{base}".replace(" ", "_")


class WakeLock:
    def __enter__(self):
        if shutil.which("termux-wake-lock"):
            subprocess.call(["termux-wake-lock"])
        return self

    def __exit__(self, *a):
        if shutil.which("termux-wake-unlock"):
            subprocess.call(["termux-wake-unlock"])


class Logger:
    """Writes log.csv that plot-training understands."""

    def __init__(self, d, cols):
        self.p = os.path.join(d, "log.csv")
        self.f = open(self.p, "w", newline="")
        self.w = csv.writer(self.f)
        self.w.writerow(cols)

    def row(self, *vals):
        self.w.writerow([f"{v:.5f}" if isinstance(v, float) else v for v in vals])
        self.f.flush()


def set_threads():
    import torch
    torch.set_num_threads(max(1, os.cpu_count() or 1))
    return torch


def done_msg(name, use):
    say(f"\n[+] Model saved: {model_dir(name)}")
    say(f"    Use it:  {use}")
    say(f"    Graph:   my-ai plot {name}")


# ======================================================== 1. tiny GPT
def gpt_config(size):
    return {
        "tiny":   dict(n_layer=2, n_head=2, n_embd=64,  block=64),
        "small":  dict(n_layer=4, n_head=4, n_embd=128, block=128),
        "medium": dict(n_layer=6, n_head=6, n_embd=192, block=192),
    }[size]


def build_gpt(vocab, n_layer, n_head, n_embd, block, dropout=0.1):
    import torch, torch.nn as nn
    from torch.nn import functional as F

    class Block(nn.Module):
        def __init__(s):
            super().__init__()
            s.ln1, s.ln2 = nn.LayerNorm(n_embd), nn.LayerNorm(n_embd)
            s.attn = nn.MultiheadAttention(n_embd, n_head, dropout=dropout, batch_first=True)
            s.mlp = nn.Sequential(nn.Linear(n_embd, 4 * n_embd), nn.GELU(),
                                  nn.Linear(4 * n_embd, n_embd), nn.Dropout(dropout))

        def forward(s, x, mask):
            h = s.ln1(x)
            x = x + s.attn(h, h, h, attn_mask=mask, need_weights=False)[0]
            return x + s.mlp(s.ln2(x))

    class GPT(nn.Module):
        def __init__(s):
            super().__init__()
            s.block = block
            s.tok = nn.Embedding(vocab, n_embd)
            s.pos = nn.Embedding(block, n_embd)
            s.blocks = nn.ModuleList([Block() for _ in range(n_layer)])
            s.ln = nn.LayerNorm(n_embd)
            s.head = nn.Linear(n_embd, vocab)

        def forward(s, idx, targets=None):
            T = idx.shape[1]
            x = s.tok(idx) + s.pos(torch.arange(T, device=idx.device))
            mask = torch.triu(torch.ones(T, T, dtype=torch.bool, device=idx.device), 1)
            for b in s.blocks:
                x = b(x, mask)
            logits = s.head(s.ln(x))
            loss = None if targets is None else F.cross_entropy(
                logits.view(-1, logits.size(-1)), targets.view(-1))
            return logits, loss

        @torch.no_grad()
        def generate(s, idx, n, temperature=0.8, top_k=40):
            for _ in range(n):
                logits, _ = s(idx[:, -s.block:])
                logits = logits[:, -1, :] / max(temperature, 1e-3)
                if top_k:
                    v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                    logits[logits < v[:, [-1]]] = -float("inf")
                nxt = torch.multinomial(F.softmax(logits, -1), 1)
                idx = torch.cat([idx, nxt], 1)
            return idx

    return GPT()


def cmd_gpt(a):
    torch = set_threads()
    if not os.path.exists(a.file):
        die(f"file not found: {a.file}")
    text = open(a.file, encoding="utf-8", errors="ignore").read()
    if len(text) < 1000:
        die("text bahut chhota hai: kam se kam 1,000 characters chahiye (better 50,000+).")
    chars = sorted(set(text))
    stoi = {c: i for i, c in enumerate(chars)}
    data = torch.tensor([stoi[c] for c in text], dtype=torch.long)
    n = int(0.9 * len(data))
    train, val = data[:n], data[n:]
    cfg = gpt_config(a.size)
    block = min(cfg["block"], max(16, len(val) - 2))
    cfg["block"] = block
    model = build_gpt(len(chars), **cfg)
    params = sum(p.numel() for p in model.parameters())
    name = a.name or default_name(a.file, "gpt")
    d = model_dir(name, True)
    say(f"[*] train-gpt '{name}': {len(text):,} chars, vocab {len(chars)}, {params/1e6:.2f}M params, {a.steps} steps")
    say("    Ctrl+C dabao to beech me rok kar save kar dega.")
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr)
    log = Logger(d, ["step", "loss", "val_loss"])

    def batch(src):
        ix = torch.randint(len(src) - block - 1, (a.batch,))
        x = torch.stack([src[i:i + block] for i in ix])
        y = torch.stack([src[i + 1:i + block + 1] for i in ix])
        return x, y

    @torch.no_grad()
    def evaluate():
        model.eval()
        out = []
        for src in (train, val):
            out.append(sum(model(*batch(src))[1].item() for _ in range(10)) / 10)
        model.train()
        return out

    def save():
        torch.save(model.state_dict(), os.path.join(d, "model.pt"))
        save_meta(d, {"type": "gpt", "chars": "".join(chars), "config": cfg,
                      "source": os.path.abspath(a.file), "steps": step})

    t0, step = time.time(), 0
    every = max(1, a.steps // 20)
    with WakeLock():
        try:
            for step in range(1, a.steps + 1):
                _, loss = model(*batch(train))
                opt.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step()
                if step % every == 0 or step == a.steps:
                    tl, vl = evaluate()
                    log.row(step, tl, vl)
                    eta = (time.time() - t0) / step * (a.steps - step)
                    say(f"  step {step:5d}/{a.steps}  loss {tl:.3f}  val {vl:.3f}  ETA {eta/60:.1f} min")
        except KeyboardInterrupt:
            say("\n[!] Rok diya, ab tak ka model save kar raha hoon...")
    save()
    model.eval()
    start = torch.tensor([[stoi.get(text[0], 0)]])
    sample = "".join(chars[i] for i in model.generate(start, 200)[0].tolist())
    say("\n--- sample ---\n" + sample + "\n--------------")
    done_msg(name, f'my-ai gen {name} "shuruaat ke shabd"')


def use_gpt(name, meta, prompt, n=300, temperature=0.8):
    torch = set_threads()
    chars = meta["chars"]
    stoi = {c: i for i, c in enumerate(chars)}
    model = build_gpt(len(chars), **meta["config"], dropout=0.0)
    model.load_state_dict(torch.load(os.path.join(model_dir(name), "model.pt"), map_location="cpu"))
    model.eval()
    ids = [stoi[c] for c in prompt if c in stoi] or [0]
    out = model.generate(torch.tensor([ids]), n, temperature=temperature)
    print("".join(chars[i] for i in out[0].tolist()))


# ======================================================== 2. chat (LoRA)
DEFAULT_BASE = "HuggingFaceTB/SmolLM2-135M-Instruct"


def lora_inject(model, targets, r, alpha, dropout=0.05):
    import torch, torch.nn as nn, math

    class LoRALinear(nn.Module):
        def __init__(s, base):
            super().__init__()
            s.base = base
            s.lora_A = nn.Parameter(torch.empty(r, base.in_features))
            s.lora_B = nn.Parameter(torch.zeros(base.out_features, r))
            nn.init.kaiming_uniform_(s.lora_A, a=math.sqrt(5))
            s.scale = alpha / r
            s.drop = nn.Dropout(dropout)

        def forward(s, x):
            return s.base(x) + (s.drop(x) @ s.lora_A.t() @ s.lora_B.t()) * s.scale

    for p in model.parameters():
        p.requires_grad = False
    swaps = []
    for mod in model.modules():
        for cname, child in mod.named_children():
            if isinstance(child, nn.Linear) and cname in targets:
                swaps.append((mod, cname, child))
    for mod, cname, child in swaps:
        setattr(mod, cname, LoRALinear(child))
    return len(swaps)


def read_qa(path):
    """Accepts .jsonl ({q,a} / {question,answer} / {prompt,response} / {messages}),
    .csv (first two columns = question, answer) or .txt (Q: ... / A: ... blocks)."""
    convs = []
    ext = os.path.splitext(path)[1].lower()
    if ext in (".jsonl", ".json"):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                o = json.loads(line)
                if "messages" in o:
                    convs.append(o["messages"])
                    continue
                q = o.get("q") or o.get("question") or o.get("prompt") or o.get("input") or o.get("instruction")
                ans = o.get("a") or o.get("answer") or o.get("response") or o.get("output")
                if q and ans:
                    convs.append([{"role": "user", "content": q}, {"role": "assistant", "content": ans}])
    elif ext == ".csv":
        with open(path, encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))
        if rows and rows[0] and rows[0][0].strip().lower() in ("q", "question", "sawal", "prompt"):
            rows = rows[1:]
        for r in rows:
            if len(r) >= 2 and r[0].strip() and r[1].strip():
                convs.append([{"role": "user", "content": r[0].strip()}, {"role": "assistant", "content": r[1].strip()}])
    else:
        q = None
        for line in open(path, encoding="utf-8"):
            s = line.strip()
            if s[:2].upper() == "Q:":
                q = s[2:].strip()
            elif s[:2].upper() == "A:" and q:
                convs.append([{"role": "user", "content": q}, {"role": "assistant", "content": s[2:].strip()}])
                q = None
    return convs


def load_base(base):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    say(f"[*] Loading {base} (pehli baar ~270 MB download hoga)...")
    tok = AutoTokenizer.from_pretrained(base)
    model = AutoModelForCausalLM.from_pretrained(base, dtype="float32")
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    return tok, model


def cmd_chat(a):
    torch = set_threads()
    if not os.path.exists(a.file):
        die(f"file not found: {a.file}")
    convs = read_qa(a.file)
    if len(convs) < 5:
        die("kam se kam 5 sawal-jawab chahiye (better 50+). Format: my-ai help")
    if a.system:
        convs = [[{"role": "system", "content": a.system}] + c for c in convs]
    if not a.epochs:
        a.epochs = 8 if len(convs) < 100 else (4 if len(convs) < 500 else 2)
    tok, model = load_base(a.base)
    targets = a.targets.split(",")
    n = lora_inject(model, targets, a.rank, a.rank * 2)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    say(f"[*] LoRA on {n} layers, {trainable/1e6:.2f}M trainable params")

    examples = []
    for c in convs:
        full = tok.apply_chat_template(c, tokenize=False)
        prompt = tok.apply_chat_template(c[:-1], tokenize=False, add_generation_prompt=True)
        ids = tok(full, add_special_tokens=False)["input_ids"][:a.max_len]
        plen = len(tok(prompt, add_special_tokens=False)["input_ids"])
        labels = [-100] * min(plen, len(ids)) + ids[plen:]
        if any(l != -100 for l in labels):
            examples.append((ids, labels))
    random.seed(0)
    random.shuffle(examples)
    nval = max(1, len(examples) // 10) if len(examples) >= 10 else 0
    val, train = examples[:nval], examples[nval:]
    name = a.name or default_name(a.file, "chat")
    d = model_dir(name, True)
    say(f"[*] train-chat '{name}': {len(train)} train / {len(val)} val examples, {a.epochs} epochs")
    say("    Ctrl+C dabao to beech me rok kar save kar dega.")
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=a.lr)
    log = Logger(d, ["epoch", "loss", "val_loss"])

    def step_loss(ids, labels):
        x = torch.tensor([ids])
        y = torch.tensor([labels])
        return model(input_ids=x, labels=y).loss

    def save():
        sd = {k: v for k, v in model.state_dict().items() if "lora_" in k}
        torch.save(sd, os.path.join(d, "lora.pt"))
        save_meta(d, {"type": "chat", "base": a.base, "rank": a.rank, "alpha": a.rank * 2,
                      "targets": targets, "system": a.system or "", "examples": len(examples)})

    t0 = time.time()
    total = a.epochs * len(train)
    done = 0
    with WakeLock():
        try:
            model.train()
            for ep in range(1, a.epochs + 1):
                random.shuffle(train)
                run = 0.0
                for i, (ids, labels) in enumerate(train, 1):
                    loss = step_loss(ids, labels) / a.accum
                    loss.backward()
                    run += loss.item() * a.accum
                    if i % a.accum == 0 or i == len(train):
                        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                        opt.step()
                        opt.zero_grad(set_to_none=True)
                    done += 1
                    if i % 10 == 0 or i == len(train):
                        eta = (time.time() - t0) / done * (total - done)
                        say(f"  epoch {ep}/{a.epochs}  {i}/{len(train)}  loss {run/i:.3f}  ETA {eta/60:.1f} min")
                vl = run / len(train)
                if val:
                    model.eval()
                    with torch.no_grad():
                        vl = sum(step_loss(*e).item() for e in val) / len(val)
                    model.train()
                log.row(ep, run / len(train), vl)
                save()
        except KeyboardInterrupt:
            say("\n[!] Rok diya, ab tak ka model save kar raha hoon...")
    save()
    model.eval()
    q = convs[0][-2]["content"]
    say(f"\n--- test ---\nQ: {q}\nA: {chat_reply(tok, model, convs[0][:-1])}\n------------")
    done_msg(name, f"my-ai chat {name}")


def chat_reply(tok, model, msgs, max_new=200, temperature=0.3):
    import torch
    prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    enc = tok(prompt, return_tensors="pt", add_special_tokens=False)
    with torch.no_grad():
        out = model.generate(**enc, max_new_tokens=max_new, do_sample=temperature > 0,
                             temperature=max(temperature, 0.01), top_p=0.9,
                             repetition_penalty=1.15, pad_token_id=tok.pad_token_id)
    return tok.decode(out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True).strip()


def load_chat(name, meta):
    torch = set_threads()
    tok, model = load_base(meta["base"])
    lora_inject(model, meta["targets"], meta["rank"], meta["alpha"], dropout=0.0)
    model.load_state_dict(torch.load(os.path.join(model_dir(name), "lora.pt"), map_location="cpu"), strict=False)
    model.eval()
    return tok, model


def use_chat(name, meta, once=None):
    tok, model = load_chat(name, meta)
    sysmsg = [{"role": "system", "content": meta["system"]}] if meta.get("system") else []
    if once:
        print(chat_reply(tok, model, sysmsg + [{"role": "user", "content": once}]))
        return
    say(f"[{name}] ready. Likho aur Enter dabao. 'exit' se bahar, 'reset' se nayi baat.")
    hist = []
    while True:
        try:
            q = input("\nTum: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if q.lower() in ("exit", "quit", "bye"):
            break
        if q.lower() == "reset":
            hist = []
            continue
        if not q:
            continue
        hist.append({"role": "user", "content": q})
        ans = chat_reply(tok, model, sysmsg + hist[-6:])
        hist.append({"role": "assistant", "content": ans})
        print(f"AI: {ans}")


# ======================================================== 3. classifier
def is_num(v):
    try:
        float(v)
        return True
    except ValueError:
        return False


def cmd_classify(a):
    import joblib
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report
    if not os.path.exists(a.file):
        die(f"file not found: {a.file}")
    with open(a.file, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        die("CSV khali hai. Pehli line header honi chahiye, jaise: text,label")
    cols = list(rows[0].keys())
    label = a.label_col or ("label" if "label" in cols else cols[-1])
    feats = [c for c in cols if c != label]
    rows = [r for r in rows if (r.get(label) or "").strip()]
    y = [r[label].strip() for r in rows]
    classes = sorted(set(y))
    if len(classes) < 2:
        die(f"column '{label}' me kam se kam 2 alag labels chahiye.")
    text_col = a.text_col or ("text" if "text" in feats else None)
    if not text_col and len(feats) == 1 and not all(is_num(r[feats[0]]) for r in rows):
        text_col = feats[0]
    name = a.name or default_name(a.file, "clf")
    d = model_dir(name, True)
    if text_col:
        from sklearn.pipeline import make_pipeline, make_union
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        X = [r[text_col] for r in rows]
        mode = "text"
        make = lambda: make_pipeline(
            make_union(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, min_df=1),
                       TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)),
            LogisticRegression(max_iter=2000, C=5))
        used = [text_col]
    else:
        from sklearn.ensemble import RandomForestClassifier
        used = [c for c in feats if all(is_num(r[c]) for r in rows)]
        if not used:
            die("koi text ya number column nahi mila. --text-col NAME do.")
        X = [[float(r[c]) for c in used] for r in rows]
        mode = "numbers"
        make = lambda: RandomForestClassifier(n_estimators=200, random_state=0)
    say(f"[*] train-classifier '{name}': {len(rows)} rows, mode {mode} ({', '.join(used)}), labels {classes}")
    counts = {c: y.count(c) for c in classes}
    acc = None
    if len(rows) >= 10 and min(counts.values()) >= 2:
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=0,
                                              stratify=y if min(counts.values()) >= 5 else None)
        m = make().fit(Xtr, ytr)
        pred = m.predict(Xte)
        acc = accuracy_score(yte, pred)
        say(f"[*] Test accuracy: {acc*100:.1f}% ({len(yte)} test rows)")
        say(classification_report(yte, pred, zero_division=0))
    else:
        say("[!] Data kam hai, test skip. Har label ke 10+ examples do for better results.")
    model = make().fit(X, y)  # final model on all data
    joblib.dump(model, os.path.join(d, "model.joblib"))
    with open(os.path.join(d, "log.csv"), "w") as f:
        f.write("label,examples\n" + "".join(f"{i},{counts[c]}\n" for i, c in enumerate(classes)))
    save_meta(d, {"type": "classifier", "mode": mode, "features": used, "label": label,
                  "classes": classes, "accuracy": acc, "rows": len(rows)})
    ex = '"yahan apna text"' if mode == "text" else '"' + ",".join(["1.0"] * len(used)) + '"'
    say(f"\n[+] Model saved: {d}\n    Use it:  my-ai predict {name} {ex}")


def use_classify(name, meta, text):
    import joblib
    m = joblib.load(os.path.join(model_dir(name), "model.joblib"))
    if meta["mode"] == "text":
        X = [text]
    else:
        vals = [float(v) for v in text.replace(" ", "").split(",")]
        if len(vals) != len(meta["features"]):
            die(f"{len(meta['features'])} numbers chahiye ({', '.join(meta['features'])})")
        X = [vals]
    probs = m.predict_proba(X)[0]
    ranked = sorted(zip(m.classes_, probs), key=lambda t: -t[1])
    print(f"=> {ranked[0][0]}  ({ranked[0][1]*100:.0f}%)")
    for c, p in ranked[1:3]:
        print(f"   {c}  ({p*100:.0f}%)")


# ======================================================== 4. voice
AUDIO_EXT = (".wav", ".flac", ".ogg", ".mp3", ".m4a", ".aac", ".opus", ".3gp", ".amr", ".webm")
SR = 16000


def load_audio(path):
    import numpy as np, soundfile as sf, librosa
    try:
        y, sr = sf.read(path, dtype="float32", always_2d=True)
        y = y.mean(axis=1)
    except Exception:
        tmp = tempfile.mktemp(suffix=".wav")
        r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", path, "-ac", "1", "-ar", str(SR), tmp])
        if r.returncode != 0:
            raise RuntimeError(f"cannot read {path}")
        y, sr = sf.read(tmp, dtype="float32")
        os.remove(tmp)
    if sr != SR:
        y = librosa.resample(y, orig_sr=sr, target_sr=SR)
    y, _ = librosa.effects.trim(y, top_db=30)
    if len(y) < SR // 10:
        y = np.pad(y, (0, SR // 10 - len(y)))
    return y.astype("float32")


def features(y):
    import numpy as np, librosa
    m = librosa.feature.mfcc(y=y, sr=SR, n_mfcc=20)
    w = min(9, m.shape[1] if m.shape[1] % 2 else m.shape[1] - 1)
    parts = [m]
    if w >= 3:
        parts += [librosa.feature.delta(m, width=w), librosa.feature.delta(m, order=2, width=w)]
    else:
        parts += [np.zeros_like(m), np.zeros_like(m)]
    f = np.concatenate(parts)
    extra = [librosa.feature.spectral_centroid(y=y, sr=SR), librosa.feature.zero_crossing_rate(y),
             librosa.feature.rms(y=y)]
    e = np.concatenate(extra)
    return np.concatenate([f.mean(1), f.std(1), e.mean(1), e.std(1)]).astype("float32")


def augment(y):
    import numpy as np, librosa
    out = [y + np.random.randn(len(y)).astype("float32") * 0.005 * (np.abs(y).max() + 1e-6),
           np.roll(y, np.random.randint(len(y) // 10 + 1)),
           librosa.effects.time_stretch(y, rate=random.choice([0.9, 1.1]))]
    return [o.astype("float32") for o in out]


def build_mlp(n_in, n_out):
    import torch.nn as nn
    return nn.Sequential(nn.Linear(n_in, 128), nn.ReLU(), nn.Dropout(0.3),
                         nn.Linear(128, 64), nn.ReLU(), nn.Dropout(0.2), nn.Linear(64, n_out))


def cmd_voice(a):
    torch = set_threads()
    import numpy as np
    root = a.dir
    if not os.path.isdir(root):
        die(f"folder not found: {root}")
    labels = sorted(l for l in os.listdir(root) if os.path.isdir(os.path.join(root, l)))
    files = {l: [os.path.join(root, l, f) for f in sorted(os.listdir(os.path.join(root, l)))
                 if f.lower().endswith(AUDIO_EXT)] for l in labels}
    labels = [l for l in labels if files[l]]
    if len(labels) < 2:
        die("kam se kam 2 folders (labels) chahiye, har folder me audio files. Record: voice-record LABEL")
    for l in labels:
        if len(files[l]) < 3:
            say(f"[!] '{l}' me sirf {len(files[l])} files. 5-10 better hain.")
    name = a.name or default_name(root, "voice")
    d = model_dir(name, True)
    say(f"[*] train-voice '{name}': labels {labels}, {sum(len(files[l]) for l in labels)} files. Features nikal raha hoon...")
    random.seed(0)
    np.random.seed(0)
    Xtr, ytr, Xva, yva = [], [], [], []
    for li, l in enumerate(labels):
        fs = files[l][:]
        random.shuffle(fs)
        nval = len(fs) // 5 if len(fs) >= 5 else 0
        for i, p in enumerate(fs):
            try:
                y = load_audio(p)
            except Exception as e:
                say(f"[!] skip {p}: {e}")
                continue
            if i < nval:
                Xva.append(features(y)); yva.append(li)
            else:
                Xtr.append(features(y)); ytr.append(li)
                for ya in augment(y):
                    Xtr.append(features(ya)); ytr.append(li)
    Xtr = np.stack(Xtr)
    mean, std = Xtr.mean(0), Xtr.std(0) + 1e-6
    norm = lambda X: torch.tensor((np.stack(X) - mean) / std, dtype=torch.float32)
    Xt, yt = norm(Xtr), torch.tensor(ytr)
    Xv, yv = (norm(Xva), torch.tensor(yva)) if Xva else (None, None)
    model = build_mlp(Xt.shape[1], len(labels))
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-3)
    lossf = torch.nn.CrossEntropyLoss()
    log = Logger(d, ["epoch", "loss", "val_loss", "acc", "val_acc"])
    say(f"[*] Training: {len(Xt)} samples (with augmentation), {len(Xva)} val, {a.epochs} epochs")
    every = max(1, a.epochs // 15)
    with WakeLock():
        for ep in range(1, a.epochs + 1):
            model.train()
            perm = torch.randperm(len(Xt))
            for i in range(0, len(Xt), 32):
                idx = perm[i:i + 32]
                loss = lossf(model(Xt[idx]), yt[idx])
                opt.zero_grad(); loss.backward(); opt.step()
            model.eval()
            with torch.no_grad():
                o = model(Xt)
                tl, ta = lossf(o, yt).item(), (o.argmax(1) == yt).float().mean().item()
                if Xv is not None:
                    ov = model(Xv)
                    vl, va = lossf(ov, yv).item(), (ov.argmax(1) == yv).float().mean().item()
                else:
                    vl, va = tl, ta
            log.row(ep, tl, vl, ta, va)
            if ep % every == 0 or ep == a.epochs:
                say(f"  epoch {ep:4d}/{a.epochs}  loss {tl:.3f}  acc {ta*100:.0f}%  val_acc {va*100:.0f}%")
    torch.save(model.state_dict(), os.path.join(d, "model.pt"))
    np.savez(os.path.join(d, "norm.npz"), mean=mean, std=std)
    save_meta(d, {"type": "voice", "labels": labels, "n_in": int(Xt.shape[1]),
                  "val_acc": va if Xv is not None else None})
    done_msg(name, f"my-ai voice {name} clip.wav   (ya: my-ai voice {name} --record)")


def record_clip(out_wav, secs):
    if not shutil.which("termux-microphone-record"):
        die("termux-api chahiye: pkg install termux-api, aur Play Store/F-Droid se Termux:API app.")
    tmp = os.path.join(tempfile.gettempdir(), f"rec_{int(time.time()*1000)}.m4a")
    subprocess.call(["termux-microphone-record", "-q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.call(["termux-microphone-record", "-f", tmp, "-l", str(secs)], stdout=subprocess.DEVNULL)
    time.sleep(secs + 0.8)
    subprocess.call(["termux-microphone-record", "-q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(20):
        if os.path.exists(tmp) and os.path.getsize(tmp) > 0:
            break
        time.sleep(0.25)
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmp, "-ac", "1", "-ar", str(SR), out_wav])
    if os.path.exists(tmp):
        os.remove(tmp)
    if r.returncode != 0:
        die("recording convert nahi hui. Termux:API app ko microphone permission do.")


def cmd_record(a):
    d = os.path.join(a.dir or os.path.join(DATA, "voice"), a.label)
    os.makedirs(d, exist_ok=True)
    say(f"[*] '{a.label}' ke {a.n} clips record honge ({a.secs}s each) -> {d}")
    for i in range(1, a.n + 1):
        try:
            input(f"  [{i}/{a.n}] Enter dabao aur bolo...")
        except (EOFError, KeyboardInterrupt):
            print(); break
        out = os.path.join(d, f"{a.label}_{time.strftime('%Y%m%d_%H%M%S')}_{i}.wav")
        say("   recording...")
        record_clip(out, a.secs)
        say(f"   saved {os.path.basename(out)}")
    n = len([f for f in os.listdir(d) if f.lower().endswith(AUDIO_EXT)])
    say(f"[+] '{a.label}' me ab {n} clips. Doosre labels bhi record karo, phir: train-voice {os.path.dirname(d)}")


def use_voice(name, meta, path, record=False, secs=2):
    torch = set_threads()
    import numpy as np
    if record:
        path = os.path.join(tempfile.gettempdir(), "my_ai_voice.wav")
        say("Bolo... (recording)")
        record_clip(path, secs)
    if not path or not os.path.exists(path):
        die("audio file do: my-ai voice NAME file.wav  (ya --record)")
    nz = np.load(os.path.join(model_dir(name), "norm.npz"))
    model = build_mlp(meta["n_in"], len(meta["labels"]))
    model.load_state_dict(torch.load(os.path.join(model_dir(name), "model.pt"), map_location="cpu"))
    model.eval()
    x = torch.tensor((features(load_audio(path)) - nz["mean"]) / nz["std"], dtype=torch.float32)[None]
    with torch.no_grad():
        p = torch.softmax(model(x), 1)[0].tolist()
    ranked = sorted(zip(meta["labels"], p), key=lambda t: -t[1])
    print(f"=> {ranked[0][0]}  ({ranked[0][1]*100:.0f}%)")
    for l, v in ranked[1:3]:
        print(f"   {l}  ({v*100:.0f}%)")


# ======================================================== my-ai
HELP = f"""my-ai: apne khud ke AI models train karo aur use karo.

TRAIN (apna data):
  train-gpt   my.txt   [--size tiny|small|medium] [--steps 3000]   apne text se GPT
  train-chat  qa.jsonl [--epochs 8] [--system "Tum ... ho"]       apne Q&A se chatbot
  train-classifier data.csv  [--text-col text --label-col label]  spam/mood/category
  voice-record LABEL [--n 8]  ->  train-voice ~/my-ai/data/voice  awaz pehchanna

USE:
  my-ai list                      saare models
  my-ai chat NAME                 chatbot se baat
  my-ai ask NAME "sawal"          ek jawab
  my-ai gen NAME "shuruaat"       GPT se text likhwao
  my-ai predict NAME "text"       classifier
  my-ai voice NAME clip.wav       (ya --record)
  my-ai plot NAME                 training graph
  my-ai info NAME | delete NAME
  my-ai init                      sample data {ROOT}/samples me copy

DATA FORMATS:
  qa.jsonl : {{"q": "Tumhara naam?", "a": "Mera naam Dost hai."}}  (ek line = ek sawal)
             .csv (question,answer) ya .txt (Q: ... / A: ...) bhi chalega
  data.csv : text,label   (header zaroori)  ya number columns + label
  voice    : ~/my-ai/data/voice/<label>/*.wav  (har label ka ek folder)
"""


def cmd_init(a=None):
    dst = os.path.join(ROOT, "samples")
    os.makedirs(dst, exist_ok=True)
    os.makedirs(os.path.join(DATA, "voice"), exist_ok=True)
    os.makedirs(MODELS, exist_ok=True)
    src = os.path.join(SHARE, "samples")
    for f in os.listdir(src):
        if not os.path.exists(os.path.join(dst, f)):
            shutil.copy(os.path.join(src, f), dst)
    say(f"[+] Samples: {dst}")
    for f in sorted(os.listdir(dst)):
        say(f"    {f}")
    say("\nTry:\n  train-classifier ~/my-ai/samples/spam.csv\n  train-chat ~/my-ai/samples/qa.jsonl"
        "\n  train-gpt ~/my-ai/samples/kahani.txt --size tiny")


def cmd_my(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(HELP); return
    c, rest = argv[0], argv[1:]
    if c == "init":
        return cmd_init()
    if c == "list":
        if not os.path.isdir(MODELS) or not os.listdir(MODELS):
            say("Abhi koi model nahi. Shuru karo: my-ai init"); return
        for n in sorted(os.listdir(MODELS)):
            p = os.path.join(MODELS, n, "meta.json")
            if os.path.exists(p):
                m = json.load(open(p))
                extra = {"chat": f"base {m.get('base','').split('/')[-1]}",
                         "classifier": f"labels {m.get('classes')}",
                         "voice": f"labels {m.get('labels')}",
                         "gpt": f"{m.get('config',{}).get('n_layer')} layers"}.get(m["type"], "")
                say(f"  {n:28s} {m['type']:10s} {m.get('created','')}  {extra}")
        return
    if not rest:
        die(f"model name do: my-ai {c} NAME")
    name = rest[0]
    if c == "delete":
        shutil.rmtree(model_dir(name), ignore_errors=True); say(f"[+] deleted {name}"); return
    meta = load_meta(name)
    if c == "info":
        print(json.dumps({k: v for k, v in meta.items() if k != "chars"}, indent=2, ensure_ascii=False)); return
    if c == "plot":
        log = os.path.join(model_dir(name), "log.csv")
        out = os.path.join(ROOT, "plots", f"{name}.png")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        os.execvp("plot-training", ["plot-training", log, out])
    t = meta["type"]
    if c in ("chat", "ask"):
        if t != "chat":
            die(f"{name} ek {t} model hai, chat model nahi.")
        return use_chat(name, meta, " ".join(rest[1:]) if c == "ask" else None)
    if c == "gen":
        if t != "gpt":
            die(f"{name} ek {t} model hai. GPT ke liye: train-gpt")
        p = argparse.ArgumentParser(prog="my-ai gen")
        p.add_argument("name"); p.add_argument("prompt", nargs="?", default="")
        p.add_argument("-n", type=int, default=300); p.add_argument("-t", "--temperature", type=float, default=0.8)
        g = p.parse_args(rest)
        return use_gpt(name, meta, g.prompt, g.n, g.temperature)
    if c == "predict":
        if t != "classifier":
            die(f"{name} ek {t} model hai, classifier nahi.")
        return use_classify(name, meta, " ".join(rest[1:]) or input("text: "))
    if c == "voice":
        if t != "voice":
            die(f"{name} ek {t} model hai, voice model nahi.")
        rec = "--record" in rest
        args = [r for r in rest[1:] if r != "--record"]
        return use_voice(name, meta, args[0] if args else None, record=rec)
    die(f"unknown command '{c}'. Dekho: my-ai help")


# ======================================================== CLI
def main():
    if len(sys.argv) < 2:
        print(HELP); return
    cmd, argv = sys.argv[1], sys.argv[2:]
    if cmd == "my":
        return cmd_my(argv)
    p = argparse.ArgumentParser(prog=cmd)
    if cmd == "gpt":
        p.prog = "train-gpt"
        p.add_argument("file"); p.add_argument("--name")
        p.add_argument("--size", choices=["tiny", "small", "medium"], default="small")
        p.add_argument("--steps", type=int, default=3000); p.add_argument("--batch", type=int, default=32)
        p.add_argument("--lr", type=float, default=1e-3)
        return cmd_gpt(p.parse_args(argv))
    if cmd == "chat":
        p.prog = "train-chat"
        p.add_argument("file"); p.add_argument("--name"); p.add_argument("--base", default=DEFAULT_BASE)
        p.add_argument("--epochs", type=int, default=0); p.add_argument("--lr", type=float, default=2e-3)
        p.add_argument("--rank", type=int, default=16); p.add_argument("--accum", type=int, default=2)
        p.add_argument("--max-len", type=int, default=256); p.add_argument("--system", default="")
        p.add_argument("--targets", default="q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj")
        return cmd_chat(p.parse_args(argv))
    if cmd == "classify":
        p.prog = "train-classifier"
        p.add_argument("file"); p.add_argument("--name")
        p.add_argument("--text-col"); p.add_argument("--label-col")
        return cmd_classify(p.parse_args(argv))
    if cmd == "voice":
        p.prog = "train-voice"
        p.add_argument("dir", nargs="?", default=os.path.join(DATA, "voice")); p.add_argument("--name")
        p.add_argument("--epochs", type=int, default=150)
        return cmd_voice(p.parse_args(argv))
    if cmd == "record":
        p.prog = "voice-record"
        p.add_argument("label"); p.add_argument("--n", type=int, default=8)
        p.add_argument("--secs", type=float, default=2); p.add_argument("--dir")
        return cmd_record(p.parse_args(argv))
    if cmd == "init":
        return cmd_init()
    print(HELP)


if __name__ == "__main__":
    main()
