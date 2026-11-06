#!/usr/bin/env python3
"""Privacy gate: tight blur boxes on sensitive words only (never whole panels), following scrolls.

usage: privacy_scan.py SRC.mp4 TIMELINE.json TERMS.txt PLAN.json [--track Screen] [--media REF] [--step 15] [--jobs 10]
                       [--cache OCR_CACHE.json]
       privacy_scan.py --splits PLAN.json                   (split_clips list: every segment start after the first)
       privacy_scan.py --ops PLAN.json TIMELINE_AFTER.json  (mask delete/create ops for scripts/masks_apply.mjs)
       privacy_scan.py --sweep SRC TIMELINE.json TERMS.txt [MEDIA]  (final gate: every 3rd frame of masked clips -> create ops)
       privacy_scan.py --cover TIMELINE.json TERMS.txt OCR_CACHE.json [MEDIA]  (gate: every cached frame vs its clip's masks; exit 1 + create ops)
       privacy_scan.py --check FRAME.png TERMS.txt          (OCR a rendered frame; exit 1 if a sensitive word is readable)
--cache keeps every OCR word per source frame, so a recut or a new term re-plans without re-OCR (37 min -> seconds on a real episode).
TIMELINE "-" scans the whole source (intake: warm the cache in the background while the rough cut is made). Samples sit
on a fixed grid (every --step source frames) plus each still stretch's ends, so later timeline runs reuse the cache.
TERMS.txt: one term per line, matched case-insensitively as a substring of an OCR word (client/business names:
"acme", "bestbarber"); "a b" matches consecutive words ("best barber"); "re:<regex>" matches a single word
(account IDs, links with IDs); "line:<regex>" matches a visual text line and blurs all of it (street addresses).
Lines starting with # are comments.

Per clip (SOURCE frames): a low-res frame difference splits the clip into still stretches and motion bursts (scrolls,
page loads). Still stretches are OCR'd (tesseract, gray + red plane) at both ends and every --step frames; their boxes are the union of
the matched words. A burst (2+ moving frames, a few tenths of a second for flick scrolls) gets the bounding box of
what moved plus the boxes of its neighbours. Writes [{clip, frames, trimStart, segments: [{src: [a, b), boxes:
[[x0, y0, x1, y1], ...], burst}], words}] in normalized source coordinates (the space of Palmier rectangle masks).
Apply in Palmier: split_clips with --splits, re-read the timeline, then `node masks_apply.mjs PROJECT TIMELINE ops.json`
with --ops (only masks named "privacy blur" are touched; unchanged boxes are kept). Then verify: capture_frame at
frames inside each segment and run --check on them (masks have no keyframes; zooms don't move them).
"""
import argparse, json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np

PX, PY = 0.004, 0.006          # padding around a word box
LW, LH = 480, 270              # motion analysis size
CORNER = (0.74, 0.74)          # baked webcam (bottom-right) is ignored by motion detection; the camera overlay covers it


def load_terms(path):
    words, phrases, regs, lines = [], [], [], []
    for t in (l.strip() for l in open(path)):
        if not t or t.startswith("#"): continue
        if t.startswith("re:"): regs.append(re.compile(t[3:], re.I))
        elif t.startswith("line:"): lines.append(re.compile(t[5:]))
        elif " " in t: phrases.append(t.lower().split())
        else: words.append(t.lower())
    return words, phrases, regs, lines


def visual_lines(rows):
    """Group word indexes into visual lines: same centre height, gaps under 2.5 word heights (pixel boxes)."""
    out = []
    for i in sorted(range(len(rows)), key=lambda i: rows[i][0]):
        x0, y0, x1, y1 = rows[i][:4]; h = y1 - y0
        for L in out:
            l = rows[L[-1]]
            if abs((l[1] + l[3]) / 2 - (y0 + y1) / 2) < 0.5 * h and -h < x0 - l[2] < 2.5 * h: L.append(i); break
        else: out.append([i])
    return out


