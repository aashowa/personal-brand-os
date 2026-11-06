#!/usr/bin/env python3
"""episode-shorts pipeline: one command per step. SHORTS.json is the episode's config (see SKILL.md).

  shorts.py transcript SHORTS.json [--from S] [--to S]   long-form sentences with 1x timeline times (pick cut lists here)
  shorts.py cut        SHORTS.json NAME                  voice.wav + camera.mp4 + words.json -> <shorts>/NAME/assets
                                                         (prints duration and the repaired-camera windows to cover)
  shorts.py grade      OUT.cube RAW.png GRADED.png [RAW GRADED ...]   fit a 3D LUT that reproduces the long-form grade
  shorts.py photos     search "QUERY" OUTDIR | get ID NAME PHOTOS_DIR   free Unsplash photos (never Unsplash+), with credits
  shorts.py build      SHORTS.json NAME                  _build/NAME.py -> index.html, footage clips, sfx.wav
  shorts.py privacy    SHORTS.json                       OCR every footage clip (3 fps, 2x) with the privacy terms; exit 1 on a leak
  shorts.py deliver    SHORTS.json                       renders/NAME.mp4 -> -14 LUFS (video stream-copied), verify,
                                                         clone into OUTPUT_DIR/Shorts (+ the long-form into OUTPUT_DIR/Long-form)
  shorts.py --selftest
"""
import glob, json, os, re, subprocess, sys

KIT = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, KIT)
import shorts_kit as K

PRIVACY = os.path.join(os.path.dirname(os.path.dirname(KIT)), "palmier-hyperframes-video", "scripts", "privacy_scan.py")


def run(*a, **k): return subprocess.run([str(x) for x in a], check=True, **k)


# ---------- timeline mapping (Palmier get_timeline dump, Dialogue track)
def dialogue(cfg):
    tl = json.load(open(cfg["timeline"]))
    return [c for t in tl["tracks"] if t["name"] == cfg.get("dialogue_track", "Dialogue") for c in t["clips"]]


def pieces(clips, edl, fps):
    """EDL (1x timeline seconds) -> [(src_f0, src_f1, starts_piece, ends_piece)]; source-contiguous splits are merged."""
    out = []
    for a, b in edl:
        fa, fb = round(a * fps), round(b * fps); seg = []
        for c in clips:
            f0, f1 = c["frames"]; lo, hi = max(fa, f0), min(fb, f1)
            if lo < hi:
                s0 = c["trimStartFrame"] + lo - f0; s1 = s0 + hi - lo
                if seg and seg[-1][1] == s0: seg[-1][1] = s1     # privacy splits are contiguous in the source
                else: seg.append([s0, s1])
        out += [(s0, s1, i == 0, i == len(seg) - 1) for i, (s0, s1) in enumerate(seg)]
    return out


def timeline_words(clips, words, fps):
    """Source-time words -> [(t, text)] on the 1x timeline, in timeline order."""
    out = []
    for c in clips:
        f0, f1 = c["frames"]; s0 = c["trimStartFrame"] / fps; s1 = s0 + (f1 - f0) / fps
        out += [(f0 / fps + ws - s0, t) for ws, we, t in words if s0 <= ws < s1]
    return sorted(out)


def short_words(P, words, fps, speed):
    res, o = [], 0.0
    for s0, s1, *_ in P:
        a, b = s0 / fps, s1 / fps
        res += [[round((o + ws - a) / speed, 3), round((o + min(we, b) - a) / speed, 3), t] for ws, we, t in words if a - 0.02 <= ws < b - 0.03]
        o += b - a
    return res, o / speed


def repaired_windows(P, ranges, offset, fps, speed):
    """Camera frames the long-form repaired by interpolation smear at half-screen size: final-time windows to cover."""
    out, o = [], 0
    for s0, s1, *_ in P:
        for a, b in ranges:
            lo, hi = max(s0 + offset, a), min(s1 + offset, b)
            if lo < hi: out.append((round((o + lo - s0 - offset) / fps / speed, 2), round((o + hi - s0 - offset) / fps / speed, 2)))
        o += s1 - s0
    return out


# ---------- commands
def cmd_transcript(cfg, lo=0.0, hi=1e9):
    sent, start = [], None
    for t, w in timeline_words(dialogue(cfg), json.load(open(cfg["words"])), cfg["fps"]):
        if not lo <= t < hi: continue
        if start is None: start = t
        sent.append(w)
        if re.search(r"[.?!]$", w) or len(sent) > 40:
            print(f"{int(start // 60)}:{start % 60:05.2f}  ({start:.2f})  {' '.join(sent)}"); sent, start = [], None
    if sent: print(f"{int(start // 60)}:{start % 60:05.2f}  ({start:.2f})  {' '.join(sent)}")


