#!/usr/bin/env python3
"""Step 5b zooms: shot list -> eased zoom/pan keyframes on every Screen clip piece, baked webcam always hidden.

usage: zooms.py TIMELINE.json SHOTS.json > calls.json      (calls for palmier_mcp.mjs: set_keyframes position + scale)
       [--track Screen] [--only A:B] [--pip 0.749,0.754] [--overlay-top 0.754] [--ease 21] [--chain 45]
SHOTS.json: [{"from": F, "to": F, "focus": [x0, y0, x1, y1]}, ...] timeline frames, focus box in SOURCE coords
            (optional "hide": max share of the focus box allowed under the camera overlay, default 0.05;
             "hard": start zoomed with no ease-in (a cut into new content); "cut": hold to "to" with no ease-out;
             optional "rect": [x0, y0, w] to force a window).
Each shot holds a window that fits the focus box (12% margin, at most 2.2x), eases in/out over --ease frames
(cubic in-out, written as dense linear rows: Palmier's "smooth" overshoots holds), and pans directly to the next shot
when the gap is under --chain frames. The baked webcam (source corner --pip) must stay hidden at every frame: under the camera overlay
(canvas top --overlay-top: x0 <= pip_x*(1-w), y0 <= pip_y - overlay_top*w) or outside the window (left of it or above it).
--only A:B writes only pieces overlapping [A, B) (a fix to one stretch); without it every piece of the track is rewritten.
"""
import argparse, json, sys

PIP, OVT = (0.749, 0.754), 0.754


def hidden(f, x0, y0, w, cam=(0.749, 0.754)):
    a0, b0, a1, b1 = (f[0] - x0) / w, (f[1] - y0) / w, (f[2] - x0) / w, (f[3] - y0) / w
    ix = max(0, min(a1, 1) - max(a0, cam[0])); iy = max(0, min(b1, 1) - max(b0, cam[1]))
    return ix * iy / max(1e-9, (a1 - a0) * (b1 - b0))


def safe(x0, y0, w, pip=PIP, ovt=OVT, eps=2e-4):
    """Baked webcam invisible: under the camera overlay, or outside the window (left of it or above it)."""
    return (x0 <= pip[0] * (1 - w) + eps and y0 <= pip[1] - ovt * w + eps) or x0 + w <= pip[0] + eps or y0 + w <= pip[1] + eps


def solve(f, hide=0.05, margin=1.12, wmin=0.45, pip=PIP, ovt=OVT):
    """Smallest window (x0, y0, w) in source coords that shows the focus box with the baked webcam hidden: pushed under
    the overlay (mode A), or left out of the window entirely (B: window left of it, C: above it). B and C let text at the
    bottom-left or top-right zoom properly (Claude Code prints its newest output at the bottom)."""
    w = min(max(max(f[2] - f[0], f[3] - f[1]) * margin, wmin), 1.0)
    while w < 1.0:
        lx, ly = max(0, f[2] - w), max(0, f[3] - w)
        for hx, hy in [(min(f[0], 0.995 - w, pip[0] * (1 - w)), min(f[1], 1 - w, pip[1] - ovt * w)),   # A
                       (min(f[0], 0.995 - w, pip[0] - w), min(f[1], 1 - w)),                            # B
                       (min(f[0], 0.995 - w), min(f[1], 1 - w, pip[1] - w))]:                           # C
            if lx <= hx and ly <= hy:
                cx, cy = (f[0] + f[2]) / 2 - w / 2, (f[1] + f[3]) / 2 - w / 2
                for x0, y0 in [(min(max(cx, lx), hx), min(max(cy, ly), hy)), (hx, hy)]:
                    if hidden(f, x0, y0, w) <= hide: return (round(x0, 4), round(y0, 4), round(w, 4))
        w = round(w + 0.01, 4)
    return (0.0, 0.0, 1.0)


def ease(u): return 4 * u ** 3 if u < .5 else 1 - (-2 * u + 2) ** 3 / 2
def lerp(a, b, u): return tuple(x + (y - x) * u for x, y in zip(a, b))


def path(a, b, u, pip=PIP, ovt=OVT):
    """Window at eased progress u from a to b. A straight move between modes can show the baked webcam mid-way
    (e.g. 1x -> a bottom-left window): then zoom first and pan second (or the reverse), whichever keeps it hidden."""
    ok = lambda p, q: all(safe(*lerp(p, q, k / 20), pip=pip, ovt=ovt) for k in range(21))
    if ok(a, b): return lerp(a, b, u)
    for m in [(b[0], a[1], b[2]), (a[0], b[1], b[2]), (a[0], b[1], a[2]), (b[0], a[1], a[2])]:
        if ok(a, m) and ok(m, b): return lerp(a, m, u * 2) if u < .5 else lerp(m, b, u * 2 - 1)
    return lerp(a, b, u)


