#!/usr/bin/env python3
"""Instagram Reel cover: Nick Saraev's layout with a yellow tag + marker title, generated on Kie.ai with OpenAI's GPT Image 2.5 Sunburst.

usage: cover.py REEL_DIR     reads reel.json "cover" {"top", "left", "right", "bg", "tag", "line1", "line2"} (logo PNGs and
                             "bg", a frame of the product screen from this Reel's footage, for the background;
                             relative to REEL_DIR), uploads them with assets/cover/template.png (your approved layout) and
                             the identity still of the reel's avatar (config.json heygen.avatars.<slot>.still, else
                             assets/cover/<slot>.jpg: same outfit as the video), generates one 9:16 2K image (about 10 Kie
                             credits), writes REEL_DIR/<slug>-cover.jpg (1080x1920) + cover/receipt.json, and pushes the
                             cover to Drive like `reel.py drive`.
"""
import base64, hashlib, json, os, random, subprocess, sys, time, urllib.request

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__))); import reel as R

MODEL = "gpt-image-2-5-sunburst-image-to-image"      # OpenAI's newest image model on Kie at the time of writing
# Background: your own, built from a frame of the Reel's own product screen (cover "bg", image 6), out of focus behind
# you in ink black with a marker-yellow glow. Never the template's background (that one is borrowed).
API = "https://api.kie.ai/api/v1"
UPLOAD = "https://kieai.redpandaai.co/api/file-base64-upload"
REFS = os.path.join(R.SKILL, "assets", "cover")
PROMPT = """Create a 9:16 Instagram Reel cover.
Image 1 is the approved template for this series. Copy its composition and proportions, the person's size and position, the two tilted white icon tiles, the dark bottom third, and the title treatment exactly (a small marker-yellow #FFD43B tag with a thin black border in a bold monospace font; line 1 in white; line 2 in near-black #141412 on a flat marker-yellow #FFD43B band behind the lower half of the letters; sentence case, very heavy grotesque). Do NOT copy the background of image 1.
New background, our own: image 6 is a frame from this video (the product's real screen). Fill the whole background behind the person with that screen, large and softly out of focus (shallow depth of field), as if it is a big monitor behind them in a dark studio, so the viewer recognises the product but cannot read the small text. Grade it into our brand: deep near-black #141412 ink tones, a soft warm marker-yellow #FFD43B glow rising behind their shoulders, subtle warm amber edge light on them, fine film grain. It fades to pure black at the bottom behind the title. No glowing tile grids, no circuit patterns, no sci-fi tunnel, no particles, no lens flares.
Image 2 is the real person. Keep their face, facial hair, hair, skin tone, expression and clothes exactly as in image 2; this is a real person, do not change their identity.
Top centre: the wordmark from image 3 exactly as supplied, at the size and position of the wordmark in image 1.
Left tile: the logo from image 4. Right tile: the logo from image 5. Reproduce every logo exactly as supplied: same shapes and colours, never redrawn, no added text.
Tag: exactly "{tag}". Line 1: exactly "{line1}". Line 2: exactly "{line2}".
No other words, no red, no watermarks, no extra logos."""


# Random and subtle, never too much: a new cover picks one at random and stores it in reel.json "cover.pose", so a
# re-run keeps it. "still" is the original serious look.
POSES = {
    "still": "",
    "point": "Pose (the only change from the series): a reaction instead of a serious look. They grin with a natural, excited "
             "smile, and raise both hands near their shoulders with index fingers pointing outward at the two logo tiles, their left "
             "hand at the left tile and their right hand at the right tile. Natural hands with five fingers each; the hands do not "
             "cover the logos, their face or the title.",
    "smile": "Pose (the only change from the series): a relaxed, slight smile, as if they are about to share something useful. "
             "Shoulders and hands as in image 2. Subtle, not exaggerated.",
    "present": "Pose (the only change from the series): a slight confident smile, one hand raised near their chest with an open "
               "palm toward the right tile, as if presenting it. Natural hand with five fingers; it does not cover the logos, their "
               "face or the title. Subtle, not exaggerated.",
}
KEEP = "Keep their face, facial hair, hair, skin tone, expression and clothes exactly as in image 2"


def prompt_for(cv):
    p = PROMPT.format(tag=cv["tag"], line1=cv["line1"], line2=cv["line2"])
    pose = POSES[cv.get("pose", "still")]
    return p if not pose else p.replace(KEEP, "Keep their face, facial hair, hair, skin tone and clothes exactly as in image 2") + "\n" + pose


def call(url, token, payload=None):
    req = urllib.request.Request(url, data=json.dumps(payload).encode() if payload is not None else None,
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                                          "User-Agent": "Mozilla/5.0"})          # the upload host 403s Python's agent
    return json.load(urllib.request.urlopen(req, timeout=180))


