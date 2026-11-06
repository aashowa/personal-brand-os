#!/usr/bin/env python3
"""Pauses and "um"s -> cut ranges, plus the proof gate.

usage:
  speech_gaps.py AUDIO WORDS.json --timeline TL.json [--track Dialogue] [--skip-before F] [--min 0.45] [--pad 0.13]
                 [--verify] [--out cuts.json]          # cut ranges in TIMELINE frames for ripple_delete_ranges
  speech_gaps.py AUDIO WORDS.json --timeline TL.json --gate   # exit 1 if long pauses / fillers remain (proof gate)

AUDIO is the source the dialogue clips reference (its time = trimStartFrame/fps). WORDS.json = [[start, end, word], ...]
in source seconds (one transcription, cached). TL.json = get_timeline output.

Why acoustic fillers: Whisper drops "um/uh" even with a disfluent prompt. Fillers are found as voiced sound (pitch
periodicity 75-300 Hz) that no transcript word covers; --verify transcribes each candidate alone (mlx_whisper, local)
and keeps only um/uh/ah/er/hmm, so missed real words ("and", "so", "yeah") are never cut.
Pauses are gaps between speech (words + voiced non-filler sound), so keyboard clicks and breaths no longer hide them.
"""
import argparse, json, re, subprocess, sys
import numpy as np

SR = 16000
FILLER = re.compile(r"(?i)^\W*(u+h+m*|u+m+|a+h+|e+r+m*|h+m+|m{2,})\W*(\s+\w+\W*)?$")


