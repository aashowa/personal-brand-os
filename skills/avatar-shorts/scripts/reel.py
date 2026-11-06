#!/usr/bin/env python3
"""avatar-shorts pipeline: a script -> your HeyGen avatar -> a polished 9:16 Short (Nick Saraev format).

usage: reel.py new     REEL_DIR [--ghost WORD] [--avatar SLOT]
                                                 scaffold reel.json (the defaults below; the least-used avatar slot from
                                                 config.json heygen.avatars unless --avatar), script.txt, spec.py, HyperFrames project
       reel.py heygen  REEL_DIR                  script.txt -> HeyGen avatar render (OAuth plan credits) -> heygen/avatar.mp4
       reel.py prep    REEL_DIR                  pauses cut (voice untouched), light grade, voice polish, word timings
       reel.py rehook  REEL_DIR "LINE" [--name b] [--opening TYPE]
                                                 Trial Reel: REEL_DIR-trial-NAME with only the first sentence re-rendered
                                                 (~4 credits) and spliced in; post.json "trial" points at its master
       reel.py words   REEL_DIR                  print the spoken words with their times (to write the spec)
       reel.py build   REEL_DIR                  spec.py -> index.html, footage crops, SFX stem, ducked music; prints the screen-time mix
       reel.py render  REEL_DIR                  hyperframes check (0 errors) + delivery render -> PROJECT/renders/raw.mp4
       reel.py master  REEL_DIR [NAME]           -14 LUFS / -1 dBTP master + phone copy (< 30 MB) in REEL_DIR (stays local)
       reel.py drive   REEL_DIR [NAME]           once you approve: upload the master to your Shorts folder on Google Drive
                                                 (config.json drive.shorts_folder_id; replaces a same-name file). That folder
                                                 means approved (content-autopilot), so never before your OK
       reel.py props   REEL_DIR NAME [NAME...]   Microsoft Fluent 3D emoji (MIT, 1,500+ objects) -> REEL_DIR/photos/p3d-<name>.png,
                                                 by their Fluent name ("Money bag", "Spiral calendar"); logged in src/SOURCES.tsv
       reel.py --selftest

REEL_DIR/reel.json holds everything per Short (see DEFAULTS); your avatars, voice, glossary and Drive folder come from
<repo>/config.json ("heygen", "drive"). Built on the episode-shorts kit (shorts_kit.py) and adds Nick's third layout
(avatar full screen), pause cuts, snap zooms, kick zooms, louder SFX, a ducked music bed, and character helpers
(the Claude Code crab, props, Noto emoji stickers).
"""
import contextlib, io
import importlib.util, json, os, re, shutil, subprocess, sys, urllib.parse, urllib.request

SKILL = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
SKILLS = os.path.dirname(SKILL)
ROOT = os.path.dirname(SKILLS)                             # the repo root (skills/ sits in it): config.json and .env live here
sys.path.insert(0, os.path.join(SKILLS, "episode-shorts", "scripts"))
POLISH = os.path.join(SKILLS, "palmier-hyperframes-video", "scripts")
HF = "hyperframes@0.8.174"   # pinned: bare npx drifts between versions. Bump after a check + snapshot match on your last Reel
CONFIG = json.load(open(_p)) if os.path.exists(_p := os.path.join(ROOT, "config.json")) else {}
HG, DRIVE = CONFIG.get("heygen", {}), CONFIG.get("drive", {})

# Avatar IV is the default engine: sharper real lips and teeth than V. IV takes no motion prompt on a video avatar, so
# new() adds MOTION (+ the avatar's real-mouth line) only to a Reel set back to avatar_v.
MOTION = "Talking straight to camera like a creator explaining something, natural small hand gestures, confident and relaxed"
MOUTH = (". Keep the person's real mouth exactly as in the training footage: their own teeth, lip shape and facial hair. "
         "Natural, small mouth movements that match the words; never smooth, whiten or reshape the mouth")
# config.json heygen.avatars, in rotation order: slot -> (avatar_id, split cam_y, motion prompt addition). Each new Reel
# gets the least-used slot. heygen.legacy maps old avatar ids to a slot, so rotation and covers still count those reels.
AVATARS = {k: (v["id"], v.get("cam_y", "40%"), MOUTH if v.get("real_mouth") else "") for k, v in HG.get("avatars", {}).items()}
LEGACY = HG.get("legacy", {})
PIN = HG.get("pin")                  # a slot every new Reel uses; null = rotate
PAUSED = set(HG.get("paused", []))   # slots left out of rotation; --avatar still works for a paused one

# Recommended defaults (from the tested Reels). Change them here or per Reel in reel.json.
DEFAULTS = {
    "slug": None, "project": "project", "spec": "spec.py", "ghost": "", "cam_y": "40%",
    "footage": None,           # privacy-blurred source video for s.foot crops (e.g. an episode's 1x export), optional
    "music": None,             # bed audio; default assets/music/tech-bed.mp3 (not shipped: assets/README.md)
    "drive_folder": DRIVE.get("shorts_folder_id"),   # your Shorts folder on Drive; null = no upload
    "caption_fixes": {"words": {"ok.": "OK.", "Ok.": "OK.", **HG.get("caption_fixes", {})}},   # whisper spells the glossary sounds
    "heygen": {"type": "avatar", "avatar_id": next(iter(AVATARS.values()), [None])[0], "voice_id": HG.get("voice_id"),
               "voice_settings": {"speed": 1.0}, "engine": {"type": "avatar_iv"}, "aspect_ratio": "9:16", "resolution": "1080p",
               **({"brand_glossary_id": HG["brand_glossary_id"]} if HG.get("brand_glossary_id") else {}),   # your pronunciation glossary
               "tts": {"pitch_variance": 1.8, "seed": 7, "speed": 1.2}},  # expressive voice C; drop it for the flat voice
}
# S1 smooth-light grade: soft contrast, lifted shadows, rolled-off highlights (a bright wall stops clipping), a little
# warmth and colour; no sharpening, no vignette, no glow.
GRADE = ("eq=contrast=0.98:gamma=1.04:saturation=1.08,vibrance=intensity=0.25,colortemperature=temperature=5900:mix=0.4,"
         "curves=master='0/0.02 0.5/0.53 0.9/0.88 1/0.95'")
PAD, LEAD, TAIL = 0.05, 0.05, 0.15                         # silence kept each side of a cut pause / before the first word / after the last
SFX_LEAD = {"air-whoosh": 0.08, "whoosh-thud": 0.25, "riser-short": 1.6}
SUPPLY_SFX = ("air-whoosh", "whoosh-thud", "riser-short", "boom", "cash", "click-pop")   # names the code uses, not shipped: assets/README.md


os.environ["HYPERFRAMES_SKIP_SKILLS"] = "1"  # init would otherwise overwrite the skills in your skills folder


def run(*a, **k): return subprocess.run(a, check=True, **k)


def dur(p): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True).stdout)