def upload(path, token):
    """Named by content hash: same-name uploads overwrite each other on Kie storage, so covers built in parallel
    swapped logos (two Reels got a third Reel's logo)."""
    mime = "image/png" if path.lower().endswith(".png") else "image/jpeg"
    data = open(path, "rb").read()
    r = call(UPLOAD, token, {"base64Data": f"data:{mime};base64,{base64.b64encode(data).decode()}", "uploadPath": "images/reel-covers",
                             "fileName": hashlib.md5(data).hexdigest()[:16] + os.path.splitext(path)[1]})
    url = (r.get("data") or {}).get("downloadUrl")
    if not url: sys.exit(f"upload {path} failed: {r}")
    return url


def face(c):
    """Identity still of the reel's avatar, so the cover wears the video's outfit: config.json heygen.avatars.<slot>.still
    (relative to the repo root), else assets/cover/<slot>.jpg. An unknown avatar id falls back to the first slot."""
    name = (R.LEGACY | {v[0]: k for k, v in R.AVATARS.items()}).get(c["heygen"]["avatar_id"], next(iter(R.AVATARS), "avatar"))
    still = R.HG.get("avatars", {}).get(name, {}).get("still")
    return os.path.join(R.ROOT, still) if still else os.path.join(REFS, f"{name}.jpg")


def cover(reel):
    c = R.load(reel); cv = c["cover"]; out_dir = os.path.join(c["dir"], "cover"); os.makedirs(out_dir, exist_ok=True)
    token = R.env("KIE_API_KEY"); rec_path = os.path.join(out_dir, "receipt.json")
    rec = json.load(open(rec_path)) if os.path.exists(rec_path) else {}
    refs = [os.path.join(REFS, "template.png"), face(c)] + [os.path.join(c["dir"], cv[k]) for k in ("top", "left", "right", "bg")]
    miss = [p for p in refs if not os.path.exists(p)]
    if miss: sys.exit(f"cover: missing {miss} (template and identity stills: assets/cover/README.md)")
    if "pose" not in cv:                              # new cover: pick a subtle pose at random and keep it
        cv["pose"] = random.choice(list(POSES)); raw = json.load(open(os.path.join(c["dir"], "reel.json")))
        raw["cover"]["pose"] = cv["pose"]; json.dump(raw, open(os.path.join(c["dir"], "reel.json"), "w"), indent=1)
    prompt = prompt_for(cv)
    before = call(f"{API}/chat/credit", token).get("data")
    if rec.get("taskId") and rec.get("prompt") == prompt and rec.get("state") != "fail":
        task = rec["taskId"]                         # an earlier submit may still be running: never pay twice
    else:
        urls = [upload(p, token) for p in refs]
        r = call(f"{API}/jobs/createTask", token, {"model": MODEL, "input": {"prompt": prompt, "input_urls": urls,
                                                                             "aspect_ratio": "9:16", "resolution": "2K"}})
        task = (r.get("data") or {}).get("taskId")
        if not task: sys.exit(f"createTask failed: {r}")
        rec = {"model": MODEL, "prompt": prompt, "refs": refs, "taskId": task, "credits_before": before}
        json.dump(rec, open(rec_path, "w"), indent=1)
    for _ in range(80):
        d = call(f"{API}/jobs/recordInfo?taskId={task}", token).get("data") or {}
        if d.get("state") in ("success", "fail"): break
        time.sleep(10)
    rec["state"] = d.get("state")
    if rec["state"] != "success":
        json.dump(rec | {"fail": d.get("failMsg")}, open(rec_path, "w"), indent=1); sys.exit(f"cover {task}: {d.get('state')} {d.get('failMsg')}")
    url = json.loads(d["resultJson"])["resultUrls"][0]; raw = os.path.join(out_dir, "cover-raw.png")
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=300) as r: open(raw, "wb").write(r.read())
    out = os.path.join(c["dir"], c["slug"] + "-cover.jpg")
    R.run("ffmpeg", "-v", "error", "-y", "-i", raw, "-vf", "scale=1080:1920:flags=lanczos", "-q:v", "2", out)
    rec |= {"file": out, "credits_after": call(f"{API}/chat/credit", token).get("data")}
    json.dump(rec, open(rec_path, "w"), indent=1)
    print(f"cover ok {out} | task {task} | credits {rec.get('credits_before')} -> {rec['credits_after']}")
    R.drive(reel, c["slug"] + "-cover", ".jpg")


if __name__ == "__main__":
    if len(sys.argv) != 2: sys.exit(__doc__)
    cover(sys.argv[1])
