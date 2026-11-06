"""Per-frame layout classifier: is the presenter full-screen, in a split, or off screen?
usage: python3 -I screentime.py MODELS_DIR OUT_JSON video1.mp4 [video2.mp4 ...]
"""
import sys, json, os
import cv2
import numpy as np

models, out_path, videos = sys.argv[1], sys.argv[2], sys.argv[3:]
FPS = 5  # samples per second
det = cv2.FaceDetectorYN.create(os.path.join(models, "yunet.onnx"), "", (0, 0), 0.8)
rec = cv2.FaceRecognizerSF.create(os.path.join(models, "sface.onnx"), "")


def faces(img):
    h, w = img.shape[:2]
    det.setInputSize((w, h))
    _, f = det.detect(img)
    return [] if f is None else list(f)


def embed(img, face):
    return rec.feature(rec.alignCrop(img, face))


def sample(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    step, i, nxt, out = 1.0 / FPS, 0, 0.0, []
    while True:
        ok, img = cap.read()
        if not ok:
            break
        t = i / fps
        if t >= nxt:
            out.append((t, cv2.resize(img, (720, int(img.shape[0] * 720 / img.shape[1]))) if img.shape[1] > 720 else img))
            nxt += step
        i += 1
    return out


def classify(frames):
    # Presenter reference = largest face in the last frame that has one (every Reel ends on a to-camera CTA,
    # sometimes followed by black frames).
    ref = None
    for t, img in reversed(frames):
        fs = faces(img)
        if fs:
            ref = embed(img, max(fs, key=lambda f: f[3]))
            break
    labels = []
    for t, img in frames:
        H = img.shape[0]
        lab = "asset"
        for f in faces(img):
            if ref is None or rec.match(ref, embed(img, f), cv2.FaceRecognizerSF_FR_COSINE) < 0.36:
                continue  # someone else's face inside an asset
            cy, fh = (f[1] + f[3] / 2) / H, f[3] / H
            lab = "split" if cy > 0.55 else ("face" if fh > 0.12 else "pip")
            break
        labels.append(lab)
    return labels, ref is not None


res = {}
for v in videos:
    frames = sample(v)
    labels, has_ref = classify(frames)
    n = len(labels)
    runs = [l for k, l in enumerate(labels) if k == 0 or labels[k - 1] != l]
    res[os.path.basename(v)[:-4]] = {
        "seconds": round(n / FPS, 1),
        "ref_found": has_ref,
        "pct": {k: round(100 * labels.count(k) / n, 1) for k in ("face", "split", "pip", "asset")},
        "layout_switches": len(runs) - 1,
        "timeline": "".join({"face": "F", "split": "S", "pip": "p", "asset": "."}[l] for l in labels),
    }
    print(os.path.basename(v), res[os.path.basename(v)[:-4]]["pct"], flush=True)
json.dump(res, open(out_path, "w"), indent=1)
