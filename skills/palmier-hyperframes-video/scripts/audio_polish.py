#!/usr/bin/env python3
"""Step 03 audio polish: dialogue to about -17 LUFS with peaks at or under -6 dBFS, remuxed with the SAME video stream.

usage: audio_polish.py SRC.mp4 OUT.mov [--lufs -17] [--peak -6]
Chain (verified on a real episode): highpass 70 Hz -> gentle compression (2.5:1) -> gain to target -> limiter. Video is stream-copied
and audio is PCM in .mov, so the result swaps onto existing clips with swap_clip_media (same duration, same frames).
Prints the measured result; exits non-zero when it misses the target by more than 1 LU or the peak is over.
Leave platform loudness (-14 LUFS) to finish.py.
"""
import argparse, json, re, subprocess, sys

PRE = "highpass=f=70,acompressor=threshold=0.1:ratio=2.5:attack=5:release=120:knee=4"


def measure(path, af=None):
    cmd = ["ffmpeg", "-hide_banner", "-i", path, "-vn", "-af", (af + "," if af else "") + "ebur128=peak=true", "-f", "null", "-"]
    tail = subprocess.run(cmd, capture_output=True, text=True).stderr; tail = tail[tail.rindex("Summary:"):]
    return float(re.search(r"I:\s+(-?[\d.]+)", tail).group(1)), float(re.search(r"Peak:\s+(-?[\d.]+)", tail).group(1))


def chain(i_pre, lufs=-17.0, peak=-6.0):
    return f"{PRE},volume={lufs - i_pre:.2f}dB,alimiter=limit={10 ** (peak / 20):.4f}:level=disabled"


def selftest():
    c = chain(-24.0)
    assert "volume=7.00dB" in c and "alimiter=limit=0.5012" in c, c
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]: selftest(); sys.exit()
    ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("out")
    ap.add_argument("--lufs", type=float, default=-17); ap.add_argument("--peak", type=float, default=-6)
    a = ap.parse_args()
    i_pre, _ = measure(a.src, PRE); af = chain(i_pre, a.lufs, a.peak)
    subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", a.src, "-map", "0:v", "-map", "0:a", "-c:v", "copy",
                    "-af", af, "-c:a", "pcm_s24le", "-ar", "48000", a.out], check=True)
    i, p = measure(a.out)
    print(json.dumps({"out": a.out, "lufs": i, "peak_dbfs": p, "chain": af}))
    sys.exit(0 if abs(i - a.lufs) <= 1 and p <= a.peak + 0.5 else "audio polish missed its target: see report")