def match(rows, terms):
    """rows: [(x0,y0,x1,y1,text)] pixel boxes in reading order -> the rows that are sensitive."""
    words, phrases, regs, lines = terms; hit = set()
    norm = [re.sub(r"[^\w@./:?=&%-]", "", r[4]).lower() for r in rows]
    for i, w in enumerate(norm):
        if any(t in w for t in words) or any(r.search(rows[i][4]) for r in regs): hit.add(i)
        for p in phrases:
            if [re.sub(r"\W", "", x) for x in norm[i:i + len(p)]] == p: hit.update(range(i, i + len(p)))
    if lines:
        for L in visual_lines(rows):
            if any(r.search(" ".join(rows[i][4] for i in L)) for r in lines): hit.update(L)
    return [rows[i] for i in sorted(hit)]


def tesseract(png):
    tsv = subprocess.run(["tesseract", "stdin", "stdout", "--psm", "11", "tsv"], input=png, capture_output=True).stdout.decode()
    rows = []
    for line in tsv.splitlines()[1:]:
        f = line.split("\t")
        if len(f) == 12 and f[11].strip() and float(f[10]) >= 0:   # low-confidence words kept: blue links OCR at 5-35
            x, y, bw, bh = map(int, f[6:10]); rows.append((x, y, x + bw, y + bh, f[11]))
    return rows


PLANES = ("format=gray", "format=rgb24,extractplanes=r")   # red on dark (e.g. a red headline on a dark page) vanishes in gray