def window_fn(shots, n_ease=21, chain=45, **kw):
    pk = {k: kw[k] for k in ("pip", "ovt") if k in kw}
    full = (0.0, 0.0, 1.0)
    S = sorted(({**s, "win": tuple(s["rect"]) if "rect" in s else solve(s["focus"], s.get("hide", 0.05), **kw)} for s in shots), key=lambda s: s["from"])
    def win(f):
        for i, s in enumerate(S):
            prev = S[i - 1] if i and s["from"] - S[i - 1]["to"] < chain else None
            start = prev["win"] if prev else full
            nxt = S[i + 1] if i + 1 < len(S) and S[i + 1]["from"] - s["to"] < chain else None
            if s["from"] <= f < s["from"] + n_ease and not s.get("hard"): return path(start, s["win"], ease((f - s["from"]) / n_ease), **pk)
            if s.get("hard") and s["from"] <= f < s["from"] + n_ease: return s["win"]
            if s["from"] + n_ease <= f < s["to"]: return s["win"]
            if not nxt and not s.get("cut") and s["to"] <= f < s["to"] + n_ease: return path(s["win"], full, ease((f - s["to"]) / n_ease), **pk)
            if nxt and s["to"] <= f < nxt["from"]: return s["win"]
        return full
    return win, S


def calls(tl, shots, track="Screen", only=None, n_ease=21, chain=45, **kw):
    win, S = window_fn(shots, n_ease, chain, **kw)
    moving = {f for s in S for f in list(range(s["from"], s["from"] + n_ease + 1)) + list(range(s["to"], s["to"] + n_ease + 1))}
    out = []
    for c in (c for t in tl["tracks"] if t.get("name") == track for c in t.get("clips", [])):
        a, b = c["frames"]
        if only and not (a < only[1] and only[0] < b): continue
        fr = sorted({a, b - 1} | {f for f in range(a, b) if f in moving} | {s[k] + d for s in S for k in ("from", "to") for d in (-1, 0) if a <= s[k] + d < b})
        ws = [(f, win(f)) for f in fr]
        if not only and all(w == (0.0, 0.0, 1.0) for _, w in ws) and not c.get("keyframes", {}).get("scale"): continue
        out.append(["set_keyframes", {"clipId": c["id"], "property": "position", "keyframes": [[f - a, round(-x / w, 5), round(-y / w, 5), "linear"] for f, (x, y, w) in ws]}])
        out.append(["set_keyframes", {"clipId": c["id"], "property": "scale", "keyframes": [[f - a, round(1 / w, 5), round(1 / w, 5), "linear"] for f, (x, y, w) in ws]}])
    return out


def selftest():
    x0, y0, w = solve((0.37, 0.33, 0.75, 0.60))
    assert x0 <= PIP[0] * (1 - w) + 1e-9 and y0 <= PIP[1] - OVT * w + 1e-9 and 1 / w <= 2.23, (x0, y0, w)
    tl = {"tracks": [{"name": "Screen", "clips": [{"id": "A", "frames": [0, 100]}, {"id": "B", "frames": [100, 300]}]}]}
    c = calls(tl, [{"from": 50, "to": 200, "focus": [0.3, 0.05, 0.75, 0.2]}])
    sc = {x[1]["clipId"]: x[1]["keyframes"] for x in c if x[1]["property"] == "scale"}
    assert sc["A"][0][1] == 1.0 and sc["A"][-1][1] > 1.5 and sc["B"][-1][1] == 1.0, sc   # eases in inside A, out inside B
    # bottom-left text (Claude Code's newest output) now zooms properly, and no frame of the move shows the webcam
    x0, y0, w = solve((0.30, 0.74, 0.67, 0.98)); assert w < 0.5 and safe(x0, y0, w), (x0, y0, w)
    win, _ = window_fn([{"from": 0, "to": 60, "focus": [0.30, 0.74, 0.67, 0.98]}, {"from": 70, "to": 130, "focus": [0.42, 0.42, 0.9, 0.68]}])
    assert all(safe(*win(f)) for f in range(0, 160)), [f for f in range(160) if not safe(*win(f))]
    win, _ = window_fn([{"from": 0, "to": 50, "focus": [0.3, 0.1, 0.6, 0.3], "cut": True}, {"from": 100, "to": 150, "focus": [0.3, 0.1, 0.6, 0.3], "hard": True}])
    assert win(49)[2] < 1 and win(50) == (0.0, 0.0, 1.0) and win(100)[2] < 1, (win(49), win(50), win(100))
    # a "cut" end holds to its last frame inside one clip (keyframe on to-1, not a ramp to the full frame at "to")
    tl = {"tracks": [{"name": "Screen", "clips": [{"id": "C", "frames": [0, 200]}]}]}
    sc = {x[1]["property"]: x[1]["keyframes"] for x in calls(tl, [{"from": 10, "to": 100, "focus": [0.3, 0.1, 0.6, 0.3], "cut": True}])}["scale"]
    assert {r[0]: r[1] for r in sc}[99] > 1.5 and {r[0]: r[1] for r in sc}[100] == 1.0, sc
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]: selftest(); sys.exit()
    ap = argparse.ArgumentParser(); ap.add_argument("timeline"); ap.add_argument("shots"); ap.add_argument("--track", default="Screen")
    ap.add_argument("--only"); ap.add_argument("--pip", default="0.749,0.754"); ap.add_argument("--overlay-top", type=float, default=0.754)
    ap.add_argument("--ease", type=int, default=21); ap.add_argument("--chain", type=int, default=45)
    a = ap.parse_args(); only = tuple(map(int, a.only.split(":"))) if a.only else None
    print(json.dumps(calls(json.load(open(a.timeline)), json.load(open(a.shots)), a.track, only, a.ease, a.chain,
                           pip=tuple(map(float, a.pip.split(","))), ovt=a.overlay_top)))
