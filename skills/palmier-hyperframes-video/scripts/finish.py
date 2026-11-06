#!/usr/bin/env python3
"""Final: one command after the in-app export. Speed sections + platform loudness + verification + a copy in Downloads.

usage: finish.py IN_1x.mp4 OUT.mp4 [--speed "0:413:1.15,413:935:1.2,935:end:1.08"] [--lufs -14] [--tp -1]
                 [--vbit 45M] [--no-downloads]
--speed sections are timeline frames of the 1x export (fps read from the file); omit for no speed change.
Speed is applied once, to picture and audio together, with pitch-preserving atempo. Loudness is two-pass loudnorm
(linear). Music/SFX already mixed in the app at 1x keep their placement; pre-slow a music bed per section if its tempo
must survive the speed-up (see finishing.md).
Prints a verification report (durations, decode errors, integrated loudness, true peak) and fails loudly if it is off.
"""
import argparse, json, os, shutil, subprocess, sys


def sections(spec, total, fps):
    out = []
    for part in spec.split(","):
        a, b, r = part.split(":"); a = int(a); b = total if b == "end" else int(b)
        out.append((a / fps, b / fps, float(r)))
    assert all(abs(x[1] - y[0]) < 1e-9 for x, y in zip(out, out[1:])), "speed sections must be contiguous"
    return out


def graph(secs, loudnorm, video=True):
    n = len(secs); v = a = ""
    if video:
        v = f"[0:v]split={n}" + "".join(f"[p{i}]" for i in range(n)) + ";"
        v += "".join(f"[p{i}]trim={s}:{e},setpts=(PTS-STARTPTS)/{r}[v{i}];" for i, (s, e, r) in enumerate(secs))
        v += "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[v];"
    a = f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit={n}" + "".join(f"[x{i}]" for i in range(n)) + ";"
    a += "".join(f"[x{i}]atrim={s}:{e},asetpts=PTS-STARTPTS,atempo={r}[a{i}];" for i, (s, e, r) in enumerate(secs))
    a += "".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1,{loudnorm}[a]"
    return v + a


def probe(path):
    j = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path], capture_output=True, text=True).stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    num, den = map(int, v["r_frame_rate"].split("/"))
    return {"fps": num / den, "duration": float(j["format"]["duration"]), "size": f'{v["width"]}x{v["height"]}',
            "streams": {s["codec_type"]: float(s.get("duration", j["format"]["duration"])) for s in j["streams"]}}


def loudness(path):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    tail = err[err.rindex("Summary:"):]
    get = lambda key: float(tail.split(key)[1].split()[0])
    return get("I:"), get("Peak:")


def selftest():
    s = sections("0:413:1.15,413:935:1.2,935:end:1.08", 1000, 30)
    assert s[0] == (0.0, 413 / 30, 1.15) and s[-1][1] == 1000 / 30
    exp = sum((e - b) / r for b, e, r in s); assert abs(exp - (413 / 30 / 1.15 + 522 / 30 / 1.2 + 65 / 30 / 1.08)) < 1e-9
    g = graph(s, "anull"); assert g.count("atempo=") == 3 and "concat=n=3:v=1" in g
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]: selftest(); sys.exit()
    ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("out"); ap.add_argument("--speed", default="")
    ap.add_argument("--lufs", type=float, default=-14); ap.add_argument("--tp", type=float, default=-1); ap.add_argument("--vbit", default="45M")
    ap.add_argument("--no-downloads", action="store_true")
    a = ap.parse_args(); info = probe(a.src); fps = info["fps"]; total = round(info["duration"] * fps)
    secs = sections(a.speed or f"0:end:1.0", total, fps)
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", a.src, "-filter_complex", graph(secs, f"loudnorm=I={a.lufs}:TP={a.tp}:LRA=11:print_format=json", False),
                           "-map", "[a]", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
    ln = (f"loudnorm=I={a.lufs}:TP={a.tp}:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000")
    subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", a.src, "-filter_complex", graph(secs, ln), "-map", "[v]", "-map", "[a]",
                    "-r", str(fps), "-c:v", "h264_videotoolbox" if sys.platform == "darwin" else "libx264", "-b:v", a.vbit, "-profile:v", "high", "-pix_fmt", "yuv420p",
                    "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                    "-c:a", "aac", "-b:a", "320k", "-movflags", "+faststart", a.out], check=True)
    out = probe(a.out); expected = sum((e - s) / r for s, e, r in secs)
    dec = subprocess.run(["ffmpeg", "-v", "error", "-i", a.out, "-f", "null", "-"], capture_output=True, text=True).stderr.strip()
    lufs, tp = loudness(a.out)
    rep = {"out": a.out, "size": out["size"], "duration": round(out["duration"], 2), "expected": round(expected, 2),
           "streams": {k: round(v, 2) for k, v in out["streams"].items()}, "decode_errors": len(dec.splitlines()) if dec else 0,
           "lufs": lufs, "true_peak": tp}
    if not a.no_downloads:
        dl = os.path.expanduser(f"~/Downloads/{os.path.basename(a.out)}")
        if subprocess.run(["cp", "-c", a.out, dl]).returncode: shutil.copy2(a.out, dl)   # APFS clone: instant, no extra disk
        rep["downloads_copy"] = dl
    print(json.dumps(rep, indent=1))
    ok = abs(out["duration"] - expected) < 0.2 and rep["decode_errors"] == 0 and abs(lufs - a.lufs) <= 1 and tp <= a.tp + 0.5
    sys.exit(0 if ok else "verification failed: see report")