def cmd_cut(cfg, name):
    fps, sp = cfg["fps"], cfg["speed"]; out = os.path.join(cfg["dir"], name, "assets"); os.makedirs(out, exist_ok=True)
    P = pieces(dialogue(cfg), cfg["shorts"][name]["edl"], fps)
    w, dur = short_words(P, json.load(open(cfg["words"])), fps, sp)
    json.dump({"duration": round(dur, 3), "words": w}, open(f"{out}/words.json", "w"), indent=0)
    fl, lab = [], []                                          # voice: one trim per piece, 12 ms fades at every cut
    for i, (s0, s1, first, last) in enumerate(P):
        f = f"[0:a]atrim=start={s0 / fps:.4f}:end={s1 / fps:.4f},asetpts=PTS-STARTPTS"
        if first: f += ",afade=t=in:d=0.012"
        if last: f += f",afade=t=out:st={(s1 - s0) / fps - 0.012:.4f}:d=0.012"
        fl.append(f + f"[a{i}]"); lab.append(f"[a{i}]")
    fl.append("".join(lab) + f"concat=n={len(P)}:v=0:a=1,atempo={sp}[out]")
    run("ffmpeg", "-v", "error", "-y", "-i", cfg["voice"], "-filter_complex", ";".join(fl), "-map", "[out]", "-ar", 48000, "-c:a", "pcm_s24le", f"{out}/voice.wav")
    x, y, cw, ch = cfg["camera_crop"]; off = cfg.get("camera_offset", 0); tmp = os.path.join(cfg["dir"], "_build", f"tmp_{name}")
    os.makedirs(tmp, exist_ok=True); lst = []
    vf = f"crop={cw}:{ch}:{x}:{y},scale=1080:960:flags=lanczos" + (f",lut3d={cfg['lut']}:interp=tetrahedral" if cfg.get("lut") else "")
    for i, (s0, s1, *_) in enumerate(P):
        p = f"{tmp}/c{i:03d}.mp4"; lst.append(f"file '{p}'")
        run("ffmpeg", "-v", "error", "-y", "-ss", f"{(s0 + off) / fps:.4f}", "-i", cfg["camera"], "-frames:v", s1 - s0, "-vf", vf,
            "-an", "-c:v", "libx264", "-crf", 12, "-preset", "fast", "-pix_fmt", "yuv420p", p)
    open(f"{tmp}/list.txt", "w").write("\n".join(lst))
    run("ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", 0, "-i", f"{tmp}/list.txt", "-vf", f"setpts=(PTS-STARTPTS)/{sp},fps={fps}",
        "-c:v", "libx264", "-crf", 16, "-preset", "medium", "-pix_fmt", "yuv420p", "-g", fps, "-bf", 0, "-movflags", "+faststart", f"{out}/camera.mp4")
    for f in glob.glob(f"{tmp}/*"): os.remove(f)
    os.rmdir(tmp)
    rep = repaired_windows(P, json.load(open(cfg["repaired"]))["ranges"], off, fps, sp) if cfg.get("repaired") else []
    print(json.dumps({"short": name, "duration": round(dur, 3), "pieces": len(P), "cover_full_screen": rep}))