def load(reel):
    reel = os.path.abspath(reel); cfg = {**DEFAULTS, **json.load(open(os.path.join(reel, "reel.json")))}
    cfg["dir"], cfg["proj"] = reel, os.path.join(reel, cfg["project"]); cfg["work"] = os.path.join(reel, "_work")
    cfg["slug"] = cfg["slug"] or os.path.basename(reel); os.makedirs(cfg["work"], exist_ok=True)
    for k in ("footage", "music"):
        if cfg.get(k): cfg[k] = os.path.normpath(os.path.join(reel, os.path.expanduser(cfg[k])))
    return cfg


def env(key):
    """A secret from the environment, else from the repo-root .env (an already-set env var wins)."""
    if os.environ.get(key): return os.environ[key]
    p = os.path.join(ROOT, ".env")
    for line in (open(p) if os.path.exists(p) else []):
        if line.startswith(key + "="): return line.split("=", 1)[1].strip()
    sys.exit(f"{key} is not set: add it to {p}")


def heygen_env():
    """HEYGEN_API_KEY bills API credits (balance 0) and overrides the OAuth session, so never pass it to the CLI."""
    return {k: v for k, v in os.environ.items() if k != "HEYGEN_API_KEY"}


def credits():
    try:
        d = json.loads(subprocess.run(["heygen", "user", "me", "get"], capture_output=True, text=True, env=heygen_env()).stdout)
        return d["data"]["subscription"]["credits"]["premium_credits"]["remaining"]
    except Exception:
        return None


# ---------------------------------------------------------------- new
def next_avatar(episodes):
    """The avatar the reel-* folders have used least; ties go to the one unused longest, then AVATARS order."""
    names = LEGACY | {v[0]: k for k, v in AVATARS.items()}; used = {k: [0, -1] for k in AVATARS}; pool = [k for k in AVATARS if k not in PAUSED]
    for i, d in enumerate(sorted(x for x in os.listdir(episodes) if x.startswith("reel-"))):
        try: k = names.get(json.load(open(os.path.join(episodes, d, "reel.json")))["heygen"]["avatar_id"])
        except (OSError, KeyError, ValueError): continue
        if k: used[k][0] += 1; used[k][1] = i
    return min(pool, key=lambda k: (*used[k], list(AVATARS).index(k)))


def new(reel, ghost="", avatar=None):
    os.makedirs(reel, exist_ok=True)
    p = os.path.join(reel, "reel.json")
    if not os.path.exists(p):
        if not AVATARS: sys.exit(f"no avatars: add your HeyGen avatar looks to heygen.avatars in {ROOT}/config.json (see config.example.json)")
        avatar = avatar or PIN or next_avatar(os.path.dirname(os.path.abspath(reel)))
        aid, cam_y, extra = AVATARS[avatar]
        hg = DEFAULTS["heygen"] | {"avatar_id": aid}
        if hg["engine"]["type"] == "avatar_v": hg["motion_prompt"] = MOTION + extra
        json.dump({k: v for k, v in DEFAULTS.items() if k in ("project", "spec", "caption_fixes", "footage")} | {"ghost": ghost, "cam_y": cam_y, "heygen": hg},
                  open(p, "w"), indent=1)
        print("avatar", avatar, aid)
    if not os.path.exists(os.path.join(reel, "script.txt")): open(os.path.join(reel, "script.txt"), "w").write("")
    if not os.path.exists(os.path.join(reel, "spec.py")): shutil.copy(os.path.join(SKILL, "examples", "starter", "spec.py"), os.path.join(reel, "spec.py"))
    if not os.path.exists(os.path.join(reel, "project", "index.html")):
        run("npx", "-y", HF, "init", "project", "--non-interactive", "--example=blank", "--skill=general-video", cwd=reel)
    print("new ok", reel, "-> write script.txt, then: reel.py heygen", reel)


# ---------------------------------------------------------------- heygen
def audio_body(body, url):
    """Lip-sync to our own speech: script and voice fields go (script and audio_url are exclusive), the audio URL comes in."""
    return {k: v for k, v in body.items() if k not in ("script", "voice_id", "voice_settings", "brand_glossary_id", "tts")} | {"audio_url": url}


def spoken(text, terms):
    """The glossary only works on scripts, so the tts path puts its respellings into the speech text (script.txt keeps normal spelling)."""
    for t in terms: text = re.sub(rf"(?<!\w){re.escape(t['term'])}(?!\w)", t["pronunciation"], text, flags=re.I)   # HeyGen terms are case-insensitive ("PLUGINS" = "plugins")
    return text


def heygen(reel):
    c = load(reel); H = os.path.join(c["dir"], "heygen"); os.makedirs(H, exist_ok=True)
    script = " ".join(open(os.path.join(c["dir"], "script.txt")).read().split())
    assert script, "script.txt is empty"
    body = {**c["heygen"], "script": script, "title": c["slug"]}
    if not body.get("voice_id"): sys.exit(f"no voice_id: set heygen.voice_id in {ROOT}/config.json (or in this reel.json)")
    if not shutil.which("heygen"): sys.exit("the heygen CLI is not installed or not on PATH (references/heygen.md § Setup)")
    before = credits()
    if "tts" in body:   # expressive voice (a flat clone has "no ups and downs"): speak it with pitch_variance first, lip-sync to that
        g = body.get("brand_glossary_id")
        terms = json.loads(subprocess.run(["heygen", "brand", "glossaries", "get", g], capture_output=True, text=True, env=heygen_env(), check=True).stdout)["data"]["terms"] if g else []
        r = subprocess.run(["heygen", "model", "audio", "tts", "create", "-d", json.dumps({"voice_id": body["voice_id"], "text": spoken(script, terms), "language": "en", **body["tts"]})],
                           capture_output=True, text=True, env=heygen_env())
        if r.returncode: sys.exit(f"heygen tts failed: {r.stderr[-800:]}")
        url = json.loads(r.stdout)["data"]["audio_url"]; urllib.request.urlretrieve(url, f"{H}/voice-tts.wav")
        body = audio_body(body, url)
    json.dump(body, open(f"{H}/request.json", "w"), indent=1)
    r = subprocess.run(["heygen", "video", "create", "-d", json.dumps(body), "--wait"], capture_output=True, text=True, env=heygen_env())
    open(f"{H}/create.json", "w").write(r.stdout)
    if r.returncode: sys.exit(f"heygen failed: {r.stderr[-800:]}")
    x = json.loads(r.stdout)["data"]
    if os.path.exists(f"{H}/avatar.mp4"):                       # keep earlier takes for comparison
        n = 1
        while os.path.exists(f"{H}/avatar-take{n}.mp4"): n += 1
        os.rename(f"{H}/avatar.mp4", f"{H}/avatar-take{n}.mp4")
    urllib.request.urlretrieve(x["video_url"], f"{H}/avatar.mp4")
    after = credits()
    print(f"heygen ok {x['id']} {x['duration']:.1f}s | credits {before} -> {after}" + (f" (used {before - after})" if before and after else ""))


