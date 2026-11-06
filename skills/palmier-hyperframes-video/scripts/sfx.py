#!/usr/bin/env python3
"""Step 06: sound effects generated from the placed graphics, as one stem to drop on an SFX track at frame 0.

usage: sfx.py SPEC.json OUT.wav [--cues CUES.json] [--fps 30] [--peak -24]
  SPEC.json  graphics.py spec: every element's "start" frame + "style" (pop -> pop.mp3, slide -> whoosh-short.mp3)
  CUES.json  optional extra actions: [{"frame": F, "sfx": "key-press"}, {"frame": F, "end": F2, "sfx": "typing"}, ...]
             ("sfx": "none" on an element id in SPEC silences it: {"element": "id", "sfx": "none"})
Each hit is peak-normalised to --peak dBFS (default -24, i.e. well under -17 LUFS speech), so effects mark actions
without competing with the voice. Bank: media-use's bundled Pixabay SFX (commercial use OK, see its CREDITS.md).
media-use is a HyperFrames skill you install next to this one; set MEDIA_USE_SFX_DIR to point anywhere else.
Timeline frames are the 1x edit's; a later export speed-up moves the hits with the picture.
"""
import argparse, json, os, subprocess, sys
import numpy as np

def _bank():
    """MEDIA_USE_SFX_DIR, else media-use next to this skill (where it is linked, then where it really is), else ~/.claude/skills."""
    if os.environ.get("MEDIA_USE_SFX_DIR"): return os.environ["MEDIA_USE_SFX_DIR"]
    rel = os.path.join("media-use", "audio", "assets", "sfx")
    for f in (os.path.abspath(__file__), os.path.realpath(__file__)):
        d = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(f))), rel)
        if os.path.isdir(d): return d
    return os.path.expanduser(os.path.join("~/.claude/skills", rel))


BANK = _bank()
SR = 48000
LEAD = {"whoosh-short": 0.12, "pop": 0.0, "typing": 0.0, "key-press": 0.02, "click-soft": 0.0}  # s before the frame


def load(name):
    if not os.path.isdir(BANK): sys.exit(f"SFX bank not found at {BANK}: install the media-use skill next to this one or set MEDIA_USE_SFX_DIR")
    raw =subprocess.run(["ffmpeg", "-v", "error", "-i", f"{BANK}/{name}.mp3", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def mix(hits, fps, peak_db):
    """hits: [(frame, sfx, end_frame|None)] -> stereo float32 array."""
    cache, g = {}, 10 ** (peak_db / 20)
    end = max((e or f) for f, _, e in hits) / fps + 2 if hits else 1
    out = np.zeros((int(end * SR), 2), np.float32)
    for f, name, e in hits:
        if name not in cache:
            x = load(name); cache[name] = x / (np.abs(x).max() + 1e-9) * g
        x = cache[name]
        if e:  # loop for the action's length, short fades at the ends
            n = int((e - f) / fps * SR); x = np.tile(x, (n // len(x) + 1, 1))[:n].copy()
            r = min(len(x) // 4, int(0.05 * SR)); fade = np.linspace(0, 1, r)[:, None]; x[:r] *= fade; x[-r:] *= fade[::-1]
        s = max(0, int((f / fps - LEAD.get(name, 0)) * SR)); out[s:s + len(x)] += x[:len(out) - s]
    return out


def hits_from(spec, cues):
    mute = {c["element"] for c in cues if c.get("sfx") == "none" and "element" in c}
    h = [(v["start"], "pop" if v.get("style", "pop") == "pop" else "whoosh-short", None)
         for e, v in spec["elements"].items() if e not in mute]
    h += [(c["frame"], c["sfx"], c.get("end")) for c in cues if "frame" in c and c.get("sfx") != "none"]
    return sorted(h)


def selftest():
    spec = {"elements": {"a": {"start": 30, "style": "pop"}, "b": {"start": 90, "style": "slide"}, "c": {"start": 120}}}
    cues = [{"element": "c", "sfx": "none"}, {"frame": 0, "end": 60, "sfx": "typing"}]
    h = hits_from(spec, cues); assert h == [(0, "typing", 60), (30, "pop", None), (90, "whoosh-short", None)], h
    a = mix(h, 30, -24); pk = 20 * np.log10(np.abs(a).max())
    assert -24.5 < pk < -18, pk                                   # overlaps may sum a little above a single hit
    assert np.abs(a[int(1.1 * SR):int(1.15 * SR)]).max() > 0      # pop lands at 1.0 s
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]: selftest(); sys.exit()
    ap = argparse.ArgumentParser(); ap.add_argument("spec"); ap.add_argument("out"); ap.add_argument("--cues")
    ap.add_argument("--fps", type=float, default=30); ap.add_argument("--peak", type=float, default=-24)
    a = ap.parse_args()
    h = hits_from(json.load(open(a.spec)), json.load(open(a.cues)) if a.cues else [])
    x = mix(h, a.fps, a.peak)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "pcm_s24le", a.out],
                   input=x.tobytes(), check=True)
    print(json.dumps({"out": a.out, "hits": len(h), "seconds": round(len(x) / SR, 1)}))
