#!/usr/bin/env python3
"""QA gate on the timeline JSON: catches what a fresh-eyes reviewer would find by eye, in seconds, before any render.

usage: qa_timeline.py TIMELINE.json [--overlays Motion] [--screen Screen] [--camera Camera] [--cover Graphics]
                      [--ocr OCR_CACHE.json] [--long 240] [--min-text 0.014]
Checks (frames are timeline frames):
  overlap  two overlay graphics on screen at once whose hold boxes intersect (e.g. two tool tags stacked)
  edge     the visible card (hold box minus ~6% shadow) within 1.5% of the frame edge (reads as cut off on a phone)
  small    overlay hold box under 13% wide or 11% tall (e.g. two-word tags unreadable on a phone)
  split    one graphic cut into two clips by a ripple cut (rejoin and re-key it)
  unzoomed (warning only) an app screen at 1x for --long frames or more; with --ocr (privacy_scan cache) only when the median word height
           is under --min-text of the frame height (e.g. a browser demo)
Exit 1 when anything is found. Overlay tracks are every track whose name starts with --overlays.
"""
import argparse, json, statistics, sys


def hold(c):
    """(x0, y0, w, h) at the middle keyframe (the settled hold), or the static transform, or full frame."""
    k = c.get("keyframes", {})
    if "position" in k and "scale" in k:
        p, s = k["position"][len(k["position"]) // 2], k["scale"][len(k["scale"]) // 2]
        return p[1], p[2], s[1], s[2]
    t = c.get("transform") or {}
    w, h = t.get("width", 1), t.get("height", 1)
    return t.get("centerX", .5) - w / 2, t.get("centerY", .5) - h / 2, w, h


def inset(x, y, w, h, k=.2):
    """The card inside a PNG box: rendered graphics carry ~20% shadow/padding on each side."""
    return x + w * k, y + h * k, w * (1 - 2 * k), h * (1 - 2 * k)


def corner(c):
    """Logo-tag zone above the corner camera: one tag at a time there."""
    x, y, w, h = hold(c); return x + w / 2 > .7 and .45 < y + h / 2 < .85


def scale_at(c, f):
    """Zoom factor of a screen clip at clip-relative frame f (linear between keyframes)."""
    rows = c.get("keyframes", {}).get("scale")
    if not rows: return (c.get("transform") or {}).get("width", 1)
    if f <= rows[0][0]: return rows[0][1]
    for a, b in zip(rows, rows[1:]):
        if a[0] <= f <= b[0]: return a[1] + (b[1] - a[1]) * (f - a[0]) / max(1, b[0] - a[0])
    return rows[-1][1]


def check(tl, overlays="Motion", screen="Screen", camera="Camera", cover="Graphics", ocr=None, long=240, min_text=0.014):
    tracks = tl["tracks"]; out = []
    ov = [c for t in tracks if t["name"].startswith(overlays) for c in t.get("clips", []) if hold(c)[2] <= 1]   # wider = follows a zoom
    for c in ov:
        x, y, w, h = hold(c); cx, cy, cw, ch = inset(x, y, w, h, .06)   # the visible card: PNG box minus its ~6% shadow
        if cx < .015 or cy < .015 or cx + cw > .985 or cy + ch > .985: out.append(["edge", c["frames"][0], c["id"], [round(v, 3) for v in (x, y, w, h)]])
        if w < .13 or h < .11: out.append(["small", c["frames"][0], c["id"], [round(w, 3), round(h, 3)]])
    for i, a in enumerate(ov):
        for b in ov[i + 1:]:
            if a["frames"][0] < b["frames"][1] and b["frames"][0] < a["frames"][1]:
                (ax, ay, aw, ah), (bx, by, bw, bh) = [inset(*hold(c)) for c in (a, b)]
                if (ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah) or (corner(a) and corner(b)):
                    out.append(["overlap", max(a["frames"][0], b["frames"][0]), f'{a["id"]}+{b["id"]}', None])
            if a.get("mediaRef") == b.get("mediaRef") and (a["frames"][1] == b["frames"][0] or b["frames"][1] == a["frames"][0]):
                out.append(["split", min(a["frames"][1], b["frames"][1]), f'{a["id"]}+{b["id"]}', None])
    full = [c["frames"] for t in tracks if t["name"] in (camera, cover) for c in t.get("clips", []) if hold(c)[2] > .98]
    run = []   # (timeline frame, source frame) of visible 1x screen frames
    for c in sorted((c for t in tracks if t["name"] == screen for c in t.get("clips", [])), key=lambda c: c["frames"][0]):
        a, b = c["frames"]
        for f in range(a, b):
            covered = any(x <= f < y for x, y in full)
            if not covered and scale_at(c, f - a) < 1.05: run.append((f, c.get("trimStartFrame", 0) + f - a))
            elif run: out += flush(run, long, ocr, min_text); run = []
    out += flush(run, long, ocr, min_text)
    return sorted(out, key=lambda x: x[1])


def flush(run, long, ocr, min_text):
    if len(run) < long: return []
    if ocr:
        hs = [(r[3] - r[1]) / 2160 for f in range(run[0][1], run[-1][1] + 1) if str(f) in ocr for r in ocr[str(f)]]
        if hs and statistics.median(hs) >= min_text: return []
    return [["unzoomed", run[0][0], f"{len(run)} frames at 1x" + ("" if ocr else " (warn: no OCR cache, check text size)"), run[-1][0]]]


def selftest():
    tag = lambda i, a, b, x: {"id": i, "frames": [a, b], "mediaRef": i, "keyframes": {"position": [[0, x, .6]], "scale": [[0, .18, .15]]}}
    tl = {"tracks": [{"name": "Motion", "clips": [tag("A", 0, 80, .82)]}, {"name": "Motion2", "clips": [tag("B", 50, 120, .80), tag("C", 200, 260, .5)]},
                     {"name": "Screen", "clips": [{"id": "S", "frames": [0, 400], "trimStartFrame": 0}]},
                     {"name": "Camera", "clips": [{"id": "K", "frames": [300, 400]}]}]}
    got = {(k, f) for k, f, *_ in check(tl, long=240)}
    assert ("overlap", 50) in got and ("edge", 0) in got and ("unzoomed", 0) in got and ("small", 0) not in got, got
    assert not [x for x in check(tl, long=301) if x[0] == "unzoomed"]       # camera covers 300-400, so the 1x run is 300 long
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]: selftest(); sys.exit()
    ap = argparse.ArgumentParser(); ap.add_argument("timeline"); ap.add_argument("--overlays", default="Motion"); ap.add_argument("--screen", default="Screen")
    ap.add_argument("--camera", default="Camera"); ap.add_argument("--cover", default="Graphics"); ap.add_argument("--ocr")
    ap.add_argument("--long", type=int, default=240); ap.add_argument("--min-text", type=float, default=0.014)
    a = ap.parse_args()
    res = check(json.load(open(a.timeline)), a.overlays, a.screen, a.camera, a.cover, json.load(open(a.ocr)) if a.ocr else None, a.long, a.min_text)
    for r in res: print(json.dumps(r))
    fails = [r for r in res if r[0] != "unzoomed"]   # full screen is the default: a long 1x run is a hint only
    print(json.dumps({"issues": len(fails), "warnings": len(res) - len(fails)})); sys.exit(1 if fails else 0)