# ---------------------------------------------------------------- prep
def keep_ranges(silences, d, fps=30):
    """Silences [(start, end)] -> speech ranges to keep, each pause trimmed to 2*PAD, snapped to frames (picture and
    sound cut on the same frame boundaries so the lips stay in sync). A blip under 0.2 s between two pauses is breath."""
    snap = lambda t: round(t * fps) / fps
    merged = []
    for s, e in silences:
        if merged and s - merged[-1][1] < 0.2: merged[-1] = (merged[-1][0], e)
        else: merged.append((s, e))
    keep, cur = [], 0.0
    for s, e in merged:
        if s <= 0.01: cur = max(0.0, e - LEAD); continue
        if e >= d - 0.01: keep.append((cur, min(d, s + TAIL))); return [(snap(a), snap(b)) for a, b in keep]
        keep.append((cur, s + PAD)); cur = e - PAD
    keep.append((cur, d))
    return [(snap(a), snap(b)) for a, b in keep if b - a > 1 / fps]


def transcribe(mp3, key):
    """whisper-1 word timestamps. No prompt: passing the script made whisper-1 hallucinate ("I'll see you next time")."""
    b = "----avatarshorts"
    parts = [("model", "whisper-1"), ("response_format", "verbose_json"), ("timestamp_granularities[]", "word")]
    body = b"".join(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode() for k, v in parts)
    body += (f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="v.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n'.encode()
             + open(mp3, "rb").read() + f"\r\n--{b}--\r\n".encode())
    req = urllib.request.Request("https://api.openai.com/v1/audio/transcriptions", data=body,
                                 headers={"Authorization": "Bearer " + key, "Content-Type": f"multipart/form-data; boundary={b}"})
    r = json.load(urllib.request.urlopen(req, timeout=300))
    words = [[round(w["start"], 3), round(w["end"], 3), w["word"].strip()] for w in r["words"]]
    toks, j = r["text"].split(), 0
    for w in words:                                   # whisper drops punctuation on words: take it from the text
        while j < len(toks) and toks[j].strip(".,?!").lower() != w[2].strip(".,?!").lower(): j += 1
        if j < len(toks): w[2] = toks[j]; j += 1
    return words


