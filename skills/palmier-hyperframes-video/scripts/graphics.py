#!/usr/bin/env python3
"""Step 5b Build: brand graphics as transparent PNGs, placed and animated in Palmier.

usage:
  graphics.py render SPEC.json OUTDIR             # HTML -> cropped transparent PNG per element + OUTDIR/boxes.json
  graphics.py place  SPEC.json REFS.json SLOT     # add_clips calls (stdout) for one overlap slot -> new top track
  graphics.py keys   SPEC.json OUTDIR/boxes.json TIMELINE.json REFS.json   # set_keyframes calls (stdout)
  graphics.py --selftest

SPEC.json: {"css": "<brand CSS>", "head": "<font <link> tags>", "canvas": [3840, 2160],
            "elements": {"id": {"html": "<absolutely positioned element>", "start": F, "end": F, "slot": 1,
                                "style": "pop" | "slide", "rot": 0}}}
REFS.json maps element id -> Palmier mediaRef after import_media. Elements whose time ranges overlap need different
slots: one auto-created track per slot (same-time clips on one track overwrite each other).

Why this shape: PNG + Palmier keyframes stay editable in the app. Palmier keyframe semantics: position = TOP-LEFT,
scale = normalized width/height (not a factor), so animation is computed around each element's own centre. Chrome
headless can write the screenshot and hang: poll for the file, then kill it. CSS mask-image with file:// URLs renders
nothing; recolor logos into PNGs and use <img>.
"""
import glob, json, os, shutil, subprocess, sys, tempfile, time
MAC_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def find_chrome():
    """$CHROME, else the Mac app, else a Playwright Chromium under /opt/pw-browsers, else Chrome/Chromium on PATH."""
    if os.environ.get("CHROME"): return os.environ["CHROME"]
    if os.path.exists(MAC_CHROME): return MAC_CHROME
    on_path = [p for p in map(shutil.which, ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")) if p]
    pw = sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome"), reverse=True)
    assert on_path or pw, "no Chrome found: set CHROME=/path/to/chrome"
    return (pw + on_path)[0]  # Playwright's first: the cloud's google-chrome wrapper hangs headless


def render(spec, outdir):
    from PIL import Image
    CHROME = find_chrome()
    os.makedirs(outdir, exist_ok=True); W, H = spec.get("canvas", [3840, 2160]); boxes = {}
    for eid, el in spec["elements"].items():
        page, shot, prof = f"{outdir}/{eid}.html", f"{outdir}/{eid}_full.png", tempfile.mkdtemp(prefix="chrome_")
        open(page, "w").write(f"<!doctype html><html><head><meta charset=utf-8>{spec.get('head', '')}<style>"
                              f"html,body{{margin:0;background:transparent;width:{W}px;height:{H}px;overflow:hidden}}{spec.get('css', '')}"
                              f"</style></head><body>{el['html']}</body></html>")
        p = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                              *(["--no-sandbox"] if os.name == "posix" and os.geteuid() == 0 else []),  # Chrome refuses to start as root otherwise (cloud)
                              f"--user-data-dir={prof}", "--default-background-color=00000000", f"--window-size={W},{H}",
                              "--virtual-time-budget=8000", f"--screenshot={shot}", f"file://{os.path.abspath(page)}"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(300):
            if p.poll() is not None or (os.path.exists(shot) and os.path.getsize(shot) > 0): break
            time.sleep(0.1)
        time.sleep(0.5); p.kill(); p.wait(); shutil.rmtree(prof, ignore_errors=True)
        im = Image.open(shot).convert("RGBA"); bb = im.getbbox()
        assert bb, f"{eid}: rendered nothing (fonts/images blocked?)"
        x0, y0, x1, y1 = max(0, bb[0] - 4), max(0, bb[1] - 4), min(W, bb[2] + 4), min(H, bb[3] + 4)
        x1 -= (x1 - x0) % 2; y1 -= (y1 - y0) % 2
        im.crop((x0, y0, x1, y1)).save(f"{outdir}/{eid}.png"); os.remove(shot); boxes[eid] = [x0, y0, x1, y1]
    json.dump(boxes, open(f"{outdir}/boxes.json", "w"), indent=1)
    return boxes


def oc(u): return 1 - (1 - u) ** 3
def ic(u): return u ** 3
def lerp(a, b, u): return a + (b - a) * u


def state(style, f, n, rot=0):
    """(scale factor, dy, opacity, blur px, rotation) at clip frame f of n."""
    IN, OUT = (10, 7) if style == "pop" else (9, 7)
    k, dy, op, bl, r = 1.0, 0.0, 1.0, 0.0, rot
    if f < IN:
        u = f / IN
        if style == "pop":
            k = lerp(0.6, 1.07, oc(u / 0.6)) if u < 0.6 else lerp(1.07, 1.0, (u - 0.6) / 0.4); r = lerp(rot * 4, rot, oc(u))
        else:
            k = lerp(0.92, 1.0, oc(u)); dy = lerp(0.035, 0.0, oc(u))
        op = min(1.0, f / 4); bl = lerp(16, 0, oc(min(1.0, f / 6)))
    elif f >= n - OUT:
        u = (f - (n - OUT) + 1) / OUT
        k = lerp(1.0, 0.88 if style == "pop" else 0.97, ic(u)); dy = 0.0 if style == "pop" else lerp(0, 0.02, ic(u))
        op = 1 - u; bl = lerp(0, 10, ic(u))
    return k, dy, op, bl, r


def keyrows(box, n, style, rot=0, canvas=(3840, 2160)):
    W, H = canvas; x0, y0, x1, y1 = box; w, h = (x1 - x0) / W, (y1 - y0) / H; cx, cy = (x0 + x1) / 2 / W, (y0 + y1) / 2 / H
    rows = {"scale": [], "position": [], "opacity": [], "blur": [], "rotation": []}
    for f in sorted(set(range(0, 11)) | set(range(max(0, n - 8), n))):
        k, dy, o, b, r = state(style, f, n, rot)
        rows["scale"].append([f, round(w * k, 5), round(h * k, 5), "linear"])
        rows["position"].append([f, round(cx - w * k / 2, 5), round(cy - h * k / 2 + dy, 5), "linear"])
        rows["opacity"].append([f, round(o, 4), "linear"]); rows["blur"].append([f, round(b, 2), "linear"]); rows["rotation"].append([f, round(r, 3), "linear"])
    if not (style == "pop" and rot): del rows["rotation"]
    return rows


def selftest():
    k, dy, o, b, r = state("pop", 0, 100); assert (k, o) == (0.6, 0.0) and b == 16
    assert state("pop", 30, 100) == (1.0, 0.0, 1.0, 0.0, 0)
    assert abs(state("slide", 99, 100)[2]) < 1e-9
    rows = keyrows([0, 0, 384, 216], 60, "slide")
    hold = {r[0]: r for r in rows["position"]}[10]
    assert hold[1:3] == [0.0, 0.0] and rows["opacity"][-1][1] == 0, hold
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]: selftest(); sys.exit()
    cmd, spec = sys.argv[1], json.load(open(sys.argv[2])); E = spec["elements"]
    if cmd == "render": print(json.dumps(render(spec, sys.argv[3]), indent=1))
    elif cmd == "place":
        refs, slot = json.load(open(sys.argv[3])), int(sys.argv[4])
        print(json.dumps([["add_clips", {"entries": [{"mediaRef": refs[e], "startFrame": v["start"], "endFrame": v["end"]}
                                                     for e, v in E.items() if v.get("slot", 1) == slot]}]]))
    elif cmd == "keys":
        boxes, tl, refs = json.load(open(sys.argv[3])), json.load(open(sys.argv[4])), json.load(open(sys.argv[5]))
        by = {(c.get("mediaRef"), c["frames"][0]): c for t in tl["tracks"] for c in t.get("clips", [])}; calls = []
        for e, v in E.items():
            c = by.get((refs[e], v["start"]))
            if not c: print(f"skip {e}: not on the timeline at {v['start']}", file=sys.stderr); continue
            n = c["frames"][1] - c["frames"][0]
            for prop, rows in keyrows(boxes[e], n, v.get("style", "pop"), v.get("rot", 0), tuple(spec.get("canvas", [3840, 2160]))).items():
                calls.append(["set_keyframes", {"clipId": c["id"], "property": prop, "keyframes": rows}])
        print(json.dumps(calls))
