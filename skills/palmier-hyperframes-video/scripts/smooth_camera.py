#!/usr/bin/env python3
"""Repair OBS stutter in a camera file, frame-exact.

usage: smooth_camera.py SRC REPORT.json OUT.mp4 [--size 1920x1080] [--only START:END,...] [--workers 4]

REPORT.json is footage_health.py's report; its stutter_ranges (source frames) are rebuilt with motion-compensated
interpolation (repeated frames dropped, minterpolate back to the source rate). Every other frame is copied from the
original, and the output has exactly the source frame count, so clips swapped onto it (swap_clip_media) stay in sync.
--only limits repair to source-frame spans actually used by the edit (e.g. the corner-camera clips).
Frozen ranges are NOT repaired: a second without new frames cannot be invented convincingly; cover those shots.

Why per-range: one big ffmpeg graph (split/trim/concat + mpdecimate) drifted 51 frames short, then 145 long, in a real run.
Output is H.264, 1 s GOP, no B-frames: the edit-friendly intermediate Palmier plays reliably.
"""
import argparse, json, os, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

MAC = sys.platform == "darwin"  # VideoToolbox (hardware decode/encode) exists only there
ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("report"); ap.add_argument("out")
ap.add_argument("--size", default="1920x1080"); ap.add_argument("--only"); ap.add_argument("--workers", type=int, default=4)
ap.add_argument("--margin", type=int, default=15); ap.add_argument("--encoder", default="h264_videotoolbox" if MAC else "libx264")
a = ap.parse_args()
rep = json.load(open(a.report)); N = rep["frames"]; fps = rep["fps"]; W, H = map(int, a.size.split("x")); FS = W * H * 3 // 2
R = [[max(0, s - a.margin), min(N, e + a.margin)] for s, e in rep["stutter_ranges"]]
if a.only:
    keep = [tuple(map(int, x.split(":"))) for x in a.only.split(",")]
    R = [[max(s, k0), min(e, k1)] for s, e in R for k0, k1 in keep if min(e, k1) - max(s, k0) >= 15]
R = sorted(R); merged = []
for r in R:
    if merged and r[0] <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], r[1])
    else: merged.append(r)
tmp = tempfile.mkdtemp(prefix="smooth_")


def piece(r):
    s, e = r; out = f"{tmp}/{s}.mp4"
    vf = (f"scale={W}:{H},format=yuv420p,mpdecimate=hi=64*6:lo=64*2:frac=0.5,"
          f"minterpolate=fps={fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,"
          f"tpad=stop_mode=clone:stop_duration=60,trim=end_frame={e - s}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s / fps:.6f}", "-i", a.src, "-frames:v", str(e - s), "-vf", vf,
                    "-c:v", "libx264", "-preset", "fast", "-crf", "12", "-pix_fmt", "yuv420p", out], check=True)
    n = int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v", "-show_entries", "stream=nb_read_frames",
                            "-of", "csv=p=0", out], capture_output=True, text=True).stdout)
    assert n == e - s, f"piece {s}-{e}: {n} frames"
    return out


with ThreadPoolExecutor(a.workers) as ex: files = dict(zip([s for s, _ in merged], ex.map(piece, merged)))
starts = {s: e for s, e in merged}
dec = subprocess.Popen(["ffmpeg", "-v", "error", *(["-hwaccel", "videotoolbox"] if MAC else []), "-i", a.src, "-vf", f"scale={W}:{H},format=yuv420p",
                        "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                        "-c:v", a.encoder, "-b:v", "12M", "-maxrate", "18M", "-g", str(round(fps)), "-bf", "0", "-profile:v", "high",
                        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", a.out], stdin=subprocess.PIPE)
i = written = 0
while True:
    fr = dec.stdout.read(FS)
    if len(fr) < FS: break
    if i in starts:
        e = starts[i]; p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", files[i], "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        for k in range(e - i):
            if k: fr = dec.stdout.read(FS)
            enc.stdin.write(p.stdout.read(FS)); written += 1
        p.stdout.close(); p.wait(); i = e; continue
    enc.stdin.write(fr); written += 1; i += 1
enc.stdin.close(); enc.wait()
for f in files.values(): os.remove(f)
print(json.dumps({"out": a.out, "frames": written, "source_frames": N, "repaired_ranges": merged,
                  "repaired_s": round(sum(e - s for s, e in merged) / fps, 1)}))
assert written == N, "frame count differs from the source: do not swap this file in"