def prep(reel):
    c = load(reel); src = os.path.join(c["dir"], "heygen", "avatar.mp4"); A = os.path.join(c["proj"], "assets"); W = c["work"]
    os.makedirs(A, exist_ok=True)
    D0 = dur(src)
    log = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-vn", "-af", "silencedetect=noise=-38dB:d=0.18", "-f", "null", "-"], capture_output=True, text=True).stderr
    ss = [max(0, float(x)) for x in re.findall(r"silence_start: (-?[\d.]+)", log)]; se = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    keep = keep_ranges(list(zip(ss, se + [D0] * (len(ss) - len(se)))), D0); n = len(keep)
    vf = f"[0:v]fps=30,{GRADE},split={n}" + "".join(f"[v{i}]" for i in range(n)) + ";" + \
         ";".join(f"[v{i}]trim={a:.4f}:{b:.4f},setpts=PTS-STARTPTS[s{i}]" for i, (a, b) in enumerate(keep)) + ";" + \
         "".join(f"[s{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v]"
    af = f"[0:a]aresample=48000,asplit={n}" + "".join(f"[a{i}]" for i in range(n)) + ";" + \
         ";".join(f"[a{i}]atrim={a:.4f}:{b:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.004,afade=t=out:st={b - a - 0.004:.4f}:d=0.004[t{i}]"
                  for i, (a, b) in enumerate(keep)) + ";" + "".join(f"[t{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[a]"
    run("ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", vf + ";" + af, "-map", "[v]", "-c:v", "libx264", "-crf", "16",
        "-preset", "medium", "-pix_fmt", "yuv420p", "-g", "30", "-bf", "0", "-movflags", "+faststart", f"{A}/camera.mp4",
        "-map", "[a]", "-ac", "2", "-c:a", "pcm_s16le", f"{W}/voice-cut.wav")
    sys.path.insert(0, POLISH); import audio_polish as P   # Palmier step 03: highpass, 2.5:1, -17 LUFS, limiter -6 dBFS
    i_pre, _ = P.measure(f"{W}/voice-cut.wav", P.PRE)
    run("ffmpeg", "-v", "error", "-y", "-i", f"{W}/voice-cut.wav", "-af", P.chain(i_pre), "-c:a", "pcm_s16le", "-ar", "48000", f"{A}/voice.wav")
    bed = c["music"] or os.path.join(SKILL, "assets", "music", "tech-bed.mp3")
    if not os.path.exists(bed): sys.exit(f"prep: no music bed at {bed}: set \"music\" in reel.json or add one (assets/README.md)")
    shutil.copy(bed, f"{A}/music.mp3")
    cuts, t = [], 0.0
    for a, b in keep[:-1]: t += b - a; cuts.append(round(t, 3))          # join points on the new timeline
    run("ffmpeg", "-v", "error", "-y", "-i", f"{A}/voice.wav", "-ac", "1", "-ar", "16000", "-b:a", "48k", f"{W}/voice16k.mp3")
    words = transcribe(f"{W}/voice16k.mp3", env("OPENAI_API_KEY"))
    D = dur(f"{A}/camera.mp4")
    json.dump({"duration": round(D, 3), "words": words, "cuts": cuts}, open(f"{A}/words.json", "w"), indent=0)
    print(f"prep ok: cut {n - 1} pauses {D0:.1f}s -> {D:.1f}s, {len(words)} words")


def first_cut(words):
    """Where the first sentence ends in words.json: the frame halfway through the pause after its last word."""
    for (a, b, w), nxt in zip(words, words[1:]):
        if w.endswith((".", "?", "!")):
            return round((b + nxt[0]) / 2 * 30) / 30
    sys.exit("no sentence end in words.json")


def rehook(reel, line, name="b", opening=""):
    """A Trial Reel: the same Reel with a new first sentence (the growth loop, research/growth/test.md).
    Copies REEL_DIR to REEL_DIR-trial-NAME without renders or old takes, renders only the new line in HeyGen (~5 s,
    ~4 credits), swaps it in for the old first sentence at the pause after it (the join goes into words.json "cuts",
    so build hides it with a punch, like a patched CTA), re-transcribes, and points the Reel's post.json "trial" at
    the copy's master. Next: fix the copy's spec.py where it anchors on the old line's words, then build, render, master."""
    c = load(reel); line = " ".join(line.split()); dst = f"{c['dir']}-trial-{name}"
    if os.path.exists(dst): sys.exit(f"{dst} already exists")
    def skip(d, names):
        return [n for n in names if n in ("renders", "_work", "node_modules", "studio") or n.startswith(("avatar-", "voice-tests"))
                or (d == c["dir"] and n.endswith(".mp4")) or (os.path.basename(d) == "heygen" and n.endswith((".mp4", ".wav")))]
    shutil.copytree(c["dir"], dst, ignore=skip)
    cfg = json.load(open(f"{dst}/reel.json")); cfg["slug"] = f"{c['slug']}-trial-{name}"; json.dump(cfg, open(f"{dst}/reel.json", "w"), indent=1)
    d = load(dst); A, W = os.path.join(d["proj"], "assets"), d["work"]
    old = json.load(open(f"{A}/words.json")); cut = first_cut(old["words"])
    for f in ("camera.mp4", "voice.wav"): os.rename(f"{A}/{f}", f"{W}/orig-{f}")
    text = open(f"{dst}/script.txt").read(); first = re.split(r"(?<=[.?!])\s+", text.strip(), maxsplit=1)[0]
    open(f"{dst}/script.txt", "w").write(line)
    heygen(dst); prep(dst)                                         # assets/ now hold the new line alone
    hook, hd = json.load(open(f"{A}/words.json")), dur(f"{A}/camera.mp4")
    for f in ("camera.mp4", "voice.wav"): os.rename(f"{A}/{f}", f"{W}/hook-{f}")
    run("ffmpeg", "-v", "error", "-y", "-i", f"{W}/hook-camera.mp4", "-i", f"{W}/orig-camera.mp4", "-filter_complex",
        f"[1:v]trim=start={cut:.4f},setpts=PTS-STARTPTS[b];[0:v][b]concat=n=2:v=1:a=0[v]", "-map", "[v]", "-c:v", "libx264", "-crf", "16",
        "-preset", "medium", "-pix_fmt", "yuv420p", "-g", "30", "-bf", "0", "-movflags", "+faststart", f"{A}/camera.mp4")
    run("ffmpeg", "-v", "error", "-y", "-i", f"{W}/hook-voice.wav", "-i", f"{W}/orig-voice.wav", "-filter_complex",
        f"[0:a]afade=t=out:st={hd - 0.004:.4f}:d=0.004[a];[1:a]atrim=start={cut:.4f},asetpts=PTS-STARTPTS,afade=t=in:d=0.004[b];"
        "[a][b]concat=n=2:v=0:a=1[o]", "-map", "[o]", "-c:a", "pcm_s16le", "-ar", "48000", f"{A}/voice.wav")
    cuts = hook["cuts"] + [round(hd, 3)] + [round(x - cut + hd, 3) for x in old["cuts"] if x > cut + 0.05]
    words = hook["words"] + [[round(a - cut + hd, 3), round(b - cut + hd, 3), w] for a, b, w in old["words"] if a >= cut]   # the rest keeps its
    json.dump({"duration": round(dur(f"{A}/camera.mp4"), 3), "words": words, "cuts": cuts}, open(f"{A}/words.json", "w"), indent=0)  # own words: a re-transcribe drifts ("One" -> "1")
    open(f"{dst}/script.txt", "w").write(text.replace(first, line, 1))
    pj = os.path.join(c["dir"], "post.json"); p = json.load(open(pj)); cap = p.get("caption", "")
    p["trial"] = {"video": os.path.relpath(f"{dst}/{d['slug']}.mp4", c["dir"]), "hook": name, "opening": opening, "graduation": "MANUAL",
                  "caption": cap.replace(first, line, 1) if cap.startswith(first) else f"{line}\n\n{cap}"}
    json.dump(p, open(pj, "w"), indent=1, ensure_ascii=False)
    print(f"rehook ok: {os.path.basename(dst)} | old first line: {first!r} | joined at {hd:.2f}s (cut the old at {cut:.2f}s)\n"
          f"next: in {dst}/spec.py re-anchor what used the old line's words, then build / render / master")


def words(reel):
    c = load(reel); d = json.load(open(os.path.join(c["proj"], "assets", "words.json")))
    print(f"duration {d['duration']}s | cuts {d['cuts']}")
    print(" ".join(f"{w[2]}@{w[0]:.2f}" for w in d["words"]))


# ---------------------------------------------------------------- characters
# A character acting the story out is what makes a Reel fun. The Claude Code crab is Anthropic's mascot: Claude topics
# only, like a logo. Rebuilt as SVG parts so it can act:
# #p moves, #p-s squashes, #p-l1..l3 legs, #p-aL/aR arms, #p-eL/eR eyes. Character ids start with "k" (kit ids don't).
OR, INK = "#DA7756", "#141412"
PROPS = {   # drawn to sit on / next to the crab; the css passed to prop() places them inside the crab's box
    "cap": f'<svg viewBox="0 0 200 150" width="100%" height="100%"><polygon points="100,8 196,46 100,84 4,46" fill="{INK}"/><rect x="52" y="62" width="96" height="44" fill="{INK}"/>'
           f'<rect x="150" y="44" width="8" height="66" fill="#FFD43B"/><rect x="144" y="106" width="20" height="24" fill="#FFD43B"/></svg>',
    "chef": f'<svg viewBox="-10 -10 220 190" width="100%" height="100%"><g fill="{INK}"><rect x="6" y="32" width="188" height="90"/><rect x="22" y="6" width="72" height="56"/>'
            f'<rect x="106" y="6" width="72" height="56"/><rect x="64" y="-6" width="72" height="60"/><rect x="28" y="100" width="144" height="66"/></g><g fill="#fff">'
            f'<rect x="14" y="40" width="172" height="74"/><rect x="30" y="14" width="56" height="40"/><rect x="114" y="14" width="56" height="40"/><rect x="72" y="2" width="56" height="44"/>'
            f'<rect x="36" y="108" width="128" height="50"/></g><rect x="78" y="114" width="8" height="38" fill="{INK}"/><rect x="114" y="114" width="8" height="38" fill="{INK}"/></svg>',
    "lens": f'<svg viewBox="0 0 170 170" width="100%" height="100%"><rect x="96" y="100" width="28" height="74" fill="{INK}" transform="rotate(-45 110 137)"/>'
            f'<circle cx="64" cy="64" r="50" fill="rgba(34,81,209,.18)" stroke="{INK}" stroke-width="14"/><rect x="38" y="36" width="14" height="22" fill="#fff" opacity=".8"/></svg>',
    "receipt": f'<svg viewBox="0 0 120 160" width="100%" height="100%"><polygon points="8,8 112,8 112,150 98,140 84,150 70,140 56,150 42,140 28,150 14,140 8,150" fill="#fff" stroke="{INK}" stroke-width="8"/>'
               f'<rect x="24" y="30" width="72" height="9" fill="#5E5E58"/><rect x="24" y="54" width="56" height="9" fill="#5E5E58"/><rect x="24" y="78" width="64" height="9" fill="#5E5E58"/>'
               f'<rect x="24" y="106" width="40" height="14" fill="{INK}"/></svg>',
    "coins": '<svg viewBox="0 0 140 130" width="100%" height="100%">' + "".join(
        f'<rect x="8" y="{y}" width="124" height="32" fill="#FFD43B" stroke="{INK}" stroke-width="7"/><rect x="30" y="{y + 12}" width="80" height="7" fill="{INK}" opacity=".35"/>'
        for y in (86, 54, 22)) + '</svg>',
}
STICKERS = os.path.join(SKILL, "assets", "stickers")       # Noto animated emoji (Lottie, CC BY 4.0, © Google LLC)


def crab(s, p, x, y, w, props=""):
    """Claude Code crab at (x, y), w wide, as html for a beat; props = prop() html riding on it (they squash with it)."""
    r = lambda i, x_, y_, w_, h_, c=OR: f'<rect id="{p}-{i}" x="{x_}" y="{y_}" width="{w_}" height="{h_}" fill="{c}"/>'
    return (f'<div id="{p}" data-layout-allow-overflow style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{round(w * 240 / 336)}px;transform-origin:50% 100%">'
            f'<div id="{p}-s" data-layout-allow-overflow style="position:absolute;inset:0;transform-origin:50% 100%">'
            '<svg viewBox="0 0 336 240" style="position:absolute;inset:0;width:100%;height:100%;overflow:visible">'
            + r("l1", 52, 180, 54, 58) + r("l2", 141, 180, 54, 58) + r("l3", 230, 180, 54, 58) + r("aL", 0, 66, 60, 57) + r("aR", 276, 66, 60, 57)
            + r("bd", 52, 0, 232, 186) + r("eL", 84, 21, 32, 32, INK) + r("eR", 222, 21, 32, 32, INK) + f'</svg>{props}</div></div>')


def prop(s, pid, name, css):
    """A PROPS item (or raw svg) placed by css inside the crab box, e.g. "left:105px;top:-118px;width:210px;height:158px"."""
    return f'<div id="{pid}" data-layout-allow-overflow style="position:absolute;{css}">{PROPS.get(name, name)}</div>'


def drop(s, sel, t, frm=-1100, dur=0.22, sfx="whoosh-short"):
    """Falls in from above (crab or prop); hidden above until t. Follow with squash() at t + dur."""
    s.js.append(f"tl.fromTo('{sel}',{{y:{frm}}},{{y:0,duration:{dur},ease:'power2.in'}},{t:.3f});")
    if sfx: s.sfx.append((t - 0.05, sfx))


def squash(s, p, t, sfx="click-pop"):
    """Lands: 0.07 s squash, elastic settle."""
    s.js.append(f"tl.fromTo('#{p}-s',{{scaleX:1,scaleY:1}},{{scaleX:1.16,scaleY:0.82,duration:0.07,ease:'power2.out',immediateRender:false}},{t:.3f});")
    s.js.append(f"tl.fromTo('#{p}-s',{{scaleX:1.16,scaleY:0.82}},{{scaleX:1,scaleY:1,duration:0.35,ease:'elastic.out(1,0.45)',immediateRender:false}},{t + 0.07:.3f});")
    if sfx: s.sfx.append((t, sfx))


def blink(s, p, t):
    s.js.append(f"tl.fromTo(['#{p}-eL','#{p}-eR'],{{scaleY:1}},{{scaleY:0.12,duration:0.06,yoyo:true,repeat:1,ease:'power1.inOut',transformOrigin:'50% 50%',immediateRender:false}},{t:.3f});")


def dance(s, p, t, n=5, beat=0.13):
    """Legs and arms alternate, body rocks; n odd so every part ends where it started (lasts beat * (n + 2))."""
    s.js.append(f"tl.fromTo(['#{p}-l1','#{p}-l3','#{p}-aL'],{{y:0}},{{y:-16,duration:{beat},yoyo:true,repeat:{n},ease:'sine.inOut',immediateRender:false}},{t:.3f});")
    s.js.append(f"tl.fromTo(['#{p}-l2','#{p}-aR'],{{y:0}},{{y:-16,duration:{beat},yoyo:true,repeat:{n},ease:'sine.inOut',immediateRender:false}},{t + beat:.3f});")
    s.js.append(f"tl.fromTo('#{p}-s',{{rotation:-4}},{{rotation:4,duration:{beat * 2},yoyo:true,repeat:{n // 2},ease:'sine.inOut',immediateRender:false}},{t:.3f});")
    s.js.append(f"tl.set('#{p}-s',{{rotation:0}},{t + beat * (n + 2):.3f});")


def peek(s, p, t, h, sfx="pop"):
    """Rises h px from behind a card (put the crab before the card in the html); hidden until t."""
    s.js.append(f"tl.fromTo('#{p}',{{y:{h},opacity:0}},{{y:0,opacity:1,duration:0.32,ease:'back.out(1.6)'}},{t:.3f});")
    if sfx: s.sfx.append((t, sfx))


def clone(s, p, dx, t, sfx="whoosh"):
    """A copy slides dx px out from behind the crab it sits on (same x, earlier in the html) and lands; hidden until t."""
    s.js.append(f"tl.fromTo('#{p}',{{x:0,opacity:0}},{{x:{dx},opacity:1,duration:0.3,ease:'back.out(1.4)'}},{t:.3f});")
    squash(s, p, t + 0.3, sfx=None)
    if sfx: s.sfx.append((t - 0.02, sfx))


def sticker(s, sid, code, css, t, sfx="pop"):
    """Noto animated emoji (code like "1f440" = 👀) as a white-outlined sticker that pops in at t. Returns html for a beat.
    Lottie data is inlined (no fetch at render); a missing code is fetched once into assets/stickers/."""
    f = os.path.join(STICKERS, f"{code}.json")
    if not os.path.exists(f):
        urllib.request.urlretrieve(f"https://fonts.gstatic.com/s/e/notoemoji/latest/{code}/lottie.json", f)
    if not getattr(s, "lottie", False):
        s.html.append('<script src="https://cdnjs.cloudflare.com/ajax/libs/bodymovin/5.12.2/lottie.min.js"></script>'); s.lottie = True
    s.html.append(f'<script>window.__st_{sid}={json.dumps(json.load(open(f)), separators=(",", ":"))};</script>')
    s.js.append(f"window.__hfLottie=window.__hfLottie||[];window.__hfLottie.push(lottie.loadAnimation({{container:document.getElementById('{sid}'),"
                f"renderer:'svg',loop:true,autoplay:false,animationData:window.__st_{sid}}}));")
    s.js.append(f"tl.fromTo('#{sid}',{{scale:0,rotation:-40,opacity:0}},{{scale:1,rotation:-8,opacity:1,duration:0.32,ease:'back.out(2.2)'}},{t:.3f});")
    if sfx: s.sfx.append((t + 0.02, sfx))
    return (f'<div id="{sid}" data-layout-allow-overflow style="position:absolute;{css};filter:drop-shadow(5px 0 0 #fff) drop-shadow(-5px 0 0 #fff) '
            'drop-shadow(0 5px 0 #fff) drop-shadow(0 -5px 0 #fff) drop-shadow(0 12px 16px rgba(0,0,0,.18))"></div>')


CHARACTER = (crab, prop, drop, squash, blink, dance, peek, clone, sticker)


# ---------------------------------------------------------------- build
def build(reel):
    c = load(reel); import shorts_kit as K
    A = os.path.join(c["proj"], "assets"); wj = json.load(open(f"{A}/words.json")); D, cuts = wj["duration"], wj.get("cuts", [])
    name = os.path.basename(c["proj"])
    cfg = {"dir": c["dir"], "export": c["footage"], "speed": 1.0, "fps": 30, "caption_fixes": c["caption_fixes"],
           "shorts": {name: {"ghost": c["ghost"], "edl": [[0, D]]}}}
    K.TEMPLATE = K.TEMPLATE.replace("#camz video{{width:100%;height:100%;object-fit:cover;display:block}}",
                                    "#camz video{{width:100%;height:100%;object-fit:cover;object-position:50% " + c["cam_y"] + ";display:block}}")
    # music bed ducked under the voice: ~-22 LUFS in the gaps, ~-27.5 under speech (-7 dB on a -14.5 LUFS bed)
    run("ffmpeg", "-v", "error", "-y", "-i", f"{A}/music.mp3", "-i", f"{A}/voice.wav", "-filter_complex",
        f"[0:a]atrim=0:{D + 0.5},volume=-7dB,afade=t=out:st={D - 0.8:.2f}:d=0.8[m];[m][1:a]sidechaincompress=threshold=0.05:ratio=3:attack=20:release=250[d]",
        "-map", "[d]", "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", f"{A}/music.wav")
    K.TEMPLATE = K.TEMPLATE.replace('<audio id="sfx"', '<audio id="music" src="assets/music.wav" data-start="0" data-duration="{D}" data-track-index="10" data-volume="1"></audio>\n<audio id="sfx"')
    sys.path.insert(0, K.SFX_SCRIPTS); import sfx as S                    # extra SFX next to the media-use bank
    _load, bank = S.load, os.path.join(SKILL, "assets", "sfx")
    S.load = lambda nm: _load(nm) if not os.path.exists(f"{bank}/{nm}.mp3") else __import__("numpy").frombuffer(
        run("ffmpeg", "-v", "error", "-i", f"{bank}/{nm}.mp3", "-ac", "2", "-ar", str(S.SR), "-f", "f32le", "-", capture_output=True).stdout,
        "float32").reshape(-1, 2).copy()
    S.LEAD.update(SFX_LEAD)

    def face(s, t0, t1, zooms=()):
        """Avatar full screen: a full-frame clip of the same footage synced by data-media-start (layout tweens on
        top/height fail the check). Each pause cut inside flips the framing 1.0 <-> 1.12 (jump cut), plus (t, scale)
        punches; at most one snap per 0.35 s. Captions drop low."""
        fid = s.uid("face")
        s.html.append(f'<video id="{fid}" class="clip face" src="assets/camera.mp4" muted playsinline data-start="{t0:.3f}" '
                      f'data-duration="{t1 - t0:.3f}" data-media-start="{t0:.3f}" data-track-index="4" '
                      'style="position:absolute;left:0;top:0;width:1080px;height:1920px;object-fit:cover;z-index:5;transform-origin:50% 38%"></video>')
        ev, base = [], 1.0
        for x in cuts:
            if t0 + 0.25 < x < t1 - 0.25: base = 1.12 if base == 1.0 else 1.0; ev.append((x, base))
        prev, last = 1.0, -9.0
        for t, sc in sorted(ev + list(zooms)):
            if t - last < 0.35: continue
            last = t
            s.js.append(f"tl.fromTo('#{fid}',{{scale:{prev}}},{{scale:{sc},duration:0.06,ease:'power3.out',immediateRender:false}},{t:.3f});")
            s.sfx.append((t, "air-whoosh")); prev = sc
        s.full.append((t0, t1)); s.faces = getattr(s, "faces", []) + [(t0, t1)]

    def zap(s, t, hold=0.7, sc=1.12):
        """Very quick zoom punch on the split-screen camera."""
        s.cam_punch(t, t + hold, sc); s.sfx.append((t, "air-whoosh"))

    def kick(s, bid, t0, sfx="whoosh-thud"):
        """A full-screen graphic lands with a fast zoom-out (1.12 -> 1) and a whoosh."""
        s.js.append(f"tl.fromTo('#{bid}',{{scale:1.12}},{{scale:1,duration:0.22,ease:'expo.out',immediateRender:false}},{t0:.3f});")
        if sfx: s.sfx.append((t0, sfx))
    def card(s, t0, t1, v5, rect, box, push=1.05):
        """Footage card cropped from "footage" at any box (x, y, w, h; even sizes), above full-screen graphics (z 6).
        Hidden after t1: a wrapper left visible would cover later beats. Returns (id, frame html for the beat)."""
        x, y, w, h = box; fid = s.uid("f")
        s.footage.append({"id": fid, "v5": v5, "rect": rect, "mode": "box", "size": (w, h), "dur": t1 - t0})
        s.html.append(f'<div class="fwrap" data-layout-allow-overflow id="{fid}w" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;z-index:6"><div class="fzoom" id="{fid}z">'
                      f'<video id="{fid}" class="clip" src="assets/{fid}.mp4" muted playsinline data-start="{t0:.3f}" data-duration="{t1 - t0:.3f}" data-track-index="1"></video></div></div>')
        s.card_in([f"#{fid}w", f"#{fid}fr"], t0); s.push(f"#{fid}z", t0, t1, push); s.fade_out(f"#{fid}w", t1 - 0.02, 0.02)
        return fid, f'<div class="frame" id="{fid}fr" style="left:{x - 6}px;top:{y - 6}px;width:{w + 12}px;height:{h + 12}px"></div>'
    K.Short.face, K.Short.zap, K.Short.kick, K.Short.card, K.Short.cuts = face, zap, kick, card, cuts
    for f in CHARACTER: setattr(K.Short, f.__name__, f)

    spec = os.path.join(c["dir"], c["spec"])
    m = importlib.util.spec_from_file_location("reel_spec", spec); mod = importlib.util.module_from_spec(m); m.loader.exec_module(mod)
    s = K.Short(cfg, name); mod.make(s)
    for x in cuts:                                  # pause cuts in split beats: hide the jump with a punch
        if not any(a - 0.05 <= x <= b + 0.05 for a, b in s.full) and not any(abs(x - p[0]) < 0.3 for p in s.punch): s.zap(x, 0.5)
    # glitch-* files are 2.6-3.5 s of digital static; uncut they hiss under the voice ("static at the start")
    s.sfx = [h if len(h) > 2 or not h[1].startswith("glitch") else (h[0], h[1], h[0] + 0.3) for h in s.sfx]
    miss = sorted({h[1] for h in s.sfx if h[1] in SUPPLY_SFX and not os.path.exists(f"{bank}/{h[1]}.mp3")})
    if miss: sys.exit(f"build stopped: {miss} missing from {bank}/ (add them: assets/README.md)")
    caps = s.build()
    for f in os.listdir(A):                         # the kit reuses a cached crop by id even when its range changed: recut
        if re.fullmatch(r"f\d+\.mp4", f): os.remove(os.path.join(A, f))
    if s.footage: s.cut_footage()
    s.mix_sfx(peak=-19)                             # louder than the kit's -24: "action packed"
    st = static_runs(f"{A}/sfx.wav")
    if st: sys.exit(f"build stopped: sustained static in the SFX stem at {st} s. Cut that sound short: s.sfx.append((t, name, t_end))")
    fc = sum(b - a for a, b in getattr(s, "faces", [])); fl = sum(b - a for a, b in s.full) - fc
    print(f"build ok {D:.1f}s | face {100 * fc / D:.0f}% | split {100 * (D - fc - fl) / D:.0f}% | graphics {100 * fl / D:.0f}% "
          f"(target ~20/28/52) | footage {len(s.footage)} | captions {len(caps)} | sfx {len(s.sfx)}")


# ---------------------------------------------------------------- render / master
def render(reel):
    c = load(reel)
    chk = subprocess.run(["npx", "-y", HF, "check"], cwd=c["proj"], capture_output=True, text=True)
    m = re.search(r"(\d+) error\(s\)", chk.stdout + chk.stderr)
    if not m or int(m.group(1)) or "Check failed" in chk.stdout + chk.stderr:
        sys.exit("check failed:\n" + "\n".join(l for l in (chk.stdout + chk.stderr).splitlines() if "✗" in l or "rror" in l)[:3000])
    os.makedirs(os.path.join(c["proj"], "renders"), exist_ok=True)
    run("npx", "-y", HF, "render", "--quality", "delivery", "--workers", "2", "--output", "renders/raw.mp4", cwd=c["proj"])
    print("render ok", os.path.join(c["proj"], "renders", "raw.mp4"))


def master(reel, name=None):
    c = load(reel); src = os.path.join(c["proj"], "renders", "raw.mp4"); out = os.path.join(c["dir"], (name or c["slug"]) + ".mp4")
    m = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-vn", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    d = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}:"
          f"measured_thresh={d['input_thresh']}:offset={d['target_offset']}:linear=true,alimiter=limit=0.87:level=disabled")
    run("ffmpeg", "-v", "error", "-y", "-i", src, "-c:v", "copy", "-af", af, "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out)
    phone = out[:-4] + "-phone.mp4"                 # under 30 MB: phone and chat file limits sit around there
    run("ffmpeg", "-v", "error", "-y", "-i", out, "-c:v", "libx264", "-crf", "24", "-preset", "medium", "-c:a", "copy", "-movflags", "+faststart", phone)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", out, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    errs = subprocess.run(["ffmpeg", "-v", "error", "-i", out, "-f", "null", "-"], capture_output=True, text=True).stderr.strip()
    summ = " ".join(l.strip() for l in r[r.rindex("Summary:"):].splitlines() if l.strip().startswith(("I:", "Peak:")))
    sheet = out[:-4] + "-safe.jpg"   # Instagram's covered areas shaded on 8 frames (format.md § Safe zone)
    run("ffmpeg", "-v", "error", "-y", "-i", out, "-vf", f"fps={8 / dur(out):.5f},drawbox=0:0:iw:230:red@0.35:fill,drawbox=0:1440:iw:ih-1440:red@0.35:fill,"
        "drawbox=iw-230:960:230:480:red@0.25:fill,scale=270:-1,tile=8x1", "-frames:v", "1", sheet)
    print(f"master ok {out} ({dur(out):.1f}s, {os.path.getsize(out) / 1e6:.0f} MB) | {summ} | decode errors {len(errs.splitlines()) if errs else 0} "
          f"| phone {os.path.getsize(phone) / 1e6:.1f} MB | safe zone: {sheet}")
    print("next: watch the phone copy; `reel.py drive` only after you approve it (the Drive folder means approved)")


FLUENT = "https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets"


def props(reel, names):
    """Illustrated 3D props for the graphics (adilet.fndr-grade objects instead of system emoji)."""
    os.makedirs(f"{reel}/photos", exist_ok=True); os.makedirs(f"{reel}/src", exist_ok=True)
    for n in names:
        slug = n.lower().replace(" ", "_"); out = f"{reel}/photos/p3d-{slug.replace('_', '-')}.png"
        for path in (f"{n}/3D/{slug}_3d.png", f"{n}/Default/3D/{slug}_3d_default.png"):
            url = f"{FLUENT}/{urllib.parse.quote(path)}"
            try: urllib.request.urlretrieve(url, out)
            except Exception: continue
            open(f"{reel}/src/SOURCES.tsv", "a").write(f"photos/{os.path.basename(out)}\tMicrosoft Fluent emoji 3D (MIT) {url}\n")
            print("prop ok", os.path.basename(out)); break
        else: print("prop missing", n)


def static_runs(wav, min_len=0.5):
    """Stretches of sustained noise (spectral flatness > 0.1, louder than -40 dB) lasting >= min_len s -> [(t0, t1)].
    Catches a static-like SFX tail before you hear it ("static at the start")."""
    import numpy as np
    x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-ac", "1", "-ar", "48000", "-f", "f32le", "-"],
                                     capture_output=True, check=True).stdout, np.float32)
    W, runs = 4800, []
    for i in range(len(x) // W):
        seg = x[i * W:(i + 1) * W] * np.hanning(W); sp = np.abs(np.fft.rfft(seg)) + 1e-12
        if np.sqrt(np.mean(seg ** 2)) > 0.01 and np.exp(np.mean(np.log(sp))) / np.mean(sp) > 0.1:
            if runs and runs[-1][1] == i: runs[-1][1] = i + 1
            else: runs.append([i, i + 1])
    return [(a / 10, b / 10) for a, b in runs if b - a >= min_len * 10]


def gws(*a):
    """Google Workspace CLI (gws). Its drive.file scope can write into the folder and sees only files it uploaded, which
    is all the same-name lookup needs. config.json drive.gws_config_dir picks a gws profile (file keyring); unset = gws's
    own default. Returns the JSON reply."""
    d = DRIVE.get("gws_config_dir")
    e = os.environ | ({"GOOGLE_WORKSPACE_CLI_CONFIG_DIR": os.path.expanduser(d), "GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND": "file"} if d else {})
    if not shutil.which("gws"): sys.exit("drive: the gws CLI (Google Workspace CLI) is not installed or not on PATH")
    out = subprocess.run(["gws", *a], capture_output=True, text=True, env=e)
    if out.returncode: sys.exit(f"gws {' '.join(a[:3])} failed: {(out.stdout + out.stderr).strip()[-400:]}")
    return json.loads(out.stdout[out.stdout.index("{"):])


def drive(reel, name=None, ext=".mp4"):
    c = load(reel); f = os.path.join(c["dir"], (name or c["slug"]) + ext); folder = c["drive_folder"]
    if not folder: return print("drive: no drive.shorts_folder_id in config.json (or drive_folder in reel.json), skipped")
    q = f"name = '{os.path.basename(f)}' and '{folder}' in parents and trashed = false"
    hit = gws("drive", "files", "list", "--params", json.dumps({"q": q, "fields": "files(id)", "supportsAllDrives": True,
                                                                 "includeItemsFromAllDrives": True}))["files"]
    p = {"supportsAllDrives": True, "fields": "id,webViewLink"}
    if hit: r = gws("drive", "files", "update", "--params", json.dumps(p | {"fileId": hit[0]["id"]}), "--upload", f)
    else: r = gws("drive", "files", "create", "--params", json.dumps(p), "--json", json.dumps({"name": os.path.basename(f), "parents": [folder]}), "--upload", f)
    print(f"drive ok ({'replaced' if hit else 'new'}) {r['webViewLink']}")


def selftest():
    global AVATARS, LEGACY, PAUSED                  # placeholder slots, so the test needs no config.json
    AVATARS = {"a": ("avatar-a", "40%", ""), "b": ("avatar-b", "40%", ""), "c": ("avatar-c", "40%", MOUTH),
               "d": ("avatar-d", "36%", MOUTH), "e": ("avatar-e", "40%", MOUTH)}
    LEGACY, PAUSED = {"old-avatar-e": "e"}, {"d"}
    k = keep_ranges([(0, 0.3), (5.1, 5.7), (9.5, 10.0)], 10.0)
    assert len(k) == 2 and abs(k[0][0] - 0.25) < 0.04 and abs(k[0][1] - 5.15) < 0.04 and abs(k[1][0] - 5.65) < 0.04 and abs(k[1][1] - 9.65) < 0.04, k
    k = keep_ranges([(0, 0.3), (5.1, 5.7), (5.8, 6.4), (9.5, 10.0)], 10.0)      # 0.1 s blip between pauses = one pause
    assert len(k) == 2 and abs(k[1][0] - 6.35) < 0.04, k
    assert "HEYGEN_API_KEY" not in heygen_env()
    assert first_cut([[0, 1.0, "Most"], [1.1, 1.5, "mods."], [1.9, 2.2, "You"]]) == 1.7   # rehook joins halfway through the pause
    b = audio_body({**DEFAULTS["heygen"], "script": "hi", "tts": {"pitch_variance": 1.5}}, "https://x/a.wav")
    assert b["audio_url"] == "https://x/a.wav" and not {"script", "voice_id", "voice_settings", "brand_glossary_id", "tts"} & set(b) and b["engine"], b
    g = [{"term": "Kubectl", "pronunciation": "cube control"}, {"term": "MP4", "pronunciation": "em pee four"}, {"term": "GITHUB", "pronunciation": "GitHub"}]
    assert spoken("Run Kubectl, an MP4. Comment GITHUB; GitHub stays, MP45 too.", g) == "Run cube control, an em pee four. Comment GitHub; GitHub stays, MP45 too."
    g = [{"term": "plugin", "pronunciation": "plug-in"}, {"term": "plugins", "pronunciation": "plug-ins"}]
    assert spoken("Five plugins. Comment PLUGINS for one plugin.", g) == "Five plug-ins. Comment plug-ins for one plug-in."
    import tempfile
    with tempfile.TemporaryDirectory() as d:                 # a new Reel renders on Avatar IV without a motion prompt (IV refuses one)
        os.makedirs(f"{d}/r/project"); [open(f"{d}/r/{f}", "w").close() for f in ("script.txt", "spec.py", "project/index.html")]
        with contextlib.redirect_stdout(io.StringIO()): new(f"{d}/r", avatar="e")
        h = json.load(open(f"{d}/r/reel.json"))["heygen"]
        assert h["engine"] == {"type": "avatar_iv"} and "motion_prompt" not in h and h["avatar_id"] == AVATARS["e"][0], h
    import tempfile                                # static detector: 1 s of white noise trips it, a tone doesn't
    with tempfile.TemporaryDirectory() as d:
        for src, want in (("anoisesrc=d=1:a=0.3", 1), ("sine=f=220:d=1", 0)):
            run("ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", src, f"{d}/t.wav")
            assert len(static_runs(f"{d}/t.wav")) == want, src
    with tempfile.TemporaryDirectory() as d:        # rotation: least used wins; ties -> unused longest
        for n, a in (("reel-01", "a"), ("reel-02", "a"), ("reel-03", "c"), ("reel-04", "b"), ("ep01-x", "d")):
            os.makedirs(f"{d}/{n}"); json.dump({"heygen": {"avatar_id": AVATARS[a][0]}}, open(f"{d}/{n}/reel.json", "w"))
        assert next_avatar(d) == "e", next_avatar(d)               # d paused, e never used ("ep01-x" isn't a reel)
        os.makedirs(f"{d}/reel-05"); json.dump({"heygen": {"avatar_id": AVATARS["d"][0]}}, open(f"{d}/reel-05/reel.json", "w"))
        assert next_avatar(d) == "e", next_avatar(d)               # e never used
        os.makedirs(f"{d}/reel-06"); json.dump({"heygen": {"avatar_id": "old-avatar-e"}}, open(f"{d}/reel-06/reel.json", "w"))
        assert next_avatar(d) == "c", next_avatar(d)               # legacy id still counts as e; b, c, e used once, c unused longest
    from types import SimpleNamespace                              # characters: unique part ids, dance resets, sticker ok
    s = SimpleNamespace(js=[], sfx=[], html=[])
    ids = re.findall(r'id="([^"]+)"', crab(s, "kx", 0, 0, 336, prop(s, "kx-pr", "cap", "")))
    assert len(ids) == len(set(ids)) == 11 and all(i.startswith("kx") for i in ids), ids
    dance(s, "kx", 1.0, n=5); assert s.js[-1].endswith("},1.910);"), s.js[-1]
    assert sticker(s, "kst", "1f440", "left:0", 2.0).startswith('<div id="kst"') and s.html[0].count("lottie.min.js") == 1
    print("selftest ok")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]: selftest(); sys.exit()
    if len(a) < 2 or a[0] not in ("new", "heygen", "prep", "rehook", "words", "build", "render", "master", "drive", "props"): sys.exit(__doc__)
    if a[0] == "new": new(a[1], a[a.index("--ghost") + 1] if "--ghost" in a else "", a[a.index("--avatar") + 1] if "--avatar" in a else None)
    elif a[0] in ("master", "drive"): globals()[a[0]](a[1], a[2] if len(a) > 2 else None)
    elif a[0] == "props": props(a[1], a[2:])
    elif a[0] == "rehook": rehook(a[1], a[2], a[a.index("--name") + 1] if "--name" in a else "b", a[a.index("--opening") + 1] if "--opening" in a else "")
    else: globals()[a[0]](a[1])