def load_audio(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def db10(a):
    hop = SR // 100; m = len(a) // hop
    return 20 * np.log10(np.sqrt((a[:m * hop].reshape(m, hop) ** 2).mean(1)) + 1e-9)


def voicing(x):
    n = int(0.03 * SR); v = []
    for i in range(0, len(x) - n, n // 2):
        f = x[i:i + n] - x[i:i + n].mean()
        if (f ** 2).mean() < 1e-6: continue
        ac = np.correlate(f, f, "full")[n - 1:]; ac /= ac[0] + 1e-9
        v.append(ac[SR // 300:SR // 75].max())
    return float(np.mean(np.array(v) > 0.5)) if v else 0.0


def segments(tl, track, fps):
    clips = sorted([c for t in tl["tracks"] if t.get("name") == track for c in t["clips"]], key=lambda c: c["frames"][0])
    segs = []
    for c in clips:
        t0, t1 = c["frames"]; s0 = c["trimStartFrame"]
        if segs and segs[-1][1] == t0 and segs[-1][2] + (t0 - segs[-1][0]) == s0: segs[-1][1] = t1
        else: segs.append([t0, t1, s0])
    return [(t0, t1, s0 / fps, (s0 + t1 - t0) / fps) for t0, t1, s0 in segs]


def find(audio, words, segs, fps, mn, pad, skip, verify):
    db = db10(audio); cover = np.zeros(len(db), bool)
    for s, e, _ in words: cover[max(0, int(s * 100) - 4):int(e * 100) + 4] = True
    cand = []
    for t0, t1, a, b in segs:
        lo, hi = int(a * 100), int(b * 100); snd = (db[lo:hi] > -38) & ~cover[lo:hi]; k = 0
        while k < len(snd):
            if not snd[k]: k += 1; continue
            j = k
            while j < len(snd) and (snd[j] or snd[j + 1:j + 4].any()): j += 1
            s, d = (lo + k) / 100, (j - k) / 100
            if 0.15 <= d <= 1.5 and voicing(audio[int(s * SR):int((s + d) * SR)]) >= 0.5: cand.append({"src": s, "dur": d})
            k = j
    if verify:
        import mlx_whisper
        for c in cand:
            x = audio[max(0, int((c["src"] - 0.08) * SR)):int((c["src"] + c["dur"] + 0.08) * SR)]; z = np.zeros(int(0.3 * SR), np.float32)
            c["heard"] = mlx_whisper.transcribe(np.concatenate([z, x, z]), path_or_hf_repo="mlx-community/whisper-small-mlx", language="en",
                                                initial_prompt="Um. Uh. Hmm. Mm. Ah.", temperature=0.0, condition_on_previous_text=False)["text"].strip()
    fill = [c for c in cand if FILLER.match(c.get("heard", ""))]
    speech = sorted([(s, e) for s, e, _ in words] + [(c["src"], c["src"] + c["dur"]) for c in cand if c not in fill])
    cuts, gaps = [], []
    for t0, t1, a, b in segs:
        m = []
        for s, e in [(max(s, a), min(e, b)) for s, e in speech if e > a and s < b]:
            if m and s <= m[-1][1]: m[-1][1] = max(m[-1][1], e)
            else: m.append([s, e])
        f = lambda x: t0 + round((x - a) * fps)
        for (_, e1), (s2, _) in zip(m, m[1:]):
            if s2 - e1 >= mn and f(e1 + pad) >= skip: cuts.append([f(e1 + pad), f(s2 - pad)]); gaps.append(round(s2 - e1, 2))
        for x in fill:
            if not (a <= x["src"] < b) or f(x["src"]) < skip: continue
            prev = max([e for _, e in m if e <= x["src"] + 0.01] + [a]); nxt = min([s for s, _ in m if s >= x["src"] + x["dur"] - 0.01] + [b])
            cuts.append([f(max(x["src"] - 0.02, prev + 0.05)), f(min(x["src"] + x["dur"] + 0.02, nxt - 0.05))])
    cuts = sorted(c for c in cuts if c[1] - c[0] >= 3); out = []
    for c in cuts:
        if out and c[0] <= out[-1][1]: out[-1][1] = max(out[-1][1], c[1])
        else: out.append(c)
    return out, gaps, cand, fill


def selftest():
    t = np.arange(int(4 * SR)) / SR; a = np.zeros_like(t, dtype=np.float32)
    a[(t > 0.2) & (t < 0.8)] = 0.3 * np.sin(2 * np.pi * 140 * t[(t > 0.2) & (t < 0.8)])    # word 1
    a[(t > 1.6) & (t < 1.95)] = 0.3 * np.sin(2 * np.pi * 120 * t[(t > 1.6) & (t < 1.95)])  # untranscribed hum ("um")
    a[(t > 3.0) & (t < 3.6)] = 0.3 * np.sin(2 * np.pi * 150 * t[(t > 3.0) & (t < 3.6)])    # word 2
    words = [[0.2, 0.8, "hello"], [3.0, 3.6, "world"]]
    segs = [(0, 120, 0.0, 4.0)]
    cuts, gaps, cand, fill = find(a, words, segs, 30, 0.45, 0.13, 0, False)
    assert len(cand) == 1 and abs(cand[0]["src"] - 1.6) < 0.05, cand
    # unverified candidates count as speech: two pauses around the hum get cut, the hum itself stays
    assert len(cuts) == 2 and cuts[0][0] == 28 and cuts[1][1] == 86, cuts
    cand[0]["heard"] = "Um."; assert FILLER.match(cand[0]["heard"]) and not FILLER.match("And.") and not FILLER.match("Yeah.")
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]: selftest(); sys.exit()
    ap = argparse.ArgumentParser(); ap.add_argument("audio"); ap.add_argument("words"); ap.add_argument("--timeline", required=True)
    ap.add_argument("--track", default="Dialogue"); ap.add_argument("--skip-before", type=int, default=0); ap.add_argument("--min", type=float, default=0.45)
    ap.add_argument("--pad", type=float, default=0.13); ap.add_argument("--verify", action="store_true"); ap.add_argument("--gate", action="store_true")
    ap.add_argument("--fps", type=float); ap.add_argument("--out")
    a = ap.parse_args(); tl = json.load(open(a.timeline)); fps = a.fps or tl.get("fps", 30)
    cuts, gaps, cand, fill = find(load_audio(a.audio), json.load(open(a.words)), segments(tl, a.track, fps), fps, a.min, a.pad,
                                  a.skip_before, a.verify or a.gate)
    rep = {"cuts": cuts, "removed_s": round(sum(e - s for s, e in cuts) / fps, 1), "pauses_over_min": len(gaps), "filler_candidates": len(cand),
           "fillers": [{"src": round(c["src"], 2), "heard": c.get("heard")} for c in fill]}
    if a.out: json.dump(rep, open(a.out, "w"), indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != "cuts"}, indent=1), f"\n{len(cuts)} cut ranges")
    if a.gate: sys.exit(1 if (gaps or fill) else 0)