def cmd_grade(out, pairs):
    import numpy as np
    from PIL import Image
    X, Y = [], []
    for raw, gr in zip(pairs[::2], pairs[1::2]):
        a = Image.open(raw).convert("RGB"); b = Image.open(gr).convert("RGB").resize(a.size)
        X.append(np.asarray(a, float).reshape(-1, 3) / 255); Y.append(np.asarray(b, float).reshape(-1, 3) / 255)
    X, Y = np.concatenate(X), np.concatenate(Y); g256 = np.arange(256); curves = []
    for c in range(3):                                         # per-channel curve from binned medians, smoothed
        bins = np.clip((X[:, c] * 255).astype(int), 0, 255); med = np.full(256, np.nan)
        for i in range(256):
            m = bins == i
            if m.sum() > 30: med[i] = np.median(Y[m, c])
        ok = ~np.isnan(med); med = np.interp(g256, g256[ok], med[ok])
        curves.append(np.convolve(np.pad(med, 4, mode="edge"), np.ones(9) / 9, "valid"))
    N = 17; idx = np.clip(np.round(X * (N - 1)).astype(int), 0, N - 1); key = idx[:, 0] * N * N + idx[:, 1] * N + idx[:, 2]
    cnt = np.bincount(key, minlength=N ** 3); res = np.zeros((N ** 3, 3))
    for c in range(3): res[:, c] = np.bincount(key, weights=Y[:, c] - np.interp(X[:, c] * 255, g256, curves[c]), minlength=N ** 3)
    res = np.where(cnt[:, None] > 50, res / np.maximum(cnt, 1)[:, None], 0)    # hue-specific residual where data is dense
    g = np.linspace(0, 1, N); rows = []
    for b in range(N):
        for gg in range(N):
            for r in range(N):
                v = np.array([np.interp(x * 255, g256, curves[c]) for c, x in enumerate((g[r], g[gg], g[b]))])
                rows.append(np.clip(v + res[r * N * N + gg * N + b], 0, 1))
    with open(out, "w") as fh:
        fh.write(f"LUT_3D_SIZE {N}\n"); fh.writelines(f"{o[0]:.5f} {o[1]:.5f} {o[2]:.5f}\n" for o in rows)
    for raw, gr in zip(pairs[::2], pairs[1::2]):              # report: mean abs error before / after (0-255)
        fit = subprocess.run(["ffmpeg", "-v", "error", "-i", raw, "-vf", f"lut3d={out}:interp=tetrahedral", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
        a = np.asarray(Image.open(raw).convert("RGB"), float); b = np.asarray(Image.open(gr).convert("RGB").resize(a.shape[1::-1]), float)
        f = np.frombuffer(fit, np.uint8).reshape(a.shape).astype(float)
        print(f"{os.path.basename(raw)}: error {np.abs(a - b).mean():.1f} -> {np.abs(f - b).mean():.1f}")


def unsplash_json(url):
    out = subprocess.run(["curl", "-s", url], capture_output=True, text=True).stdout
    try: return json.loads(out)
    except ValueError: sys.exit(f"Unsplash did not answer with JSON (a bot challenge or rate limit; its napi endpoint can block a machine): {out[:120]!r}")


def cmd_photos(args):
    import urllib.parse
    if args[0] == "search":                                     # contact sheet of free results; ids on the tiles
        from PIL import Image, ImageDraw
        q, outdir = args[1], args[2]; os.makedirs(outdir, exist_ok=True)
        d = unsplash_json("https://unsplash.com/napi/search/photos?per_page=24&query=" + urllib.parse.quote(q))
        free = [r for r in d["results"] if not (r.get("premium") or r.get("plus"))][:8]; tiles = []
        for r in free:
            fn = f"{outdir}/{r['id']}.jpg"; run("curl", "-sfL", r["urls"]["small"], "-o", fn)
            im = Image.open(fn).convert("RGB"); im.thumbnail((360, 360)); ImageDraw.Draw(im).rectangle([0, 0, 150, 16], fill="black")
            ImageDraw.Draw(im).text((3, 3), r["id"], fill="yellow"); tiles.append(im)
        sheet = Image.new("RGB", (360 * 4, 360 * 2), "white")
        for i, im in enumerate(tiles): sheet.paste(im, ((i % 4) * 360, (i // 4) * 360))
        sheet.save(f"{outdir}/sheet.jpg", quality=80)
        print(json.dumps([{"id": r["id"], "by": r["user"]["name"], "alt": r.get("alt_description")} for r in free], indent=0)); print("sheet:", f"{outdir}/sheet.jpg")
    elif args[0] == "get":                                      # full photo at 1600 px + credits.json entry
        pid, name, pdir = args[1], args[2], args[3]; os.makedirs(pdir, exist_ok=True)
        r = unsplash_json(f"https://unsplash.com/napi/photos/{pid}")
        if r.get("premium") or r.get("plus"): sys.exit(f"{pid} is Unsplash+ (paid licence): pick another")
        run("curl", "-sfL", r["urls"]["raw"] + "&w=1600&q=85&fm=jpg", "-o", f"{pdir}/{name}.jpg")
        cp = f"{pdir}/credits.json"; cr = json.load(open(cp)) if os.path.exists(cp) else {}
        cr[name] = {"file": f"{name}.jpg", "id": pid, "unsplash": r["links"]["html"], "by": r["user"]["name"], "license": "Unsplash License (free; not Unsplash+)"}
        json.dump(cr, open(cp, "w"), indent=1); print("saved", f"{pdir}/{name}.jpg", "by", r["user"]["name"])


def cmd_privacy(cfg):
    leaks = n = 0
    for clip in sorted(glob.glob(os.path.join(cfg["dir"], "*", "assets", "f*.mp4"))):
        d = os.path.join("/tmp", "shorts_privacy", os.path.basename(os.path.dirname(os.path.dirname(clip))) + "_" + os.path.basename(clip)[:-4])
        os.makedirs(d, exist_ok=True); [os.remove(f) for f in glob.glob(f"{d}/*.png")]
        run("ffmpeg", "-v", "error", "-y", "-i", clip, "-vf", "fps=3,scale=iw*2:ih*2:flags=lanczos", f"{d}/%03d.png")
        for fr in sorted(glob.glob(f"{d}/*.png")):
            n += 1; r = subprocess.run([sys.executable, PRIVACY, "--check", fr, cfg["terms"]], capture_output=True, text=True)
            if r.returncode: leaks += 1; print("LEAK", fr, r.stdout.strip()[:300])
    print(f"checked {n} frames, {leaks} with a readable sensitive word"); sys.exit(1 if leaks else 0)


def loud(path):
    t = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    t = t[t.rindex("Summary:"):]
    return float(re.search(r"I:\s+(-?[\d.]+)", t).group(1)), float(re.search(r"Peak:\s+(-?[\d.]+)", t).group(1))


def cmd_deliver(cfg):
    desk = cfg["output_dir"]; os.makedirs(f"{desk}/Shorts", exist_ok=True); ok = True
    for name, sh in cfg["shorts"].items():
        src = os.path.join(cfg["dir"], name, "renders", f"{name}.mp4"); dst = os.path.join(cfg["dir"], sh.get("file", name) + ".mp4")
        e = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", "loudnorm=I=-14:TP=-1:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
        m = json.loads(e[e.rindex("{"):e.rindex("}") + 1])
        ln = (f"loudnorm=I=-14:TP=-1:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
              f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000")
        run("ffmpeg", "-v", "error", "-y", "-i", src, "-map", "0:v", "-map", "0:a", "-c:v", "copy", "-af", ln, "-c:a", "aac", "-b:a", "320k",
            "-ar", 48000, "-movflags", "+faststart", dst)                    # picture untouched: no second video encode
        dec = subprocess.run(["ffmpeg", "-v", "error", "-i", dst, "-f", "null", "-"], capture_output=True, text=True).stderr.strip()
        I, tp = loud(dst)
        d0, d1 = (float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout) for f in (src, dst))
        good = not dec and abs(I + 14) <= 0.5 and tp <= -0.9 and abs(d0 - d1) < 0.05; ok &= good
        desk_file = f"{desk}/Shorts/{sh.get('title', name)}.mp4"
        if good: run("cp", "-c", dst, desk_file)                            # APFS clone: no extra disk
        print(json.dumps({"short": name, "file": dst, "duration": d1, "decode_errors": len(dec.splitlines()) if dec else 0,
                          "lufs": I, "true_peak": tp, "output": desk_file if good else None}))
    lf = cfg.get("longform")
    if lf and os.path.exists(lf["file"]):
        os.makedirs(f"{desk}/Long-form", exist_ok=True); run("cp", "-c", lf["file"], f"{desk}/Long-form/{lf['title']}.mp4")
        print(json.dumps({"longform": f"{desk}/Long-form/{lf['title']}.mp4"}))
    sys.exit(0 if ok else 1)


def selftest():
    clips = [{"frames": [0, 100], "trimStartFrame": 1000}, {"frames": [100, 130], "trimStartFrame": 1100}, {"frames": [130, 300], "trimStartFrame": 5000}]
    P = pieces(clips, [[0, 5.0], [6.0, 8.0]], 30)
    assert P[0][:2] == (1000, 1130) and P[0][2] and not P[0][3], P     # contiguous privacy split merged
    assert P[1][:2] == (5000, 5020) and P[2][:2] == (5050, 5110) and P[2][2] and P[2][3], P
    tw = timeline_words(clips, [[33.5, 33.7, "hi"], [168.0, 168.2, "yo"]], 30)
    assert [round(t, 2) for t, _ in tw] == [0.17, 5.67], tw
    w, dur = short_words(P, [[33.5, 33.7, "hi"], [168.4, 168.6, "yo"]], 30, 1.0)
    assert round(dur, 2) == 7.0 and w[1][0] == 5.067, (w, dur)
    assert repaired_windows(P, [[5060, 5080]], 0, 30, 1.0) == [(5.33, 6.0)]
    s = K.Short.__new__(K.Short); s.edl, s.speed = [[10.0, 12.0], [20.0, 25.0]], 1.0
    assert s.v5(1.97) == 20.0 and abs(s.v5(1.97, end=True) - 11.97) < 1e-9 and s.v5(3.0) == 21.0   # cut-aware mapping
    print("selftest ok")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"): print(__doc__); sys.exit()
    if a[0] == "--selftest": selftest(); sys.exit()
    if a[0] == "grade": cmd_grade(a[1], a[2:]); sys.exit()
    if a[0] == "photos": cmd_photos(a[1:]); sys.exit()
    cfg = K.load(a[1])
    if a[0] == "transcript":
        lo = float(a[a.index("--from") + 1]) if "--from" in a else 0.0; hi = float(a[a.index("--to") + 1]) if "--to" in a else 1e9
        cmd_transcript(cfg, lo, hi)
    elif a[0] == "cut": cmd_cut(cfg, a[2])
    elif a[0] == "build": K.build(cfg, a[2])
    elif a[0] == "privacy": cmd_privacy(cfg)
    elif a[0] == "deliver": cmd_deliver(cfg)
    else: sys.exit(__doc__)
