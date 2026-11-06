#!/usr/bin/env python3
"""Step 05 captions: SRT in TIMELINE time from the one cached transcription, following every cut.

usage: captions_srt.py WORDS.json TIMELINE.json OUT.srt [--track Dialogue] [--max-words 5] [--max-chars 32] [--skip START:END,...]
Words are mapped through the dialogue clips (trimStartFrame -> timeline frame), so cuts made after transcription are
honoured without re-transcribing. Cues are 1-5 words, broken at punctuation and pauses; --skip blanks spans where the
picture already shows the words (e.g. a typing hook) so captions do not compete with on-screen text.
Import the SRT into Palmier (import_media, application/x-subrip) or burn it with ffmpeg; check size in an exported frame.
"""
import argparse, json, sys


def cues(words, tl, track="Dialogue", fps=30, max_words=5, max_chars=32, skip=()):
    clips = [c for t in tl["tracks"] if t.get("name") == track for c in t["clips"]]
    placed = []
    for c in clips:
        t0, t1 = c["frames"]; s0 = c["trimStartFrame"]
        for s, e, w in words:
            if s0 <= s * fps < s0 + (t1 - t0):
                a = t0 + (s * fps - s0); b = min(t1, t0 + (e * fps - s0))
                if not any(k0 <= a < k1 for k0, k1 in skip): placed.append((a / fps, b / fps, w.strip()))
    placed.sort(); out, cur = [], []
    for i, (s, e, w) in enumerate(placed):
        cur.append((s, e, w)); nxt = placed[i + 1] if i + 1 < len(placed) else None
        text = " ".join(x[2] for x in cur)
        if (not nxt or len(cur) >= max_words or w[-1:] in ".?!," or nxt[0] - e > 0.3
                or len(text) + 1 + len(nxt[2]) > max_chars):
            end = min(nxt[0], max(e, cur[0][0] + 0.7)) if nxt else max(e, cur[0][0] + 0.7)
            out.append((cur[0][0], end, text)); cur = []
    return out


def ts(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def selftest():
    tl = {"tracks": [{"name": "Dialogue", "clips": [{"frames": [0, 60], "trimStartFrame": 300}, {"frames": [60, 120], "trimStartFrame": 600}]}]}
    words = [[10.0, 10.3, "So"], [10.4, 10.8, "this"], [11.0, 11.4, "works."], [20.0, 20.5, "Next"], [20.6, 21.0, "part"], [15.0, 15.5, "cut"]]
    c = cues(words, tl)
    assert [x[2] for x in c] == ["So this works.", "Next part"], c
    assert abs(c[0][0] - 0.0) < 1e-6 and abs(c[1][0] - 2.0) < 1e-6, c   # second clip starts at timeline 2.0 s
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]: selftest(); sys.exit()
    ap = argparse.ArgumentParser(); ap.add_argument("words"); ap.add_argument("timeline"); ap.add_argument("out")
    ap.add_argument("--track", default="Dialogue"); ap.add_argument("--max-words", type=int, default=5); ap.add_argument("--max-chars", type=int, default=32)
    ap.add_argument("--skip", default="")
    a = ap.parse_args(); tl = json.load(open(a.timeline)); fps = tl.get("fps", 30)
    skip = [tuple(map(int, x.split(":"))) for x in a.skip.split(",") if x]
    cs = cues(json.load(open(a.words)), tl, a.track, fps, a.max_words, a.max_chars, skip)
    open(a.out, "w").write("\n".join(f"{i}\n{ts(s)} --> {ts(e)}\n{t}\n" for i, (s, e, t) in enumerate(cs, 1)))
    print(json.dumps({"out": a.out, "cues": len(cs)}))
