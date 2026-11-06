#!/usr/bin/env python3
"""Intake gate: is this footage safe to edit, and where does it stutter or freeze?

usage:
  footage_health.py SRC [--crop W:H:X:Y] [--out report.json]
  footage_health.py SRC --sync REF [--ref-crop W:H:X:Y] [--window 300]   # frame offset of SRC vs REF by motion

Report:
  * edit_friendly: H.264 with no B-frames and keyframes <= 2 s. Long-GOP HEVC (OBS default) rendered random
    black stretches in Palmier: make an intermediate (see palmier.md) before placing clips.
  * per-second "real fps" = frames that differ from the previous one. OBS fills dropped frames with copies, so an
    overloaded recording shows ~8 real fps (stutter -> interpolate) or ~1 (frozen -> cover the shot).
  * stutter / frozen ranges in source frames, merged, ready for smooth_camera.py.
"""
import argparse, json, subprocess, sys
import numpy as np

W, H = 96, 54
DUP = 0.04  # mean abs diff (0-255 gray, 96x54) below this = repeated frame; sensor noise on a still shot is ~0.05-0.1


def probe(src):
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", src],
                                  capture_output=True, text=True, check=True).stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    keys = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-skip_frame", "nokey", "-show_entries",
                           "frame=pts_time", "-of", "csv=p=0", "-read_intervals", "%+60", src], capture_output=True, text=True).stdout.split()
    kt = [float(x.strip(",")) for x in keys if x.strip(",").strip()]
    gop = round(float(np.median(np.diff(kt))), 2) if len(kt) > 1 else None
    num, den = map(int, v["r_frame_rate"].split("/"))
    audio = [s for s in j["streams"] if s["codec_type"] == "audio"]
    silent = None
    if audio:
        vd = subprocess.run(["ffmpeg", "-v", "info", "-t", "120", "-i", src, "-map", "0:a:0", "-af", "volumedetect", "-f", "null", "-"],
                            capture_output=True, text=True).stderr
        mx = [l for l in vd.splitlines() if "max_volume" in l]
        silent = bool(mx) and float(mx[0].split(":")[1].split()[0]) < -60
    return {"codec": v["codec_name"], "size": f'{v["width"]}x{v["height"]}', "fps": num / den, "b_frames": int(v.get("has_b_frames", 0)),
            "gop_s": gop, "duration": float(j["format"]["duration"]), "audio_streams": len(audio), "audio_silent": silent,
            "edit_friendly": v["codec_name"] == "h264" and int(v.get("has_b_frames", 0)) == 0 and gop is not None and gop <= 2}


def motion(src, crop=None):
    vf = (f"crop={crop}," if crop else "") + f"scale={W}:{H},format=gray"
    hw = ["-hwaccel", "videotoolbox"] if sys.platform == "darwin" else []  # macOS only: elsewhere ffmpeg can't set it up and the report would silently pass bad footage
    p = subprocess.Popen(["ffmpeg", "-v", "error", *hw, "-i", src, "-vf", vf, "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    prev, d = None, []
    while True:
        b = p.stdout.read(W * H)
        if len(b) < W * H: break
        f = np.frombuffer(b, np.uint8).astype(np.int16)
        if prev is not None: d.append(np.abs(f - prev).mean())
        prev = f
    if p.wait() != 0: sys.exit(f"ffmpeg could not decode {src}: this report would pass bad footage, so no report was made")
    return np.array(d, np.float32)


def ranges(mask, fps, gap_s=2, min_s=0.5):
    idx = np.where(mask)[0]; out = []
    for i in idx:
        i = int(i)
        if out and i - out[-1][1] <= gap_s * fps: out[-1][1] = i
        else: out.append([i, i])
    return [[a, b + 1] for a, b in out if (b + 1 - a) >= min_s * fps]


def classify(d, fps):
    """per-second real fps -> stutter (worth interpolating) and frozen (cover) masks in frames."""
    n = len(d) + 1; f = int(round(fps)); real = np.zeros(n // f + 1)
    stutter = np.zeros(n, bool); frozen = np.zeros(n, bool)
    for s in range(n // f):
        w = d[s * f:(s + 1) * f]; real[s] = (w >= DUP).sum()
        if real[s] < 0.15 * f: frozen[s * f:(s + 1) * f] = True                       # ~4 real fps or fewer
        elif (w < DUP).mean() >= 0.3 and w.mean() >= 0.2: stutter[s * f:(s + 1) * f] = True  # copies while moving
    return real, stutter, frozen


def sync(a, b, window, maxlag=90):
    """lag L (frames) maximising correlation of motion: SRC frame i shows what REF shows at frame i+L."""
    a, b = a[:window], b[:window + maxlag]; best = (0, -2)
    for L in range(-maxlag, maxlag + 1):
        x = a[max(0, -L):len(a) - max(0, L)] if L >= 0 else a[-L:]
        y = b[max(0, L):max(0, L) + len(x)]
        m = min(len(x), len(y))
        if m < 100: continue
        c = np.corrcoef(x[:m], y[:m])[0, 1]
        if c > best[1]: best = (L, c)
    return best


def selftest():
    fps = 30; d = np.full(30 * 20, 0.6, np.float32)
    d[30 * 5:30 * 9] = np.tile([1.2, 0.01, 0.01, 0.01], 30)         # 4 s of 1-in-4 stutter
    d[30 * 12:30 * 16] = 0.0; d[30 * 12:30 * 16:30] = 3.0            # 4 s frozen, one new frame per second
    real, st, fr = classify(d, fps)
    assert ranges(st, fps) == [[150, 270]], ranges(st, fps)
    assert ranges(fr, fps) == [[360, 480]], ranges(fr, fps)
    sig = np.random.default_rng(0).random(3000).astype(np.float32)
    assert sync(sig[7:], sig, 2000)[0] == 7
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]: selftest(); sys.exit()
    ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("--crop"); ap.add_argument("--out")
    ap.add_argument("--sync"); ap.add_argument("--ref-crop"); ap.add_argument("--window", type=int, default=300)
    a = ap.parse_args()
    info = probe(a.src); d = motion(a.src, a.crop); fps = info["fps"]
    real, st, fr = classify(d, fps)
    rep = {"source": a.src, **info, "frames": len(d) + 1, "real_fps_median": float(np.median(real)),
           "seconds_under_10fps": int((real < 10).sum()), "stutter_ranges": ranges(st, fps), "frozen_ranges": ranges(fr, fps)}
    if a.sync:
        L, c = sync(d, motion(a.sync, a.ref_crop), int(a.window * fps))
        rep["sync"] = {"ref": a.sync, "offset_frames": L, "corr": round(float(c), 3)}
    if a.out: json.dump(rep, open(a.out, "w"), indent=1)
    s = {k: v for k, v in rep.items() if k not in ("stutter_ranges", "frozen_ranges")}
    print(json.dumps(s, indent=1))
    for k in ("stutter_ranges", "frozen_ranges"):
        print(k, len(rep[k]), "ranges,", round(sum(b - a for a, b in rep[k]) / fps, 1), "s")
