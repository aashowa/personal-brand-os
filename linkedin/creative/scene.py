"""Facebook Scene image: a candid Kie photo of you at a device with a green screen, then the REAL screen composited on it.

    python3 linkedin/creative/scene.py <dir> "typing on a silver laptop at a wooden desk in a home office"
    python3 linkedin/creative/scene.py <dir> "..." --crop 400,264,2112,1400   # tighter framing (x,y,w,h on the 2512x1664 photo)

Needs <dir>/screen.png (what's on the device: a real screenshot or Reel frame, ~16:10). Writes <dir>/scene-raw-green.png
(Kie, ~10 credits, reused on re-runs), <dir>/scene-real.png and <dir>/scene.jpg (1080 wide) for <dir>/facebook.html.
The reference face is your avatar still from config.json: heygen.avatars.<slot>.still, slot = linkedin.scene_avatar
(default: the first avatar). Rules: physically possible, nothing floating, no text from the model, readable at a glance.
Facebook only.
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skills/avatar-shorts/scripts"))
import cover as C  # Kie helpers (upload, call, API, MODEL); C.R is reel.py: CONFIG (config.json), env() (.env)

PROMPT = ("A real, candid photo taken on an iPhone, natural and unposed. Over the shoulder and slightly to the side of {person}, "
          "{setting}. Their face is visible in three-quarter profile. The screen faces the camera and fills about half of the "
          "frame; the screen is a solid, flat, bright green (#00FF00), edge to edge, with no reflections. Ordinary room, natural "
          "window light, slight grain. Nothing floating, no graphics, no text, no logos, no stickers.")
PERSON = "the person in the reference image (same face, hair and clothes)"
LI = C.R.CONFIG.get("linkedin", {})


def still():
    """Your avatar still (the face Kie keeps), from heygen.avatars.<slot>.still; relative paths are from the repo root."""
    avatars = C.R.HG.get("avatars", {})
    slot = LI.get("scene_avatar") or next(iter(avatars), None)
    path = avatars.get(slot, {}).get("still")
    if not path:
        sys.exit(f"config.json needs heygen.avatars.{slot or '<slot>'}.still (a photo of you) for the scene")
    return os.path.join(C.R.ROOT, path)


def generate(d, setting):
    raw = os.path.join(d, "scene-raw-green.png")
    if os.path.exists(raw):
        return raw
    token = C.R.env("KIE_API_KEY")
    url = C.upload(still(), token)
    r = C.call(f"{C.API}/jobs/createTask", token, {"model": C.MODEL, "input": {"prompt": PROMPT.format(person=LI.get("scene_person") or PERSON, setting=setting),
                                                                               "input_urls": [url], "aspect_ratio": "3:2", "resolution": "2K"}})
    task = (r.get("data") or {}).get("taskId") or sys.exit(f"createTask failed: {r}")
    for _ in range(80):
        s = C.call(f"{C.API}/jobs/recordInfo?taskId={task}", token).get("data") or {}
        if s.get("state") in ("success", "fail"):
            break
        time.sleep(10)
    if s.get("state") != "success":
        sys.exit(f"scene {task}: {s.get('state')} {s.get('failMsg')}")
    res = json.loads(s["resultJson"])["resultUrls"][0]
    with urllib.request.urlopen(urllib.request.Request(res, headers={"User-Agent": "Mozilla/5.0"}), timeout=300) as f:
        open(raw, "wb").write(f.read())
    return raw


def composite(ph, scr):
    """Warp scr onto the photo's green screen (largest green blob, corners from its extremes), then clean the edge fringe."""
    green = lambda im, lo: cv2.inRange(cv2.cvtColor(im, cv2.COLOR_BGR2HSV), lo, (85, 255, 255))
    m = cv2.morphologyEx(green(ph, (40, 120, 120)), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    pts = max(cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0], key=cv2.contourArea).reshape(-1, 2).astype(np.float32)
    s, df = pts.sum(1), np.diff(pts, axis=1).ravel()
    quad = np.array([pts[s.argmin()], pts[df.argmin()], pts[s.argmax()], pts[df.argmax()]], np.float32)  # tl, tr, br, bl
    quad = quad.mean(0) + (quad - quad.mean(0)) * 1.012  # a hair larger: covers the green fringe under the bezel
    h, w = scr.shape[:2]
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), quad.astype(np.float32))
    warp = cv2.convertScaleAbs(cv2.GaussianBlur(cv2.warpPerspective(scr, M, ph.shape[1::-1], flags=cv2.INTER_AREA), (0, 0), 0.7), alpha=0.93, beta=4)
    a = cv2.GaussianBlur(cv2.warpPerspective(np.full((h, w), 255, np.uint8), M, ph.shape[1::-1]), (0, 0), 1.0).astype(np.float32)[..., None] / 255
    out = np.clip(ph * (1 - a) + warp * a + np.random.default_rng(7).normal(0, 3, ph.shape) * a, 0, 255).astype(np.uint8)
    qm = cv2.fillPoly(np.zeros(ph.shape[:2], np.uint8), [quad.astype(np.int32)], 255)
    band = cv2.subtract(cv2.dilate(qm, np.ones((31, 31), np.uint8)), cv2.erode(qm, np.ones((9, 9), np.uint8)))  # never the plants
    out[cv2.dilate(cv2.bitwise_and(green(out, (45, 90, 110)), band), np.ones((3, 3), np.uint8)) > 0] = (22, 22, 24)
    return out


if __name__ == "__main__":
    d, setting = os.path.abspath(sys.argv[1]), sys.argv[2]
    out = composite(cv2.imread(generate(d, setting)), cv2.imread(os.path.join(d, "screen.png")))
    cv2.imwrite(os.path.join(d, "scene-real.png"), out)
    if "--crop" in sys.argv:
        x, y, w, h = map(int, sys.argv[sys.argv.index("--crop") + 1].split(","))
        out = out[y:y + h, x:x + w]
    cv2.imwrite(os.path.join(d, "scene.jpg"), cv2.resize(out, (1080, round(out.shape[0] * 1080 / out.shape[1])), interpolation=cv2.INTER_AREA),
                [cv2.IMWRITE_JPEG_QUALITY, 92])
    print("scene ok", os.path.join(d, "scene.jpg"))
