#!/usr/bin/env python3
"""YouTube thumbnail variants on Kie.ai (OpenAI GPT Image 2.5 Sunburst, image-to-image): 10 credits each.

usage: thumbs.py SPEC.json [VARIANT ...]
SPEC.json (paths relative to the spec's folder):
  {"refs_dir": "thumbnail-refs", "out_dir": ".", "prefix": "thumbnail-ep01", "cap": 100,
   "variants": {"v1-command": {"refs": ["me.jpg", "layout-ref.jpg", "app-logo.png"], "prompt": "Create a 16:9 ..."}}}
Writes <out_dir>/<prefix>-<variant>.jpg (1920x1080), raw PNGs in <out_dir>/thumbnail-raw/, and <spec>-receipt.json
(task ids, prompts, refs, credits before/after). A variant whose prompt is unchanged and didn't fail is never paid twice.
Rules for what goes in the prompts: research/packaging/PLAYBOOK.md. Check every result at full size and
at 160x90; fix small text locally (never ship a misspelled word).
"""
import json, os, subprocess, sys, time, urllib.request
from importlib.machinery import SourceFileLoader

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../.."))   # repo root
K = SourceFileLoader("cover", os.path.join(ROOT, "skills/avatar-shorts/scripts/cover.py")).load_module()


def token():
    if os.environ.get("KIE_API_KEY"): return os.environ["KIE_API_KEY"]   # an already-set env var wins
    env = os.path.join(ROOT, ".env")
    for l in (open(env) if os.path.exists(env) else []):
        if l.startswith("KIE_API_KEY="): return l.split("=", 1)[1].strip().strip('"')
    sys.exit("KIE_API_KEY missing: set it in .env")


def main(spec_path, names):
    spec = json.load(open(spec_path)); base = os.path.dirname(os.path.abspath(spec_path))
    ref, out_dir = os.path.join(base, spec.get("refs_dir", ".")), os.path.join(base, spec.get("out_dir", "."))
    names = names or list(spec["variants"]); cap = spec.get("cap", 100); t = token()
    rp = os.path.splitext(spec_path)[0] + "-receipt.json"
    rec = json.load(open(rp)) if os.path.exists(rp) else {"model": K.MODEL, "cap_credits": cap, "tasks": {}}
    before = K.call(f"{K.API}/chat/credit", t).get("data"); rec.setdefault("credits_before", before)
    todo = [n for n in names if not (rec["tasks"].get(n, {}).get("prompt") == spec["variants"][n]["prompt"]
                                     and rec["tasks"][n].get("state") != "fail")]
    if (rec["credits_before"] - before) + 10 * len(todo) > cap: sys.exit(f"cap {cap}: already {rec['credits_before'] - before}, {len(todo)} more")
    os.makedirs(os.path.join(out_dir, "thumbnail-raw"), exist_ok=True)
    for n in todo:                                    # submit all first, then poll
        v = spec["variants"][n]; urls = [K.upload(os.path.join(ref, f), t) for f in v["refs"]]
        r = K.call(f"{K.API}/jobs/createTask", t, {"model": K.MODEL, "input": {"prompt": v["prompt"], "input_urls": urls,
                                                                              "aspect_ratio": spec.get("aspect_ratio", "16:9"), "resolution": "2K"}})
        task = (r.get("data") or {}).get("taskId") or sys.exit(f"createTask {n}: {r}")
        rec["tasks"][n] = {"taskId": task, "prompt": v["prompt"], "refs": v["refs"]}; json.dump(rec, open(rp, "w"), indent=1)
    for n in names:
        task = rec["tasks"][n]["taskId"]
        for _ in range(90):
            d = K.call(f"{K.API}/jobs/recordInfo?taskId={task}", t).get("data") or {}
            if d.get("state") in ("success", "fail"): break
            time.sleep(10)
        rec["tasks"][n]["state"] = d.get("state")
        if d.get("state") != "success": rec["tasks"][n]["fail"] = d.get("failMsg"); print(n, "FAILED", d.get("failMsg")); continue
        raw = os.path.join(out_dir, "thumbnail-raw", n + ".png")
        url = json.loads(d["resultJson"])["resultUrls"][0]
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=300) as r: open(raw, "wb").write(r.read())
        out = os.path.join(out_dir, f"{spec['prefix']}-{n}.jpg")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-vf", "scale=1920:1080:flags=lanczos", "-q:v", "3", out], check=True)
        rec["tasks"][n]["file"] = out; print(n, "ok", out)
    rec["credits_after"] = K.call(f"{K.API}/chat/credit", t).get("data"); json.dump(rec, open(rp, "w"), indent=1)
    print("credits", rec["credits_before"], "->", rec["credits_after"])


if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2:])