def ocr(src, frame=None, fps=30):
    """Every word on a source frame (or an image file when frame is None), OCR'd on gray AND the red plane."""
    seek = ["-ss", f"{frame / fps:.3f}"] if frame is not None else []
    return [r for vf in PLANES for r in tesseract(subprocess.run(["ffmpeg", "-v", "error", *seek, "-i", src, "-frames:v", "1", "-vf", vf,
                                                                  "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout)]


def pad(b, px=PX, py=PY): return [max(0, b[0] - px), max(0, b[1] - py), min(1, b[2] + px), min(1, b[3] + py)]
def hit(a, b): return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]
def hull(a, b): return [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]


def merge(boxes):
    bs = [list(b[:4]) for b in boxes]; changed = True
    while changed:
        changed = False
        for i in range(len(bs)):
            for j in range(i + 1, len(bs)):
                if hit(bs[i], bs[j]): bs[i] = hull(bs[i], bs[j]); bs.pop(j); changed = True; break
            if changed: break
    return sorted([round(v, 4) for v in b] for b in bs)


def motion(frames, thr=0.8, gap=6):
    """frames: (n, LH, LW) uint8 -> [(a, b, kind, bbox)] covering 0..n: kind 'still' or 'burst' (relative frame indexes)."""
    f = frames.astype(np.int16); n = len(f)
    keep = np.ones((LH, LW), bool); keep[:int(.03 * LH)] = False; keep[int(CORNER[1] * LH):, int(CORNER[0] * LW):] = False
    diff = np.abs(np.diff(f, axis=0)) * keep if n > 1 else np.zeros((0, LH, LW))
    d = np.concatenate([[0], diff.mean(axis=(1, 2))]) if n > 1 else np.zeros(1)
    runs = []
    for i in np.where(d > thr)[0]:   # frame i differs from i-1: the change happens between them
        if runs and i - runs[-1][1] <= gap: runs[-1][1] = i
        else: runs.append([i, i])
    segs, pos = [], 0
    for a, b in runs:
        if b == a:                                    # instant switch (page load): boundary only
            if a > pos: segs.append((pos, a, "still", None)); pos = a
            continue
        a0, b1 = max(a - 1, pos), min(b + 1, n)       # include the frame before and after the change
        m = (diff[a - 1:b] > 12).any(axis=0); ys, xs = np.nonzero(m)
        bbox = pad([xs.min() / LW, ys.min() / LH, (xs.max() + 1) / LW, (ys.max() + 1) / LH], .01, .015) if len(xs) else None
        if a0 > pos: segs.append((pos, a0, "still", None))
        segs.append((a0, b1, "burst", bbox)); pos = b1
    if pos < n: segs.append((pos, n, "still", None))
    return [(int(a), int(b), k, [float(v) for v in bb] if bb else None) for a, b, k, bb in segs if b > a]   # plain types for json


def lowres(src, start, n, fps):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{start / fps:.3f}", "-i", src, "-frames:v", str(n),
                          "-vf", f"scale={LW}:{LH},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8); return a[: len(a) // (LW * LH) * LW * LH].reshape(-1, LH, LW)


def runs(clips, cap=1800):
    """Clips grouped into contiguous SOURCE runs (pieces of one take), so each frame is decoded once: [[start, n, [(clip, offset)]]]."""
    out = []
    for c in sorted(clips, key=lambda c: c.get("trimStartFrame", 0)):
        ts, n = c.get("trimStartFrame", 0), c["frames"][1] - c["frames"][0]
        if out and out[-1][0] + out[-1][1] == ts and out[-1][1] + n <= cap: out[-1][2].append((c, out[-1][1])); out[-1][1] += n
        else: out.append([ts, n, [(c, 0)]])
    return out


def ops(plan_, tl, media=None, track="Screen"):
    """Mask ops that make every piece's "privacy blur" masks equal its plan segment's boxes (keep matches, delete the rest)."""
    segs = [(r["frames"][0] + s["src"][0] - r["trimStart"], r["frames"][0] + s["src"][1] - r["trimStart"], s["boxes"]) for r in plan_ for s in r["segments"]]
    out = []
    for c in (c for t in tl["tracks"] if t.get("name") == track for c in t.get("clips", []) if not media or c.get("mediaRef") == media):
        a, b = c["frames"]; want = [s[2] for s in segs if s[0] <= a and b <= s[1]]
        assert len(want) <= 1 and (want or not any(s[0] < b and a < s[1] for s in segs)), f"split first: {c['id']} {c['frames']}"
        want, used = (want[0] if want else []), set()
        for m in (m for m in c.get("masks", []) if m.get("name") == "privacy blur"):
            g = m["geometry"]; box = [g["centerX"] - g["width"] / 2, g["centerY"] - g["height"] / 2, g["centerX"] + g["width"] / 2, g["centerY"] + g["height"] / 2]
            j = next((i for i, w in enumerate(want) if i not in used and max(abs(x - y) for x, y in zip(w, box)) < 2e-3), None)
            if j is None: out.append(["delete", c["id"], m["maskId"]])
            else: used.add(j)
        out += [["create", c["id"], w] for i, w in enumerate(want) if i not in used]
    return out


def plan(segs, boxes_at):
    """segs: [(a, b, kind, bbox)] source frames; boxes_at: {frame: [boxes]} OCR results -> segments with merged boxes."""
    seen = [merge(pad(x) for f in sorted(boxes_at) if a <= f < b for x in boxes_at[f]) for a, b, k, _ in segs]
    sensitive = any(boxes_at.values())
    out = []
    for i, (a, b, k, bbox) in enumerate(segs):
        if k == "still": bx = seen[i]
        else:   # moving text OCRs unreliably (e.g. a PDF opening): blur what moves whenever the clip shows anything sensitive
            near = [x for j in (i - 1, i + 1) if 0 <= j < len(segs) and segs[j][2] == "still" for x in seen[j]]
            bx = merge(near + seen[i] + ([bbox] if bbox and sensitive else []))
        if out and out[-1]["boxes"] == bx: out[-1]["src"][1] = b
        else: out.append({"src": [a, b], "boxes": bx, "burst": k == "burst"})
    return out


def sweep(src, tl, terms, media=None, track="Screen", step=3, spread=10, jobs=10, fps=30):
    """Final privacy gate + fix: OCR every `step`-th frame of each masked clip (gray + red); a sensitive word that the clip's
    masks don't cover becomes a box on that clip and on its same-source neighbours within `spread` frames (OCR misses a word
    on some frames, so one hit covers the stretch). Returns create ops for masks_apply.mjs."""
    clips = [c for t in tl["tracks"] if t.get("name") == track for c in t.get("clips", []) if c.get("masks") and (not media or c.get("mediaRef") == media)]
    w, h = map(int, subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", src],
                                   capture_output=True, text=True).stdout.strip().split(","))
    def boxes(c): return [[m["geometry"]["centerX"] - m["geometry"]["width"] / 2, m["geometry"]["centerY"] - m["geometry"]["height"] / 2,
                           m["geometry"]["centerX"] + m["geometry"]["width"] / 2, m["geometry"]["centerY"] + m["geometry"]["height"] / 2] for m in c["masks"]]
    have = {c["id"]: boxes(c) for c in clips}
    js = [(c, c["frames"][0] + f - c["trimStartFrame"], f) for c in clips
          for f in sorted(set(range(c["trimStartFrame"], c["trimStartFrame"] + c["frames"][1] - c["frames"][0], step)) | {c["trimStartFrame"] + c["frames"][1] - c["frames"][0] - 1})]
    with ThreadPoolExecutor(jobs) as ex: res = list(ex.map(lambda j: (j, match(ocr(src, j[2], fps), terms)), js))
    want = {}
    for (c, tf, sf), rows in res:
        for r in rows:
            b = [r[0] / w, r[1] / h, r[2] / w, r[3] / h]
            if covered(b, have[c["id"]]) < .9:
                for n in clips:
                    if n["frames"][0] - spread <= tf < n["frames"][1] + spread and abs((n["trimStartFrame"] - n["frames"][0]) - (sf - tf)) <= 1:
                        want.setdefault(n["id"], []).append(pad(b))
    return [["create", cid, b] for cid, bs in want.items() for b in merge(bs) if covered(b, have[cid]) < .9]


def cover(tl, terms, cache, media=None, track="Screen", w=3840, h=2160):
    """Gate after every recut or mask merge (a labelled "AppID: ..." card once shipped unblurred): match every cached
    OCR frame inside each clip against its masks; create ops for anything under 90% covered. Seconds, no new OCR."""
    out = []
    for c in (c for t in tl["tracks"] if t.get("name") == track for c in t.get("clips", []) if not media or c.get("mediaRef") == media):
        g = [m["geometry"] for m in c.get("masks", []) if m.get("name") == "privacy blur"]
        have = [[x["centerX"] - x["width"] / 2, x["centerY"] - x["height"] / 2, x["centerX"] + x["width"] / 2, x["centerY"] + x["height"] / 2] for x in g]
        a = c.get("trimStartFrame", 0); want = []
        for f in range(a, a + c["frames"][1] - c["frames"][0]):
            for r in match([tuple(x) for x in cache.get(str(f), cache.get(f, []))], terms):
                b = [r[0] / w, r[1] / h, r[2] / w, r[3] / h]
                if covered(b, have) < .9: want.append(pad(b))
        out += [["create", c["id"], b] for b in merge(want)]
    return out


def covered(b, boxes):
    a = max((b[2] - b[0]) * (b[3] - b[1]), 1e-9)
    return sum(max(0, min(b[2], x[2]) - max(b[0], x[0])) * max(0, min(b[3], x[3]) - max(b[1], x[1])) for x in boxes) / a


def selftest():
    terms = (["acme", "bestbarber"], [["best", "barber"]], [re.compile(r"\b\d{3}-\d{3}-\d{4}\b")], [re.compile(r"\d+ \w+ St\b")])
    rows = [(0, 0, 60, 20, "ACCOUNT"), (70, 0, 90, 20, "ID:"), (100, 0, 200, 20, "555-010-4477"), (0, 40, 30, 60, "Best"),
            (40, 40, 90, 60, "Barber,"), (0, 80, 200, 100, "@ACMESWEETS_TOWNSVILLE"), (0, 120, 60, 140, "barber."),
            (0, 160, 30, 180, "123"), (40, 160, 100, 180, "Main"), (110, 160, 130, 180, "St"), (140, 160, 160, 180, "E,"),
            (400, 160, 460, 180, "Budget")]
    got = [r[4] for r in match(rows, terms)]
    assert got == ["555-010-4477", "Best", "Barber,", "@ACMESWEETS_TOWNSVILLE", "123", "Main", "St", "E,"], got
    fr = np.zeros((30, LH, LW), np.uint8); fr[:, 50:60, 100:200] = 200
    for i in range(10, 14): fr[i:] = 0; fr[i:, 50 - 5 * (i - 9):60 - 5 * (i - 9), 100:200] = 200   # 4-frame scroll up
    fr[20:, 200:240, 50:150] = 255                                                                 # instant change
    segs = motion(fr)
    assert [(a, b, k) for a, b, k, _ in segs] == [(0, 9, "still"), (9, 14, "burst"), (14, 20, "still"), (20, 30, "still")], segs
    p = plan([(100 + a, 100 + b, k, bb) for a, b, k, bb in segs], {100: [[.2, .2, .3, .22]], 108: [[.2, .2, .3, .22]], 113: [[.2, .1, .3, .12]], 119: [[.2, .1, .3, .12]], 125: [[.2, .1, .3, .12]]})
    assert [x["src"] for x in p] == [[100, 109], [109, 114], [114, 130]] and p[1]["burst"], p
    b = p[1]["boxes"][0]; assert b[1] <= .1 and b[3] >= .22, p   # burst box covers the whole scroll path
    assert abs(covered([0, 0, 1, 1], [[0, 0, .5, 1]]) - .5) < 1e-9
    cl = [{"id": "A", "frames": [0, 10], "trimStartFrame": 100}, {"id": "B", "frames": [10, 30], "trimStartFrame": 110}, {"id": "C", "frames": [30, 40], "trimStartFrame": 500}]
    assert [(r[0], r[1], [c["id"] for c, _ in r[2]]) for r in runs(cl)] == [(100, 30, ["A", "B"]), (500, 10, ["C"])]
    pl = [{"clip": "B", "frames": [10, 30], "trimStart": 110, "segments": [{"src": [110, 130], "boxes": [[.1, .1, .2, .2]]}]}]
    tl = {"tracks": [{"name": "Screen", "clips": [{"id": "B", "frames": [10, 30], "masks": [
        {"name": "privacy blur", "maskId": "m1", "geometry": {"centerX": .15, "centerY": .15, "width": .1, "height": .1}},
        {"name": "privacy blur", "maskId": "m2", "geometry": {"centerX": .5, "centerY": .5, "width": .1, "height": .1}}]}]}]}
    assert ops(pl, tl) == [["delete", "B", "m2"]], ops(pl, tl)
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]: selftest(); sys.exit()
    if sys.argv[1:2] == ["--splits"]:
        print(json.dumps([{"clipId": r["clip"], "atFrame": r["frames"][0] + x["src"][0] - r["trimStart"]} for r in json.load(open(sys.argv[2])) for x in r["segments"][1:]])); sys.exit()
    if sys.argv[1:2] == ["--ops"]:
        print(json.dumps(ops(json.load(open(sys.argv[2])), json.load(open(sys.argv[3])), sys.argv[4] if len(sys.argv) > 4 else None))); sys.exit()
    if sys.argv[1:2] == ["--sweep"]:   # --sweep SRC TIMELINE TERMS [MEDIA]
        print(json.dumps(sweep(sys.argv[2], json.load(open(sys.argv[3])), load_terms(sys.argv[4]), sys.argv[5] if len(sys.argv) > 5 else None))); sys.exit()
    if sys.argv[1:2] == ["--cover"]:   # --cover TIMELINE TERMS CACHE [MEDIA]: every cached frame of every clip, in seconds
        tl, terms, cache = json.load(open(sys.argv[2])), load_terms(sys.argv[3]), json.load(open(sys.argv[4]))
        out = cover(tl, terms, cache, sys.argv[5] if len(sys.argv) > 5 else None)
        print(json.dumps(out)); sys.exit(1 if out else 0)
    if sys.argv[1:2] == ["--check"]:
        if not os.path.isfile(sys.argv[2]): sys.exit(f"--check: no such image {sys.argv[2]}")   # a missing file once read as "clean"
        bad = match(ocr(sys.argv[2]), load_terms(sys.argv[3]))
        print(json.dumps([[r[4]] + list(r[:4]) for r in bad])); sys.exit(1 if bad else 0)
    ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("timeline"); ap.add_argument("terms"); ap.add_argument("out")
    ap.add_argument("--track", default="Screen"); ap.add_argument("--step", type=int, default=15); ap.add_argument("--jobs", type=int, default=10)
    ap.add_argument("--media", help="only clips whose mediaRef is SRC's Palmier media id")
    ap.add_argument("--cache", help="JSON of every OCR word per source frame; reused and extended on each run")
    a = ap.parse_args()
    pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate:format=duration",
                         "-of", "json", a.src], capture_output=True, text=True).stdout
    pj = json.loads(pr); st = pj["streams"][0]; w, h = st["width"], st["height"]; num, den = map(int, st["r_frame_rate"].split("/"))
    if a.timeline == "-":   # whole source in 1800-frame pieces
        n = int(float(pj["format"]["duration"]) * num / den)
        tl = {"fps": round(num / den), "tracks": [{"name": a.track, "clips": [{"id": f"src{i}", "frames": [i, min(i + 1800, n)], "trimStartFrame": i, "mediaRef": a.media}
                                                                        for i in range(0, n, 1800)]}]}
    else: tl = json.load(open(a.timeline))
    fps = tl.get("fps", 30)
    terms = load_terms(a.terms)
    clips = [c for t in tl["tracks"] if t.get("name") == a.track for c in t.get("clips", []) if not a.media or c.get("mediaRef") == a.media]

    def segs_of(run):
        fr = lowres(a.src, run[0], run[1], fps)
        return [(c["id"], [(run[0] + o + x, run[0] + o + y, k, bb) for x, y, k, bb in motion(fr[o:o + c["frames"][1] - c["frames"][0]])]) for c, o in run[2]]
    with ThreadPoolExecutor(4) as ex: byid = dict(x for r in ex.map(segs_of, runs(clips)) for x in r)
    allsegs = [byid[c["id"]] for c in clips]
    cache = {int(k): v for k, v in json.load(open(a.cache)).items()} if a.cache and os.path.exists(a.cache) else {}
    jobs = sorted({(i, f) for i, segs in enumerate(allsegs) for x, y, k, _ in segs for f in ([x, y - 1] + list(range(x - x % a.step + a.step, y, a.step)) if k == "still" else range(x, y, 3))})
    todo = sorted({f for _, f in jobs} - set(cache))
    with ThreadPoolExecutor(a.jobs) as ex:
        for f, rows in zip(todo, ex.map(lambda f: ocr(a.src, f, fps), todo)): cache[f] = rows
    if a.cache: json.dump(cache, open(a.cache, "w"))
    res = [(i, f, match([tuple(r) for r in cache[f]], terms)) for i, f in jobs]
    found, words = [{} for _ in clips], [set() for _ in clips]
    for i, f, rows in res: found[i][f] = [[r[0] / w, r[1] / h, r[2] / w, r[3] / h] for r in rows]; words[i].update(r[4] for r in rows)
    out = [{"clip": c["id"], "frames": c["frames"], "trimStart": c.get("trimStartFrame", 0), "segments": plan(segs, bx), "words": sorted(ws)}
           for c, segs, bx, ws in zip(clips, allsegs, found, words) if ws]
    json.dump(out, open(a.out, "w"), indent=0)
    print(json.dumps({"clips": len(clips), "ocr_frames": len(todo), "cached_frames": len(jobs) - len(todo), "clips_with_hits": len(out), "segments": sum(len(r["segments"]) for r in out),
                      "bursts": sum(s["burst"] for r in out for s in r["segments"]), "masks": sum(len(s["boxes"]) for r in out for s in r["segments"])}))
