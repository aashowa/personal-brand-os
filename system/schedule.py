#!/usr/bin/env python3
"""Put an approved video into the next open slot, on every platform at once.

    python3 system/schedule.py add <video_dir>          # dry run: shows slot + posts
    python3 system/schedule.py add <video_dir> --go     # uploads + schedules
    python3 system/schedule.py add <video_dir> --from 2026-10-20 [--go]   # first free slot on or after that date
    python3 system/schedule.py add <video_dir> --at "2026-10-13 12:00" [--go]   # a time you picked, off the cadence
    python3 system/schedule.py linkedin <dir> [--topic books] [--at "2026-11-06 12:00"] [--go]   # <dir>/linkedin.txt + linkedin-NN.png -> next LinkedIn slot (or that time)
    python3 system/schedule.py facebook <dir> [--go]   # <dir>/facebook.txt + facebook-01.png (+ facebook-comment.txt) -> the Reel's day, schedule.facebook_time
    python3 system/schedule.py list                     # what's coming up
    python3 system/schedule.py check                    # did everything due go out? marks `published`, exit 1 on a failure
    python3 system/schedule.py remind                   # pin-comment reminders for upcoming videos that don't have one
    python3 system/schedule.py reslot                   # push ledger slots to YouTube publishAt and GHL
    python3 system/schedule.py dashboard                # runway dashboard data -> .tmp/dashboard/
    python3 system/schedule.py reels                    # published Reels' YouTube numbers for research/reels-log.md
    python3 system/schedule.py growth                   # IG followers + YouTube subs vs growth.goals -> research/growth/daily.csv, every post -> posts.csv
    python3 system/schedule.py trial <video_dir|today> [--go] # post.json "trial" (one hook, or a list for A/B) -> Instagram Trial Reels, non-followers first
    python3 system/schedule.py selftest

<video_dir>/post.json (written when you approve the video):
    {"kind": "reel" | "episode", "video": "reel-01.mp4", "title": "YouTube title",
     "caption": "Instagram/Facebook/TikTok caption, your voice, ends with the CTA",
     "description": "optional YouTube description (default: caption)", "tags": ["optional"],
     "thumbnail": "optional episode thumbnail", "cover": "reel cover: YouTube Shorts thumbnail + Instagram/Facebook cover",
     "comment": "optional first comment on Instagram/Facebook (e.g. the repo link)",
     "pin": "optional comment you pin on YouTube (default: comment); you get a reminder at the slot",
     "platforms": ["youtube"] (optional; a reel goes to YouTube + every platform in PLATFORMS unless this narrows it),
     "topic": "books" (required for a new slot: the same topic stays a week apart in the same feed, Shorts/Reels or LinkedIn), "ai": false}

config.json (repo root): "creator.timezone"; "schedule": {"reel" | "episode" | "linkedin": {"days": ["tue", ...], "time": "HH:MM"},
"facebook_time": "18:00", "reminder_list": "Content"}; "ghl.user_email" (default creator.email); "instagram.username"
(default creator.handle); "growth.goals". Secrets in .env (an env var already set wins): GHL_API_KEY, GHL_LOCATION_ID,
META_ACCESS_TOKEN, plus youtube_upload.py's YOUTUBE_OAUTH_*.

Default slots (config.example.json): reels 12:00 every day, the earliest open day first -> YouTube Shorts (API, private + publishAt) and
Instagram + Facebook page + TikTok (one GHL Social Planner post, status scheduled). Ledger statuses: youtube_only -> scheduled -> published (by `check`).
Episodes Tue 10:00 -> YouTube only. LinkedIn posts Tue/Wed/Thu 12:00 -> your profile (GHL). Facebook posts 18:00 on their
Reel's day -> your page (GHL). Both platforms hold the schedule, so nothing has to stay running.
Ledger: system/schedule-ledger.json. Episode folders live in episodes/<slug>/.
Optional tools: remctl (Apple Reminders CLI) for pin reminders; the GHL internal client for LinkedIn PDF carousels (see internal()).
"""
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import time as time_mod
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
LEDGER = Path(__file__).with_name("schedule-ledger.json")
CONFIG = ROOT / "config.json"
CFG = json.loads(CONFIG.read_text()) if CONFIG.exists() else {}
CREATOR, SCHED = CFG.get("creator") or {}, CFG.get("schedule") or {}
WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def cadence_of(kind):
    """config "schedule.<kind>" {"days": ["tue", "thu"], "time": "10:00"} -> ([1, 3], time(10, 0)), Mon=0"""
    return [WEEKDAYS.index(d[:3].lower()) for d in SCHED[kind]["days"]], time.fromisoformat(SCHED[kind]["time"])


TZ = ZoneInfo(CREATOR["timezone"]) if CREATOR.get("timezone") else None  # the __main__ check refuses to run without it
CADENCE = {k: cadence_of(k) for k in ("reel", "episode", "linkedin") if k in SCHED}  # Mon=0
CADENCE_FROM = {}  # {kind: (date, weekdays)}: a cadence change that takes over from its date, so past slots stay right on the dashboard
LEAD = timedelta(hours=3)  # never schedule closer than this; uploads need processing time
TOPIC_GAP = timedelta(days=7)  # same topic, same feed: at least a week apart
MAKE_DAYS = {"reel": 3, "episode": 7, "linkedin": 2}  # ponytail: guessed days to make one before its slot; tune per feed
FEED_NAME = {"reel": "Reels", "episode": "Episodes", "linkedin": "LinkedIn"}
DASH = ROOT / ".tmp/dashboard"
GROWTH = ROOT / "research/growth/daily.csv"
POSTS = ROOT / "research/growth/posts.csv"   # every post's numbers, one row per post per day (cmd_growth)
# (from, by, {platform: (start, target)}) from config.json "growth.goals":
# [{"from": "YYYY-MM-DD", "by": "YYYY-MM-DD", "targets": {"instagram": [start, target], "youtube": [start, target]}}]. Add each month's goal.
GOALS = [(date.fromisoformat(g["from"]), date.fromisoformat(g["by"]), {p: tuple(v) for p, v in g["targets"].items()})
         for g in (CFG.get("growth") or {}).get("goals", [])]
GHL = "https://services.leadconnectorhq.com"
GRAPH = "https://graph.facebook.com/v23.0"
PLATFORMS = ("instagram", "facebook", "tiktok")
GHL_USER_EMAIL = ((CFG.get("ghl") or {}).get("user_email") or CREATOR.get("email") or "").lower()  # GHL user who owns the posts
IG_USERNAME = (CFG.get("instagram") or {}).get("username") or (CREATOR.get("handle") or "").lstrip("@")
FB_AT = time.fromisoformat(SCHED.get("facebook_time", "18:00"))  # Facebook page post: same day as its Reel, in the evening so it doesn't sit on top of the Reel
REMINDER_LIST = SCHED.get("reminder_list", "Content")  # Apple Reminders list for pin reminders


def load_env():
    env = ROOT / ".env"
    for line in (env.read_text().splitlines() if env.exists() else []):
        m = re.match(r"\s*([A-Z0-9_]+)=(.*)", line)
        if m and m.group(1) not in os.environ:
            os.environ[m.group(1)] = m.group(2).strip().strip("'\"")


def ledger():
    return json.loads(LEDGER.read_text()) if LEDGER.exists() else []


def rel(p):
    """A folder as `episodes/...`. Ledger rows hold the absolute path of the machine that wrote them (a laptop, a server
    or a cloud session), so "already scheduled" compares this form, never absolute paths."""
    p = str(p)
    return p[p.rindex("episodes/"):] if "episodes/" in p else p


def days_on(kind, day):
    """The cadence weekdays in force on day: a CADENCE_FROM entry takes over from its date."""
    start, days = CADENCE_FROM.get(kind, (None, None))
    return days if start and day >= start else CADENCE[kind][0]


def next_slot(kind, taken, now):
    at = CADENCE[kind][1]
    d = now.astimezone(TZ).date()
    busy = {s[:10] for s in taken}  # a day is taken whatever the time (an exact-time match let a 10:30 post and a 12:00 post share a day)
    for i in range(0, 366):
        day = d + timedelta(days=i)
        if day.weekday() in days_on(kind, day):
            t = datetime.combine(day, at, TZ)
            if t > now + LEAD and day.isoformat() not in busy:
                return t
    raise SystemExit("no free slot in the next year")


def feed(kind):
    """Where a post competes for the same audience: Shorts/Reels share one feed, LinkedIn another. Episodes are exempt
    (a Short near its own episode is promotion, not a repeat)."""
    return {"reel": "shorts", "linkedin": "linkedin"}.get(kind)


def topic_clash(led, kind, topic, slot, skip=None):
    """The other live post with the same topic in the same feed within TOPIC_GAP of slot, or None."""
    if not topic or not feed(kind):
        return None
    return next((e for e in led if e is not skip and feed(e["kind"]) == feed(kind) and e.get("topic") == topic
                 and e["status"] in ("scheduled", "youtube_only", "published")
                 and abs(datetime.fromisoformat(e["slot"]) - slot) < TOPIC_GAP), None)


def spaced_slot(led, kind, topic, taken, now):
    """next_slot, skipping slots that would repeat the topic in the same feed within a week."""
    taken = set(taken)
    while True:
        slot = next_slot(kind, taken, now)
        if not topic_clash(led, kind, topic, slot):
            return slot
        taken.add(slot.isoformat())


def ghl(method, path, **kw):
    import requests
    h = {"Authorization": f"Bearer {os.environ['GHL_API_KEY']}", "Version": "2021-07-28",
         "Accept": "application/json", "User-Agent": "Mozilla/5.0"}  # browser UA: Cloudflare 1010 otherwise
    r = requests.request(method, GHL + path, headers=h, timeout=300, **kw)
    if r.status_code >= 300:
        raise SystemExit(f"GHL {method} {path} -> {r.status_code}: {r.text[:300]}")
    return r.json()


_TOKENS = None


def internal(method, path, **kw):
    """GHL's own app backend (Firebase login from the gohighlevel-cli plugin). It takes a PDF for a LinkedIn carousel;
    the public API rejects PDFs and keeps only the first image of a scheduled LinkedIn post. Optional: only carousels need it."""
    import requests
    global _TOKENS
    if _TOKENS is None:
        sys.path.insert(0, str(ROOT / "plugins/gohighlevel-cli/cli_anything/gohighlevel/utils"))
        try:
            from ghl_internal_client import TokenManager
        except ImportError:
            raise SystemExit("LinkedIn carousels need the GHL internal client (ghl_internal_client.py with TokenManager, from the "
                             "gohighlevel-cli plugin) in plugins/gohighlevel-cli/cli_anything/gohighlevel/utils/. Single-image posts work without it.")
        _TOKENS = TokenManager()  # one Firebase refresh per run; it caches the token ~50 min
    for attempt in range(3):  # the plugin's refresh call times out at 10 s and exits; it usually works on a retry
        try:
            token = _TOKENS.get_token()
            break
        except SystemExit:
            if attempt == 2:
                raise
            time_mod.sleep(3)
    h = {"token-id": token, "channel": "APP", "source": "WEB_USER", "version": "2021-07-28",
         "Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    r = requests.request(method, "https://backend.leadconnectorhq.com" + path, headers=h, timeout=300, **kw)
    if r.status_code >= 300:
        raise SystemExit(f"GHL internal {method} {path} -> {r.status_code}: {r.text[:300]}")
    return r.json()


def ghl_ids():
    loc = os.environ["GHL_LOCATION_ID"]
    accts = ghl("GET", f"/social-media-posting/{loc}/accounts")["results"]["accounts"]
    ids = {}
    for a in accts:  # look up by platform, never hardcode
        if a["platform"] in PLATFORMS + ("linkedin",) and not a.get("isExpired") and (a["platform"] != "facebook" or a.get("type") == "page"):
            ids.setdefault(a["platform"], a["id"])
    missing = [p for p in PLATFORMS if p not in ids]
    if missing:
        raise SystemExit(f"GHL has no connected {missing} account; reconnect in Social Planner")
    users = ghl("GET", f"/users/?locationId={loc}").get("users", [])
    uid = next((u["id"] for u in users if (u.get("email") or "").lower() == GHL_USER_EMAIL), None)
    if not uid:
        raise SystemExit(f"no GHL user '{GHL_USER_EMAIL}' on this location (set ghl.user_email or creator.email in config.json)")
    return loc, ids, uid


GHL_MAX = 24_000_000  # GHL media library rejects files over 25 MB (413/502)


def ghl_copy(video):
    """GHL-sized copy of a video (YouTube keeps the full master). Cached next to the master."""
    if video.stat().st_size <= GHL_MAX:
        return video
    out = video.with_name(video.stem + ".ghl.mp4")
    if out.exists() and out.stat().st_size <= GHL_MAX:
        return out
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                               capture_output=True, text=True).stdout)
    for target in (21_000_000, 17_000_000):
        kbps = int(target * 8 / dur / 1000) - 160
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-c:v", "libx264", "-preset", "medium",
                        "-b:v", f"{kbps}k", "-maxrate", f"{int(kbps * 1.5)}k", "-bufsize", f"{kbps * 2}k",
                        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out)], check=True)
        if out.stat().st_size <= GHL_MAX:
            return out
    raise SystemExit(f"could not get {video.name} under 25 MB for GHL")


def upload_media(path):
    """Upload to GHL Media Storage with the file's real type. Without it GHL stores and serves everything as text/plain:
    Instagram then ignores the Reel cover and GHL's composer can't open the video."""
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    with open(path, "rb") as f:
        r = ghl("POST", "/medias/upload-file", files={"file": (path.name, f, mime)}, data={"hosted": "false", "name": path.name})
    return r["url"]


def youtube(p, folder, slot, go):
    desc = folder / ".yt-description.txt"
    desc.write_text(p.get("description") or p["caption"])
    cmd = [sys.executable, str(Path(__file__).with_name("youtube_upload.py")), "upload", str(folder / p["video"]),
           "--title", p["title"], "--description-file", str(desc), "--privacy", "private",
           "--publish-at", slot.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")]
    if p.get("tags"):
        cmd += ["--tags", ",".join(p["tags"])]
    if p.get("ai"):
        cmd.append("--ai")
    thumb = p.get("thumbnail") or (p.get("cover") if p["kind"] == "reel" else None)  # Shorts take the vertical cover
    if thumb:
        cmd += ["--thumbnail", str(folder / thumb)]
    if go:
        cmd.append("--go")
    out = subprocess.run(cmd, capture_output=True, text=True)
    print(out.stdout.strip() or out.stderr.strip())
    if out.returncode:
        raise SystemExit("YouTube upload failed; nothing else was scheduled")
    m = re.search(r"youtu\.be/([\w-]+)", out.stdout)
    return m.group(1) if m else None


def social_platforms(p):
    """GHL platforms a post.json goes to: a reel's are all of PLATFORMS unless "platforms" narrows them; episodes are YouTube only."""
    return [x for x in PLATFORMS if x in p.get("platforms", PLATFORMS)] if p["kind"] == "reel" else []


def remctl():
    r = shutil.which("remctl") or os.path.expanduser("~/bin/remctl")
    return r if os.path.exists(r) else None


def pin_reminder(e, p):
    """YouTube's API can't pin a comment (and GHL can't comment on TikTok), so you get a reminder in your REMINDER_LIST
    list (Apple Reminders, through remctl) 5 minutes after the slot, with the text to post and pin."""
    text = p.get("pin") or p.get("comment")
    if not text or e.get("pin_reminder") or not e.get("youtube"):
        return
    where = "YouTube" + (" and TikTok" if "tiktok" in social_platforms(p) else "")
    due = datetime.fromisoformat(e["slot"]) + timedelta(minutes=5)
    if not remctl():  # optional tool: without it, say what to pin; `remind` sets the reminder once remctl is installed
        return print(f"  no remctl (Apple Reminders CLI): at {due:%a %b %d, %-I:%M %p} post and pin this on {where}:\n  {text}")
    subprocess.run([remctl(), "add", "-l", REMINDER_LIST, "-d", f"{due:%Y-%m-%d %H:%M}", "--url", f"https://youtu.be/{e['youtube']}",
                    "-n", f"Post this as a comment and pin it on {where}:\n\n{text}", f"Pin comment: {e['title'][:60]}"],
                   check=True, capture_output=True)
    e["pin_reminder"] = True
    print(f"  pin reminder set for {due:%a %b %d, %-I:%M %p}")


def socials(p, folder, slot):
    loc, ids, uid = ghl_ids()
    media = {"url": upload_media(ghl_copy(folder / p["video"])), "type": "video/mp4"}
    if p.get("cover"):
        media["thumbnail"] = upload_media(folder / p["cover"])
    body = {
        "accountIds": [ids[x] for x in PLATFORMS], "type": "reel", "status": "scheduled", "userId": uid,
        "scheduleDate": slot.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "summary": p["caption"], "media": [media],
        "instagramPostDetails": {"type": "reel", "showOnFeed": True},
        "facebookPostDetails": {"type": "reel"},
        "tiktokPostDetails": {"privacyLevel": "PUBLIC_TO_EVERYONE", "enableComment": True, "enableDuet": True,
                              "enableStitch": True, "promoteYourBrand": False, "promoteOtherBrand": False,
                              "videoDisclosure": False},
    }
    # GHL can't post a first comment on TikTok, so a Reel with a comment becomes two posts at the same time
    plats_all = social_platforms(p)
    commented = [x for x in plats_all if x != "tiktok"] if p.get("comment") else []
    groups = [(commented, p.get("comment")), ([x for x in plats_all if x not in commented], None)]
    out = []
    for plats, comment in groups:
        if not plats:
            continue
        b = {**body, "accountIds": [ids[x] for x in plats]}
        if comment:
            b["followUpComment"] = comment
        if "tiktok" not in plats:
            b.pop("tiktokPostDetails")
        r = ghl("POST", f"/social-media-posting/{loc}/posts", json=b)
        post = (r.get("results") or {}).get("post") or r.get("post") or {}
        out.append(post.get("_id") or post.get("id"))
    return out


def cmd_add(folder, go, start=None, at=None):
    folder = Path(folder).resolve()
    p = json.loads((folder / "post.json").read_text())
    assert p["kind"] in CADENCE, "kind must be reel or episode"
    for k in ("video", "title", "caption"):
        assert p.get(k), f"post.json needs {k}"
    assert (folder / p["video"]).is_file(), f"missing {p['video']}"
    led = ledger()
    mine = next((e for e in led if rel(e["folder"]) == rel(folder) and e["kind"] == p["kind"] and e["status"] in ("scheduled", "youtube_only", "published")), None)
    if mine and mine["status"] != "youtube_only":
        raise SystemExit(f"already {mine['status']}; see `schedule.py list`")
    taken = {e["slot"] for e in led if e["kind"] == p["kind"] and e["status"] in ("scheduled", "youtube_only")}
    topic = p.get("topic")
    if mine:  # YouTube done on an earlier run; keep its slot, only finish the socials
        slot = datetime.fromisoformat(mine["slot"])
    else:
        assert topic, 'post.json needs "topic" (e.g. "books", "chatbot") so repeats stay a week apart'
        if at:  # a time you picked, off the cadence
            slot = datetime.fromisoformat(at).replace(tzinfo=TZ)
            assert slot > datetime.now(TZ) + LEAD, f"--at must be at least {LEAD} from now"
            assert slot.isoformat() not in taken, f"{slot} is taken by another {p['kind']}"
        else:
            now = datetime.now(TZ)
            if start:  # you asked for a later slot
                now = max(now, datetime.combine(date.fromisoformat(start), time(0, 0), TZ))
            slot = spaced_slot(led, p["kind"], topic, taken, now)
        clash = topic_clash(led, p["kind"], topic, slot)
        if clash:  # only possible with --at: say so, you picked the time
            print(f"  NOTE: same topic '{topic}' as '{clash['title'][:50]}' on {datetime.fromisoformat(clash['slot']):%a %b %d}")
    plats = social_platforms(p)
    where = "YouTube" + (f" + {', '.join(plats)} (GHL)" if plats else "")
    print(f"{folder.name}: {p['kind']} -> {slot:%a %b %d %Y, %-I:%M %p %Z} on {where}" + (" (YouTube already uploaded)" if mine else ""))
    print(f"  title: {p['title']}\n  caption: {p['caption'][:140]}{'…' if len(p['caption']) > 140 else ''}")
    if p["kind"] == "reel":
        fixes, flags = copy_check(p["caption"])
        if fixes:
            raise SystemExit(f"AI tells in the caption: {', '.join(fixes)}. Rewrite them, or drop a word from linkedin/human/slop.json if it's really yours.")
        first = p["caption"].split("\n")[0]
        if len(first) > 125:  # Instagram shows ~125 characters before "... more"
            flags.append(f"first line is {len(first)} characters; Instagram cuts at ~125, so end it at a full stop or a cliff before that")
        for f in flags:
            print(f"  check by eye: {f}")
    if not go:
        if not mine:
            youtube(p, folder, slot, go=False)
        if plats:
            load_env(); _, ids, uid = ghl_ids()
            print(f"GHL ready: {', '.join(ids)} connected, posting as {GHL_USER_EMAIL}")
        print("Dry run. Add --go to upload and schedule.")
        return
    load_env()
    if not mine:
        mine = {"folder": str(folder), "kind": p["kind"], "slot": slot.isoformat(), "title": p["title"], "topic": topic,
                "youtube": youtube(p, folder, slot, go=True), "ghl_post": None, "status": "youtube_only",
                "youtube_slot_ok": True, "added": datetime.now(TZ).isoformat()}
        led.append(mine)
        LEDGER.write_text(json.dumps(led, indent=1))  # slot is taken the moment YouTube has it
    if plats:
        mine["ghl_post"] = socials(p, folder, slot)
    mine["status"] = "scheduled"
    pin_reminder(mine, p)
    LEDGER.write_text(json.dumps(led, indent=1))
    print(f"Scheduled. YouTube {mine['youtube']}" + (f", GHL posts {mine['ghl_post']}" if mine["ghl_post"] else ""))
    if p["kind"] == "episode":
        print(f"Tracker: set this episode's row to scheduled, publish date {slot:%Y-%m-%d %H:%M} ({notion_url(folder) or 'no notion.md'})")


def copy_check(text):
    """AI tells in a post (linkedin/human: humanize.py + slop.json, from Jake Schincariol's MIT linkedin-agent-skill).
    Returns (fixes, flags): fixes are em dashes, curly quotes, hidden characters and stock AI words, which block scheduling;
    flags are sentence shapes ("It's not just X, it's Y", triads, even sentence lengths) to judge by eye."""
    sys.path.insert(0, str(ROOT / "linkedin/human"))
    import humanize
    lex = humanize.load_lexicon()
    rep = humanize.humanize(text, lex)[1]
    fixes = [h.get("find") or h["name"] for k in ("invisible", "typographic", "lexical") for h in rep[k]]
    even = lambda fs: [f["name"] for f in fs if f["name"].startswith("Uniform")]
    joined = re.sub(r"(?<!\n)\n(?!\n)", " ", text)  # its sentence-length check reads every short line as a sentence; judge whole sentences
    return fixes, [f["name"] for f in rep["structures"] if not f["name"].startswith("Uniform")] + even(humanize.scan_structures(joined, lex))


def cmd_linkedin(folder, go, topic=None, at=None):
    """A LinkedIn post you approved: <dir>/linkedin.txt is the exact text; <dir>/linkedin-NN.png (from linkedin/creative/render.py)
    is one image, or several sent as one swipeable PDF carousel. Topic: --topic, else the folder's post.json."""
    folder = Path(folder).resolve()
    if not topic and (folder / "post.json").exists():
        topic = json.loads((folder / "post.json").read_text()).get("topic")
    assert topic, "give --topic (e.g. books, chatbot) so LinkedIn repeats stay a week apart"
    text = (folder / "linkedin.txt").read_text().strip()
    assert len(text) <= 3000, f"LinkedIn caps posts at 3,000 characters; this is {len(text)}"
    fixes, flags = copy_check(text)
    if fixes:
        raise SystemExit(f"AI tells in linkedin.txt: {', '.join(fixes)}. Rewrite them, or drop a word from linkedin/human/slop.json if it's really yours.")
    slides = sorted(folder.glob("linkedin-[0-9][0-9].png"))
    pdf = folder / "linkedin.pdf"
    if len(slides) > 1:  # a carousel goes to GHL as one PDF through its app backend (see internal())
        im = "magick" if shutil.which("magick") else "convert"  # ImageMagick 7 is `magick`; 6 (Linux apt) only has `convert`
        subprocess.run([im, *map(str, slides), "-units", "PixelsPerInch", "-density", "72", str(pdf)], check=True)
    led = ledger()
    if any(rel(e["folder"]) == rel(folder) and e["kind"] == "linkedin" and e["status"] in ("scheduled", "published") for e in led):
        raise SystemExit("LinkedIn post already scheduled; see `schedule.py list`")
    taken = {e["slot"] for e in led if e["kind"] == "linkedin" and e["status"] == "scheduled"}
    if at:  # a day you picked, off the cadence
        slot = datetime.fromisoformat(at).replace(tzinfo=TZ)
        assert slot > datetime.now(TZ) + LEAD, f"--at must be at least {LEAD} from now"
        near = next((e for e in led if e["kind"] == "linkedin" and e["status"] in ("scheduled", "published")
                     and abs(datetime.fromisoformat(e["slot"]) - slot) < timedelta(hours=20)), None)
        assert not near, f"another LinkedIn post is within 20 hours: {near and near['title'][:50]}"
        clash = topic_clash(led, "linkedin", topic, slot)
        assert not clash, f"topic {topic} is within a week of: {clash and clash['title'][:50]}"
    else:
        slot = spaced_slot(led, "linkedin", topic, taken, datetime.now(TZ))
    html = folder / "linkedin.html"
    style = (re.search(r'<meta name="style" content="([\w-]+)"', html.read_text()) or [None, None])[1] if html.exists() else None
    prev = max((e for e in led if e["kind"] == "linkedin" and e["status"] in ("scheduled", "published") and e["slot"] < slot.isoformat()),
               key=lambda e: e["slot"], default=None)
    if style and prev and prev.get("style") == style:  # the styles rotate (linkedin/PLAYBOOK.md): the same one twice in a row reads as repetitive
        raise SystemExit(f"same style ({style}) as the LinkedIn post before it ({prev['title'][:50]}); pick another style")
    print(f"{folder.name}: linkedin -> {slot:%a %b %d %Y, %-I:%M %p %Z}, {len(text)} chars, {len(slides)} slide(s){' (carousel)' if len(slides) > 1 else ''}, style {style or '?'}")
    if not style:
        print('  check by eye: linkedin.html has no <meta name="style">, so the rotation can\'t be checked')
    print(f"  shows before '...see more' (~140 on mobile): {text[:140]!r}")
    for f in flags:
        print(f"  check by eye: {f}")
    load_env()
    loc, ids, uid = ghl_ids()
    if "linkedin" not in ids:
        raise SystemExit("GHL has no connected LinkedIn profile; reconnect in Social Planner (the token lasts ~60 days)")
    if not go:
        print("Dry run. Add --go to schedule.")
        return
    body = {"accountIds": [ids["linkedin"]], "type": "post", "status": "scheduled", "userId": uid, "summary": text,
            "scheduleDate": slot.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "media": [{"url": upload_media(f), "type": "image/png"} for f in slides]}
    if len(slides) > 1:  # the way GHL's composer does it: PDF -> page images -> post (GHL keeps every page in the post's page folder)
        title = re.search(r"<title>(.*?)</title>", (folder / "linkedin.html").read_text()).group(1)
        job = internal("POST", f"/social-media-posting/media/{loc}/document-to-image", json={"fileUrl": upload_media(pdf), "mimeType": "application/pdf"})["results"]
        for _ in range(60):
            res = internal("GET", f"/social-media-posting/media/{loc}/document-to-image/{job['fileId']}")["results"]
            if res["status"] == "completed":
                break
            time_mod.sleep(2)
        else:
            raise SystemExit(f"GHL PDF conversion did not finish: {res}")
        pages = [{"url": x["url"], "type": x.get("type", "image/jpeg")} for x in sorted(res["pages"], key=lambda x: x["pageNumber"])]
        assert len(pages) == len(slides), f"GHL made {len(pages)} pages from {len(slides)} slides"
        internal("POST", f"/social-media-posting/{loc}/posts", json={"userIds": [ids["linkedin"]], "createdBy": uid, "type": "post", "status": "scheduled",
                 "summary": text, "media": pages, "scheduleDate": body["scheduleDate"], "mediaOptimization": True,
                 "linkedinPostDetails": {"postAsPdf": True, "pdfTitle": title[:100]}})  # its reply has no post id, so find the post
        found = ghl("POST", f"/social-media-posting/{loc}/posts/list", json={"type": "scheduled", "accounts": ids["linkedin"], "skip": "0", "limit": "50",
                    "fromDate": (slot - timedelta(minutes=1)).astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                    "toDate": (slot + timedelta(minutes=1)).astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%S.000Z"), "includeUsers": "false"})
        post = next((x for x in (found.get("results") or {}).get("posts") or [] if x.get("summary") == text), {})
    else:
        r = ghl("POST", f"/social-media-posting/{loc}/posts", json=body)
        post = (r.get("results") or {}).get("post") or r.get("post") or {}
    led.append({"folder": str(folder), "kind": "linkedin", "slot": slot.isoformat(), "title": text.splitlines()[0], "topic": topic, "style": style,
                "ghl_post": [post.get("_id") or post.get("id")], "status": "scheduled", "added": datetime.now(TZ).isoformat(),
                **({"via": "ghl-internal carousel (composer flow): check LinkedIn shows every page after it posts"} if len(slides) > 1 else {})})
    LEDGER.write_text(json.dumps(led, indent=1))
    print(f"Scheduled on LinkedIn. GHL post {led[-1]['ghl_post']}")


def cmd_facebook(folder, go):
    """A Facebook page post you approved, on the same day as the folder's Reel at FB_AT: <dir>/facebook.txt is the exact
    text, <dir>/facebook-01.png the image (render.py <dir> facebook), <dir>/facebook-comment.txt the optional first comment
    (the list + the comment-WORD CTA; GHL posts one first comment)."""
    folder = Path(folder).resolve()
    led = ledger()
    reel = next((e for e in led if rel(e["folder"]) == rel(folder) and e["kind"] == "reel" and e["status"] in ("scheduled", "published")), None)
    assert reel, "schedule the Reel first (`schedule.py add`): its Facebook post goes out the same day"
    if any(rel(e["folder"]) == rel(folder) and e["kind"] == "facebook" and e["status"] in ("scheduled", "published") for e in led):
        raise SystemExit("Facebook post already scheduled; see `schedule.py list`")
    text = (folder / "facebook.txt").read_text().strip()
    comment = (folder / "facebook-comment.txt").read_text().strip() if (folder / "facebook-comment.txt").exists() else ""
    img = folder / "facebook-01.png"
    assert img.exists(), "needs facebook-01.png (render.py <dir> facebook)"
    for name, t in (("facebook.txt", text), ("facebook-comment.txt", comment)):
        fixes, flags = copy_check(t) if t else ([], [])
        if fixes:
            raise SystemExit(f"AI tells in {name}: {', '.join(fixes)}. Rewrite them, or drop a word from linkedin/human/slop.json if it's really yours.")
        for f in flags:
            print(f"  check by eye ({name}): {f}")
    slot = datetime.combine(datetime.fromisoformat(reel["slot"]).astimezone(TZ).date(), FB_AT, TZ)
    assert slot > datetime.now(TZ) + LEAD, f"{slot:%a %b %d %-I:%M %p} is too soon"
    print(f"{folder.name}: facebook -> {slot:%a %b %d %Y, %-I:%M %p %Z} (the Reel's day), {len(text)} chars, {img.name}" + (", first comment" if comment else ""))
    print(f"  shows before '...see more': {text[:180]!r}")
    load_env()
    loc, ids, uid = ghl_ids()
    if not go:
        print("Dry run. Add --go to schedule.")
        return
    body = {"accountIds": [ids["facebook"]], "type": "post", "status": "scheduled", "userId": uid, "summary": text,
            "scheduleDate": utc(slot), "media": [{"url": upload_media(img), "type": "image/png"}]}
    if comment:
        body["followUpComment"] = comment
    r = ghl("POST", f"/social-media-posting/{loc}/posts", json=body)
    post = (r.get("results") or {}).get("post") or r.get("post") or {}
    led.append({"folder": str(folder), "kind": "facebook", "slot": slot.isoformat(), "title": text.splitlines()[0], "topic": reel.get("topic"),
                "ghl_post": [post.get("_id") or post.get("id")], "status": "scheduled", "added": datetime.now(TZ).isoformat()})
    LEDGER.write_text(json.dumps(led, indent=1))
    print(f"Scheduled on Facebook. GHL post {led[-1]['ghl_post']}")


def youtube_upload():
    import importlib.util
    spec = importlib.util.spec_from_file_location("yu", Path(__file__).with_name("youtube_upload.py"))
    yu = importlib.util.module_from_spec(spec); spec.loader.exec_module(yu)
    return yu


def yt_client():
    yu = youtube_upload()
    return yu.youtube(yu.saved_creds())


def cmd_reels():
    """Published Reels' YouTube numbers for research/reels-log.md: views against the Reels' own median, stayed (engaged views / views: the share who didn't swipe away, the
    hook's grade), average % watched, and shares and subscribers per 100 views. Analytics lag YouTube's own views by 2-3 days."""
    from googleapiclient.discovery import build
    yu = youtube_upload()
    creds = yu.saved_creds()
    yt, ya = yu.youtube(creds), build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
    led = {e["youtube"]: e for e in ledger() if e["kind"] == "reel" and e.get("youtube") and e["status"] == "published"}
    if not led:
        return print("no published Reels yet")
    views = {v["id"]: int(v["statistics"].get("viewCount", 0)) for v in yt.videos().list(part="statistics", id=",".join(led)).execute()["items"]}
    rows = ya.reports().query(ids="channel==MINE", startDate="2026-01-01", endDate=date.today().isoformat(), dimensions="video",
                              metrics="views,engagedViews,averageViewPercentage,shares,subscribersGained", filters="video==" + ",".join(led)).execute()
    stats = {r[0]: r[1:] for r in rows.get("rows") or []}
    med = sorted(views.values())[len(views) // 2] or 1
    print(f"{'posted':<10} {'reel':<28} {'views':>6} {'x med':>5} {'stayed':>6} {'avg %':>5} {'shares/100':>10} {'subs/100':>8}")
    for i, e in sorted(led.items(), key=lambda kv: kv[1]["slot"]):
        if i not in views:
            continue
        av, engaged, pct, shares, subs = stats.get(i, [0, 0, None, 0, 0])
        stayed = f"{engaged / av:.0%}" if av else "-"
        print(f"{e['slot'][:10]:<10} {Path(e['folder']).name[:28]:<28} {views[i]:>6} {views[i] / med:>5.1f} {stayed:>6} "
              f"{f'{pct:.0f}' if pct is not None else '-':>5} {shares * 100 / (av or 1):>10.1f} {subs * 100 / (av or 1):>8.1f}")


def pace(start, target, frm, by, today, now):
    """(the straight line's value for today, how many a day are needed from here to hit the target)"""
    total = (by - frm).days
    return round(start + (target - start) * min((today - frm).days, total) / total), (target - now) / max((by - today).days, 1)


def graph(method, path, **kw):
    import requests
    kw.setdefault("params", {})["access_token"] = os.environ["META_ACCESS_TOKEN"]
    r = requests.request(method, GRAPH + path, timeout=300, **kw).json()
    if "error" in r:
        raise SystemExit(f"Instagram {path}: {r['error'].get('message')}")
    return r


def ig_me():
    """Your Instagram user id (IG_USERNAME), through the Facebook page the system user token was given."""
    pages = graph("GET", "/me/accounts", params={"fields": "instagram_business_account{id,username}", "limit": 200}).get("data", [])
    ig = next((a["instagram_business_account"]["id"] for a in pages if (a.get("instagram_business_account") or {}).get("username") == IG_USERNAME), None)
    if not ig:
        raise SystemExit(f"META_ACCESS_TOKEN doesn't have @{IG_USERNAME}: assign it to the system user in Business Settings")
    return ig


def ig_insights(mid):
    """A Reel's views, reach, shares, saves, average and total watch (ms) and skip rate (the % who left in the first
    3 seconds). Instagram gives no follows or profile visits per Reel."""
    try:
        r = graph("GET", f"/{mid}/insights", params={"metric": "views,reach,shares,saved,ig_reels_avg_watch_time,"
                                                               "ig_reels_video_view_total_time,reels_skip_rate"})
    except SystemExit:  # not a Reel, or too new
        return {}
    return {x["name"]: x["values"][0]["value"] for x in r["data"]}


def ig_account(n=50):
    """Your Instagram followers, post count and last n posts (trials included), each with its insights."""
    ig = graph("GET", f"/{ig_me()}", params={"fields": f"followers_count,media_count,media.limit({n}){{id,timestamp,like_count,comments_count,caption}}"})
    for m in ig.get("media", {}).get("data", []):
        m.update(ig_insights(m["id"]))
    return ig


def ig_path(uid, days=28):
    """Instagram's last 28 days as the path to a follow: reach (and how much of it doesn't follow yet), profile visits,
    follows, unfollows and bio link taps. In follows_and_unfollows Meta labels follows FOLLOWER and unfollows NON_FOLLOWER."""
    until = int(time_mod.time())
    def total(metric, **kw):
        v = graph("GET", f"/{uid}/insights", params={"metric": metric, "period": "day", "metric_type": "total_value",
                                                      "since": until - days * 86400, "until": until, **kw})["data"][0]["total_value"]
        return v.get("value") or 0, {x["dimension_values"][0]: x["value"] for b in v.get("breakdowns", []) for x in b["results"]}
    reach, split = total("reach", breakdown="follow_type")
    fu = total("follows_and_unfollows", breakdown="follow_type")[1]
    return {"ig28_reach": reach, "ig28_nonfollower_reach": split.get("NON_FOLLOWER", 0), "ig28_profile_views": total("profile_views")[0],
            "ig28_follows": fu.get("FOLLOWER", 0), "ig28_unfollows": fu.get("NON_FOLLOWER", 0), "ig28_link_taps": total("profile_links_taps")[0]}


def drop_off(curve, seconds):
    """YouTube's retention curve [(share of the video, audience watch ratio)] -> (the second the most viewers leave, the %
    of the starting audience lost in that second, the % still there at the end). The last 2 seconds are left out:
    everyone leaves at the end."""
    import bisect
    if len(curve) < 2 or seconds < 4:
        return None, None, None
    xs, ys = [c[0] * seconds for c in curve], [c[1] for c in curve]
    def at(t):
        i = min(max(bisect.bisect_left(xs, t), 1), len(xs) - 1)
        return ys[i - 1] + (ys[i] - ys[i - 1]) * (t - xs[i - 1]) / (xs[i] - xs[i - 1])
    start = ys[0] or 1
    loss, sec = max((at(s) - at(s + 1), s) for s in range(int(seconds) - 2))
    return sec, round(100 * loss / start, 1), round(100 * ys[-1] / start)


def post_vars(e, trial=False):
    """The variables a Reel was made with, from its post.json "vars" ({"opening", "seconds", ...}; a trial's own
    "opening" sits on its post.json "trial" entry), so posts.csv can compare like with like (research/growth/test.md)."""
    try:
        p = json.loads((ROOT / rel(e["folder"]) / "post.json").read_text())
    except (OSError, ValueError):
        return {}
    v = dict(p.get("vars") or {})
    if trial:
        t = p.get("trial") or []
        t = t if isinstance(t, list) else [t]
        hit = [x for x in t if x.get("video") == e.get("video")] or t[:1]  # older trials were logged without their video
        v["opening"] = hit[0].get("opening", "") if hit else ""
    return v


def write_rows(path, rows):
    import csv
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[-1]))
        w.writeheader()
        w.writerows(rows)


def cmd_growth():
    """The goal's daily numbers and every post's, for the daily review's one-change-at-a-time loop (research/growth/test.md).
    daily.csv: one row a day (a rerun replaces today's): followers and subscribers against the current goal's straight
    line (GOALS), plus Instagram's 28-day path to a follow. posts.csv: one row per post per day, Instagram (trials included)
    and YouTube, with skip rate, watch time, shares, saves and YouTube's drop-off second, so any post can be read back day
    by day. YouTube Analytics lags 2-3 days; the subscriber count doesn't."""
    import csv
    from googleapiclient.discovery import build
    load_env()
    if not GOALS:
        sys.exit('config.json needs growth.goals: [{"from": "YYYY-MM-DD", "by": "YYYY-MM-DD", "targets": {"instagram": [now, goal], "youtube": [now, goal]}}]')
    today, ig, yu = datetime.now(TZ).date(), ig_account(), youtube_upload()
    creds = yu.saved_creds()
    yt, ya = yu.youtube(creds), build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
    ch = yt.channels().list(part="statistics", mine=True).execute()["items"][0]["statistics"]
    now = {"instagram": ig["followers_count"], "youtube": int(ch["subscriberCount"])}
    path = ig_path(ig["id"])
    rows = [r for r in csv.DictReader(GROWTH.open()) if r["date"] != today.isoformat()] if GROWTH.exists() else []
    rows.append({"date": today.isoformat(), "instagram": now["instagram"], "ig_posts": ig["media_count"],
                 "youtube": now["youtube"], "yt_views": ch["viewCount"], **path})
    rows.sort(key=lambda r: r["date"])
    write_rows(GROWTH, rows)
    frm, by, goal = next((g for g in GOALS if g[1] >= today), GOALS[-1])
    week = next((r for r in reversed(rows) if date.fromisoformat(r["date"]) <= today - timedelta(days=7)), None)
    print(f"{today}  goal {by:%b %-d}, {(by - today).days} days left")
    for p, (start, target) in goal.items():
        plan, need = pace(start, target, frm, by, today, now[p])
        last7 = f"{(now[p] - int(week[p])) / 7:+.1f}/day last 7d" if week else "last 7d: under a week of data"
        print(f"{p:9} {now[p]:>6,}  line {plan:>6,}  target {target:,}  need {need:.1f}/day  {last7}  {'ON' if now[p] >= plan else 'OFF'} pace")
    p = path
    print(f"\nInstagram, last 28 days: reached {p['ig28_reach']:,} ({p['ig28_nonfollower_reach'] / (p['ig28_reach'] or 1):.0%} don't follow) "
          f"-> {p['ig28_profile_views']} profile visits ({p['ig28_profile_views'] / (p['ig28_reach'] or 1):.1%}) -> {p['ig28_follows']} follows "
          f"({p['ig28_follows'] / (p['ig28_profile_views'] or 1):.1%} of visits), {p['ig28_unfollows']} unfollows, {p['ig28_link_taps']} bio link taps")

    led = ledger()
    mains = {e["slot"][:10]: e for e in led if e["kind"] == "reel" and e["status"] == "published"}  # ponytail: one main Reel a day; a second one that day would take the first's place
    trials = {e["instagram"]: e for e in led if e["kind"] == "trial" and e.get("instagram")}
    media = ig.get("media", {}).get("data", [])
    seen = {m["id"] for m in media}
    for mid, e in trials.items():  # a trial the media list doesn't return yet
        if mid not in seen:
            try:
                media.append({**graph("GET", f"/{mid}", params={"fields": "id,timestamp,like_count,comments_count,caption"}), **ig_insights(mid)})
            except SystemExit:
                pass
    out = []
    for m in media:
        posted = datetime.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S%z").astimezone(TZ).date()
        t = trials.get(m["id"])
        e = t or mains.get(posted.isoformat())
        v = post_vars(e, trial=bool(t)) if e else {}
        out.append({"date": today.isoformat(), "platform": "instagram", "kind": "trial" if t else "reel" if e else "post",
                    "reel": Path(e["folder"]).name if e else "", "post_id": m["id"], "posted": posted.isoformat(),
                    "title": (m.get("caption") or "").strip().split("\n")[0][:90], "opening": v.get("opening", ""),
                    "seconds": v.get("seconds", ""), "views": m.get("views", ""), "reach": m.get("reach", ""),
                    "skip_pct": m.get("reels_skip_rate", ""), "stayed_pct": "",
                    "avg_watch_s": round(m["ig_reels_avg_watch_time"] / 1000, 1) if m.get("ig_reels_avg_watch_time") else "",
                    "avg_pct": "", "likes": m.get("like_count", ""), "comments": m.get("comments_count", ""), "shares": m.get("shares", ""),
                    "saves": m.get("saved", ""), "subs": "", "drop_at_s": "", "drop_pct": "", "end_pct": ""})

    r = ya.reports().query(ids="channel==MINE", startDate="2026-01-01", endDate=today.isoformat(), dimensions="video", sort="-views", maxResults=200,
                           metrics="views,engagedViews,averageViewDuration,averageViewPercentage,likes,comments,shares,subscribersGained").execute()
    stats = {x[0]: x[1:] for x in r.get("rows") or []}
    ids, info = list(stats), {}
    for i in range(0, len(ids), 50):
        for x in yt.videos().list(part="snippet,contentDetails", id=",".join(ids[i:i + 50])).execute()["items"]:
            d = re.fullmatch(r"P(?:\d+D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", x["contentDetails"]["duration"])
            d = d.groups() if d else (None, None, None)
            info[x["id"]] = (x["snippet"]["title"], datetime.fromisoformat(x["snippet"]["publishedAt"].replace("Z", "+00:00")).astimezone(TZ).date(),
                             sum(int(n or 0) * k for n, k in zip(d, (3600, 60, 1))))
    by_yt = {e["youtube"]: e for e in led if e.get("youtube")}
    for vid, (views, engaged, avg_s, avg_pct, likes, comments, shares, subs) in stats.items():
        title, posted, secs = info.get(vid, ("", None, 0))
        drop = (None, None, None)
        if posted and posted >= today - timedelta(days=28):  # the curve for recent videos only: one call each
            curve = ya.reports().query(ids="channel==MINE", startDate="2026-01-01", endDate=today.isoformat(), dimensions="elapsedVideoTimeRatio",
                                       metrics="audienceWatchRatio", filters=f"video=={vid}").execute().get("rows") or []
            drop = drop_off(curve, secs)
        e = by_yt.get(vid)
        v = post_vars(e) if e else {}
        out.append({"date": today.isoformat(), "platform": "youtube", "kind": e["kind"] if e else "video", "reel": Path(e["folder"]).name if e else "",
                    "post_id": vid, "posted": posted.isoformat() if posted else "", "title": title[:90], "opening": v.get("opening", ""),
                    "seconds": v.get("seconds") or secs, "views": views, "reach": "", "skip_pct": "",
                    "stayed_pct": round(100 * engaged / views) if views else "", "avg_watch_s": avg_s, "avg_pct": round(avg_pct),
                    "likes": likes, "comments": comments, "shares": shares, "saves": "", "subs": subs,
                    "drop_at_s": "" if drop[0] is None else drop[0], "drop_pct": "" if drop[1] is None else drop[1], "end_pct": "" if drop[2] is None else drop[2]})
    old = [x for x in csv.DictReader(POSTS.open()) if x["date"] != today.isoformat()] if POSTS.exists() else []
    write_rows(POSTS, old + out)

    def recent(plat):
        return sorted((x for x in out if x["platform"] == plat and x["posted"] >= (today - timedelta(days=28)).isoformat()), key=lambda x: x["posted"])
    def med(xs, k):
        vals = sorted(float(x[k]) for x in xs if x[k] != "")
        return vals[len(vals) // 2] if vals else 0
    igr = [x for x in recent("instagram") if x["kind"] != "trial"]
    print(f"\nInstagram posts, last 28 days (posts.csv). Typical Reel: {med(igr, 'views'):.0f} views, {med(igr, 'skip_pct'):.0f}% skip, "
          f"{med(igr, 'avg_watch_s'):.1f}s watched. Trials = same video, new opening, non-followers only.")
    print("  posted     kind   views reach skip% watch-s shr sav like cmt  opening  title")
    for x in recent("instagram"):
        print(f"  {x['posted']} {x['kind']:<6} {x['views']:>5} {x['reach']:>5} {x['skip_pct']:>5} {x['avg_watch_s']:>7} {x['shares']:>3} {x['saves']:>3} "
              f"{x['likes']:>4} {x['comments']:>3}  {x['opening'] or '-':<8} {x['title'][:60]}")
    ytr = recent("youtube")
    print(f"\nYouTube, posted in the last 28 days (Analytics lags 2-3 days). Typical: {med(ytr, 'views'):.0f} views, {med(ytr, 'stayed_pct'):.0f}% stayed.")
    print("  posted     views stayed% avg% subs secs  most leave at  reach end  opening  title")
    for x in ytr:
        leave = f"{x['drop_at_s']}s (-{x['drop_pct']}%)" if x["drop_at_s"] != "" else "-"
        print(f"  {x['posted']} {x['views']:>5} {x['stayed_pct']:>6} {x['avg_pct']:>4} {x['subs']:>4} {x['seconds']:>4}  {leave:<13}  "
              f"{(str(x['end_pct']) + '%') if x['end_pct'] != '' else '-':>9}  {x['opening'] or '-':<8} {x['title'][:60]}")


def cmd_trial(folder, go):
    """Post hook versions of a Reel as Instagram Trial Reels: shown to non-followers first, not on the grid, so hooks get
    tested without spamming followers. Reads post.json "trial": one {"video", "hook" (a label, e.g. "A"), "caption"
    (default: the Reel's), "graduation": "MANUAL" (you share the winner in the app, default) or "SS_PERFORMANCE"
    (Instagram decides)}, or a list of them for an A/B test with Instagram off the GHL post. The Reel's cover
    and first comment go on each. Posts right away (the API can't schedule). Graduating isn't in the API."""
    import requests
    load_env()
    if folder == "today":  # the 12:05 job: today's main Reel, so its trial goes out in the same hours
        e = next((e for e in ledger() if e["kind"] == "reel" and e["slot"][:10] == datetime.now(TZ).date().isoformat()), None)
        folder = ROOT / rel(e["folder"]) if e else sys.exit("no Reel today")
    folder = Path(folder).resolve()
    p = json.loads((folder / "post.json").read_text())
    ts = p.get("trial") or sys.exit('post.json has no "trial": {"video": ..., "caption": ...}')
    ts = ts if isinstance(ts, list) else [ts]
    done = {e.get("video") for e in ledger() if e["kind"] == "trial" and rel(e["folder"]) == rel(folder)}
    if done & ({t["video"] for t in ts} | {None}):  # None: a trial logged before videos were
        sys.exit("this Reel already has a trial in the ledger")
    for t in ts:
        caption = t.get("caption") or p["caption"]
        print(f"Trial {t.get('hook', '')} of {folder.name}: {t['video']} ({(folder / t['video']).stat().st_size / 1e6:.1f} MB), "
              f"graduation {t.get('graduation', 'MANUAL')}\n{caption}\n")
        fixes = copy_check(caption)[0]
        if fixes:
            sys.exit("copy check: " + "; ".join(fixes))
    if not go:
        return print("dry run: add --go to post now")
    ig = ig_me()
    cover = upload_media(folder / p["cover"]) if p.get("cover") else None
    for t in ts:
        video, caption, grad = folder / t["video"], t.get("caption") or p["caption"], t.get("graduation", "MANUAL")
        c = graph("POST", f"/{ig}/media", data={"media_type": "REELS", "upload_type": "resumable", "caption": caption,
                                               "trial_params": json.dumps({"graduation_strategy": grad}),
                                               **({"cover_url": cover} if cover else {})})
        r = requests.post(c["uri"], headers={"Authorization": f"OAuth {os.environ['META_ACCESS_TOKEN']}", "offset": "0",
                                             "file_size": str(video.stat().st_size)}, data=video.read_bytes(), timeout=900)
        if r.status_code >= 300:
            sys.exit(f"upload -> {r.status_code}: {r.text[:300]}")
        for _ in range(60):  # Instagram processes the video before it can publish
            st = graph("GET", f"/{c['id']}", params={"fields": "status_code,status"})
            if st["status_code"] == "FINISHED":
                break
            if st["status_code"] == "ERROR":
                sys.exit(f"Instagram rejected the video: {st.get('status')}")
            time_mod.sleep(10)
        else:
            sys.exit(f"still processing after 10 minutes; container {c['id']}")
        mid = graph("POST", f"/{ig}/media_publish", data={"creation_id": c["id"]})["id"]
        led = ledger()
        led.append({"kind": "trial", "folder": str(folder), "trial_of": folder.name, "title": caption.splitlines()[0][:80],
                    "topic": p.get("topic"), "slot": datetime.now(TZ).isoformat(timespec="seconds"), "status": "published",
                    "instagram": mid, "graduation": grad, "video": t["video"], "hook": t.get("hook", "")})
        LEDGER.write_text(json.dumps(led, indent=1))
        print(f"posted trial {t.get('hook', '')} {mid}")
        if p.get("comment"):
            try:
                graph("POST", f"/{mid}/comments", data={"message": p["comment"]})
            except SystemExit as e:  # the trial is out and logged; a missing comment isn't worth failing over
                print(f"  first comment failed: {e}")
    print("the daily growth pull compares the trials")


def notion_url(folder):
    f = Path(folder) / "notion.md"
    m = f.exists() and re.search(r"https://\S+", f.read_text())  # the episode's tracker page (e.g. a Notion run sheet)
    return m.group(0).rstrip(").,") if m else None


def utc(t):
    return t.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def ghl_outcome(loc, pid, slot):
    """Problems with one GHL post, [] when it went out. When a post publishes, GHL retires it (deleted: true) and makes one
    post per platform carrying parentPostId, so the outcome lives on those children."""
    r = ghl("GET", f"/social-media-posting/{loc}/posts/{pid}")
    post = (r.get("results") or {}).get("post") or r
    if post.get("status") == "published":
        return []
    found = ghl("POST", f"/social-media-posting/{loc}/posts/list", json={"type": "all", "skip": "0", "limit": "100", "includeUsers": "false",
                "fromDate": utc(slot - timedelta(hours=1)), "toDate": utc(slot + timedelta(days=1))})
    kids = [x for x in (found.get("results") or {}).get("posts") or [] if x.get("parentPostId") == pid]
    if not kids:
        return [f"GHL post {pid} still {post.get('status')}, nothing went out"]
    return [f"{k.get('platform')} {k.get('status')} {k.get('error') or k.get('errorMessage') or ''}".strip()
            for k in kids if k.get("status") != "published"]


def cmd_check():
    """Did everything that was due go out? YouTube public, every GHL post published. Marks the ledger `published`,
    prints FAIL lines and exits 1 if anything didn't, so the daily task can alert you."""
    load_env()
    loc, yt, now, led, fails = os.environ["GHL_LOCATION_ID"], yt_client(), datetime.now(TZ), ledger(), []
    for e in led:
        slot = datetime.fromisoformat(e["slot"])
        if e["status"] != "scheduled" or slot + timedelta(minutes=15) > now:
            continue
        bad = []
        if e.get("youtube"):
            items = yt.videos().list(part="status", id=e["youtube"]).execute().get("items", [])
            st = items[0]["status"]["privacyStatus"] if items else "missing"
            if st != "public":
                bad.append(f"YouTube {e['youtube']} is {st}")
        if e.get("via", "").startswith("linkedin-native"):  # scheduled on LinkedIn itself; GHL only holds a draft copy
            e["checked"] = "not checkable here: scheduled on LinkedIn itself"
        else:
            for pid in e.get("ghl_post") or []:
                bad += ghl_outcome(loc, pid, slot)
        if bad:
            fails.append(f"FAIL {slot:%a %b %d %-I:%M %p} {e['kind']} {e['title'][:50]}: " + "; ".join(bad))
            continue
        e["status"], e["published_checked"] = "published", now.isoformat()
        print(f"ok   {slot:%a %b %d %-I:%M %p} {e['kind']:8} {e['title'][:60]}")
        if e["kind"] == "episode":
            print(f"Tracker: set this episode's row to published ({notion_url(e['folder']) or 'no notion.md'})")
    LEDGER.write_text(json.dumps(led, indent=1))
    for f in fails:
        print(f)
    if fails:
        sys.exit(1)
    print("check ok: everything due went out")


def cmd_remind():
    """Pin-comment reminders for upcoming videos that have pin text and no reminder yet (backfill; `add` sets them itself)."""
    led, now = ledger(), datetime.now(TZ)
    for e in led:
        f = Path(e["folder"]) / "post.json"
        if e["kind"] != "linkedin" and e["status"] == "scheduled" and datetime.fromisoformat(e["slot"]) > now and f.exists():
            pin_reminder(e, json.loads(f.read_text()))
    LEDGER.write_text(json.dumps(led, indent=1))
    print("remind done")


def ghl_move(loc, ids, uid, pid, slot):
    """Move one scheduled GHL post to slot. The PUT needs the whole post back, so text, media, cover and
    first comment are resent as GHL holds them. True when the read-back has the new time and nothing else changed."""
    get = lambda: (lambda r: (r.get("results") or {}).get("post") or r)(ghl("GET", f"/social-media-posting/{loc}/posts/{pid}"))
    p = get()
    assert p["status"] == "scheduled", f"GHL post {pid} is {p['status']}, not moving it"
    media = [{"url": m["url"], "type": m["type"], **({"thumbnail": p["thumbnail"]} if p.get("thumbnail") else {})} for m in p["media"]]
    body = {k: p[k] for k in ("accountIds", "type", "summary", "followUpComment") if p.get(k)}
    for k in ("instagramPostDetails", "facebookPostDetails", "tiktokPostDetails"):
        if p.get(k) and (k != "tiktokPostDetails" or ids["tiktok"] in p["accountIds"]):
            body[k] = {a: b for a, b in p[k].items() if a != "shortenedLinks"}
    ghl("PUT", f"/social-media-posting/{loc}/posts/{pid}", json={**body, "status": "scheduled", "userId": uid, "media": media,
                                                                 "scheduleDate": utc(slot), "scheduleTimeUpdated": True})
    q = get()
    return (q["scheduleDate"] == utc(slot) and q["status"] == "scheduled" and q["summary"] == p["summary"]
            and q.get("followUpComment") == p.get("followUpComment") and bool(q.get("thumbnail")) == bool(p.get("thumbnail"))
            and sorted(q["accountIds"]) == sorted(p["accountIds"]))


def cmd_reslot():
    """Push each ledger slot to YouTube's publishAt (needs the full youtube scope; re-run youtube_upload.py auth) for rows
    marked youtube_slot_ok: false, and to GHL for rows marked ghl_slot_ok: false."""
    led = ledger()
    if any(e.get("ghl_slot_ok") is False for e in led):
        load_env()
        loc, ids, uid = ghl_ids()
        for e in led:
            if e.get("ghl_slot_ok") is False:
                e["ghl_slot_ok"] = all(ghl_move(loc, ids, uid, pid, datetime.fromisoformat(e["slot"])) for pid in e["ghl_post"])
                print(f"{e['title'][:60]}: GHL {datetime.fromisoformat(e['slot']):%a %b %d %-I:%M %p} {'ok' if e['ghl_slot_ok'] else 'MISMATCH'}")
                LEDGER.write_text(json.dumps(led, indent=1))
    yt = yt_client()
    for e in led:
        if e.get("youtube") and e.get("youtube_slot_ok") is False:
            at = datetime.fromisoformat(e["slot"]).astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")
            p = json.loads((Path(e["folder"]) / "post.json").read_text())
            yt.videos().update(part="status", body={"id": e["youtube"], "status": {
                "privacyStatus": "private", "publishAt": at, "selfDeclaredMadeForKids": False,
                "containsSyntheticMedia": bool(p.get("ai"))}}).execute()
            for _ in range(10):  # YouTube's read-back lags the update by a few seconds
                got = yt.videos().list(part="status", id=e["youtube"]).execute()["items"][0]["status"].get("publishAt")
                if got == at:
                    break
                time_mod.sleep(3)
            e["youtube_slot_ok"] = got == at
            print(f"{e['title']}: YouTube publishAt {got} {'ok' if e['youtube_slot_ok'] else 'MISMATCH'}")
            LEDGER.write_text(json.dumps(led, indent=1))
    print("reslot done")


def cmd_list():
    now, led = datetime.now(TZ), ledger()
    rows = sorted((e for e in led if e["status"] in ("scheduled", "youtube_only") and datetime.fromisoformat(e["slot"]) >= now),
                  key=lambda e: e["slot"])
    for e in rows:
        slot = datetime.fromisoformat(e["slot"])
        clash = None if e.get("topic_ok") else topic_clash(led, e["kind"], e.get("topic"), slot, skip=e)  # topic_ok: you kept it
        flags = ("  [socials not scheduled]" if e["status"] == "youtube_only" else "") + \
                ("  [YouTube time not set; run reslot]" if e.get("youtube_slot_ok") is False else "") + \
                ("  [GHL time not set; run reslot]" if e.get("ghl_slot_ok") is False else "") + \
                (f"  [topic repeat: {datetime.fromisoformat(clash['slot']):%b %d}]" if clash else "")
        print(f"{slot:%a %b %d, %-I:%M %p}  {e['kind']:8}  {(e.get('topic') or '?'):16}  {e['title']}{flags}")
    print(f"{len(rows)} upcoming" if rows else "nothing scheduled")


def cadence_slots(kind, start, end):
    """Every cadence slot of kind on days start..end (end excluded)."""
    at = CADENCE[kind][1]
    return [datetime.combine(start + timedelta(i), at, TZ) for i in range((end - start).days)
            if (start + timedelta(i)).weekday() in days_on(kind, start + timedelta(i))]


def parse_picks(text, found):
    """Reel/Episode top picks from one radar digest (research/radar/YYYY-MM-DD.md, format in RUBRIC.md)."""
    top = text.split("## Top picks", 1)[-1].split("\n## ", 1)[0]
    picks = []
    for block in re.split(r"\n(?=\d+\. \*\*)", top):
        name, verdict = re.match(r"\d+\. \*\*(.+?)\*\*", block), re.search(r"· (Reel|Episode)\b[^·\n]*· (\d+)/25", block)
        if name and verdict:
            link, hook = re.search(r"\((https?://[^)\s]+)\)", block), re.search(r'hook:? "(.+?)"', block, re.I) or re.search(r"What it is:\**\s*(.+)", block)
            picks.append({"id": name.group(1), "pick": name.group(1), "verdict": verdict.group(1), "score": int(verdict.group(2)),
                          "hook": hook.group(1) if hook else "", "link": link.group(1) if link else "", "found": found})
    return picks


def cmd_dashboard():
    """Write the runway dashboard's data: slots.json (every cadence slot, this week + 3), runway.json (per feed: when the
    queue runs dry and the date to make the next one by), radar.json (last week's Reel/Episode radar picks)."""
    now, led, fmt = datetime.now(TZ), ledger(), lambda t: f"{t:%a %b %-d, %-I:%M %p}"
    start = now.date() - timedelta(days=now.weekday())  # this Monday
    end = start + timedelta(days=28)
    slots, runway = [], []
    for kind, (days, at) in CADENCE.items():
        mine = {e["slot"]: e for e in led if e["kind"] == kind and e["status"] in ("scheduled", "youtube_only", "published")}
        cad = cadence_slots(kind, start, end)
        extra = [datetime.fromisoformat(s) for s in mine if start <= datetime.fromisoformat(s).date() < end]
        for t in sorted({x.isoformat(): x for x in cad + extra}.values()):
            e = mine.get(t.isoformat())
            slots.append({"id": f"{kind}-{t.isoformat()}", "feed": FEED_NAME[kind], "kind": kind, "slot": t.isoformat(),
                          "day": t.date().isoformat(), "when": fmt(t), "cadence": t in cad,
                          "status": e["status"] if e else ("missed" if t < now else "open"),
                          "title": e["title"] if e else "", "topic": (e or {}).get("topic") or "",
                          "where": "" if not e else {"episode": "YouTube", "linkedin": "LinkedIn"}.get(kind)
                          or ("Shorts, IG, FB, TikTok" if e.get("ghl_post") else "YouTube Shorts")})
        gap = next_slot(kind, set(mine), now)
        upcoming = [s for s in mine if datetime.fromisoformat(s) >= now and mine[s]["status"] != "published"]
        upcoming.sort(key=datetime.fromisoformat)
        streak = 0
        for t in cadence_slots(kind, min((datetime.fromisoformat(s).date() for s in mine), default=gap.date()), gap.date()):
            streak = streak + 1 if t.isoformat() in mine else 0
        make_by = gap.date() - timedelta(days=MAKE_DAYS[kind])
        left = (make_by - now.date()).days
        covered = max((datetime.fromisoformat(s) for s in upcoming if datetime.fromisoformat(s) < gap), default=None)
        runway.append({"kind": kind, "feed": FEED_NAME[kind],
                       "cadence": ", ".join("Mon Tue Wed Thu Fri Sat Sun".split()[d] for d in days_on(kind, end)) + f" · {at:%-I:%M %p}",
                       "queued": len(upcoming), "next_when": fmt(datetime.fromisoformat(upcoming[0])) if upcoming else "",
                       "next_title": mine[upcoming[0]]["title"] if upcoming else "",
                       "covered_through": f"{covered:%a %b %-d}" if covered else "", "open_slot": fmt(gap),
                       "make_by": make_by.isoformat(), "make_by_day": f"{make_by:%a %b %-d}", "days_left": left,
                       "state": "behind" if left < 0 else "soon" if left <= 7 else "ok", "make_days": MAKE_DAYS[kind],
                       "open_4w": sum(t > now + LEAD and t.isoformat() not in mine for t in cadence_slots(kind, now.date(), now.date() + timedelta(days=28))),
                       "streak": streak})
    picks = {}
    for f in sorted((ROOT / "research/radar").glob("20*.md"))[-7:]:  # newest digest wins a repeat
        picks.update({p["id"]: p for p in parse_picks(f.read_text(), f.stem)})
    radar = sorted(picks.values(), key=lambda p: (p["score"], p["found"]), reverse=True)[:6]
    DASH.mkdir(parents=True, exist_ok=True)
    for name, rows in (("slots", slots), ("runway", runway), ("radar", radar)):
        (DASH / f"{name}.json").write_text(json.dumps(rows, indent=1))
    for r in runway:
        print(f"{r['feed']:9} next {r['next_when'] or '-':24} open {r['open_slot']:24} make by {r['make_by_day']} ({r['days_left']}d, {r['state']})")
    print(f"{len(slots)} slots, {len(radar)} radar picks -> {DASH}")


def selftest():
    global TZ, CADENCE, CADENCE_FROM  # fallback values, so the slot maths runs the same with or without config.json
    TZ = ZoneInfo("America/New_York")
    CADENCE = {"reel": ([0, 2, 4], time(12, 0)), "episode": ([1], time(10, 0)), "linkedin": ([1, 2, 3], time(12, 0))}
    CADENCE_FROM = {"reel": (date(2026, 10, 26), [0, 1, 2, 3, 4, 5, 6])}  # a cadence change: Reels every day from Oct 26
    mon = datetime(2026, 10, 12, 8, 0, tzinfo=TZ)  # a Monday morning
    assert next_slot("reel", set(), mon) == datetime(2026, 10, 12, 12, 0, tzinfo=TZ)
    taken = {datetime(2026, 10, 12, 12, 0, tzinfo=TZ).isoformat()}
    assert next_slot("reel", taken, mon) == datetime(2026, 10, 14, 12, 0, tzinfo=TZ)  # Wed
    assert next_slot("reel", set(), datetime(2026, 10, 12, 10, 0, tzinfo=TZ)) == datetime(2026, 10, 14, 12, 0, tzinfo=TZ)  # inside 3h lead
    assert next_slot("episode", set(), mon) == datetime(2026, 10, 13, 10, 0, tzinfo=TZ)  # Tue
    assert next_slot("reel", set(), datetime(2026, 10, 16, 13, 0, tzinfo=TZ)).weekday() == 0  # Fri pm -> Mon
    assert next_slot("linkedin", set(), mon) == datetime(2026, 10, 13, 12, 0, tzinfo=TZ)  # Tue
    assert next_slot("linkedin", set(), datetime(2026, 10, 15, 9, 0, tzinfo=TZ)) == datetime(2026, 10, 20, 12, 0, tzinfo=TZ)  # Thu inside lead -> next Tue
    assert next_slot("linkedin", {datetime(2026, 10, 20, 10, 30, tzinfo=TZ).isoformat()}, datetime(2026, 10, 15, 9, 0, tzinfo=TZ)) == datetime(2026, 10, 21, 12, 0, tzinfo=TZ)  # 10:30 post same day -> next day
    assert social_platforms({"kind": "reel"}) == list(PLATFORMS)
    assert social_platforms({"kind": "reel", "platforms": ["youtube"]}) == []  # YouTube-only Short: no GHL post
    assert social_platforms({"kind": "reel", "platforms": ["youtube", "tiktok"]}) == ["tiktok"]
    assert social_platforms({"kind": "episode"}) == []
    row = lambda kind, slot, topic: {"kind": kind, "slot": slot.isoformat(), "topic": topic, "status": "scheduled"}
    led = [row("reel", datetime(2026, 10, 12, 12, 0, tzinfo=TZ), "books"), row("episode", datetime(2026, 10, 13, 10, 0, tzinfo=TZ), "books")]
    assert topic_clash(led, "reel", "books", datetime(2026, 10, 14, 12, 0, tzinfo=TZ)) is led[0]
    assert topic_clash(led, "reel", "books", datetime(2026, 10, 19, 12, 0, tzinfo=TZ)) is None      # 7 days later is fine
    assert topic_clash(led, "linkedin", "books", datetime(2026, 10, 13, 12, 0, tzinfo=TZ)) is None  # other feed
    assert topic_clash(led, "episode", "books", datetime(2026, 10, 12, 10, 0, tzinfo=TZ)) is None    # episodes exempt
    assert spaced_slot(led, "reel", "books", set(), mon) == datetime(2026, 10, 19, 12, 0, tzinfo=TZ)  # skips Mon/Wed/Fri inside the week
    assert spaced_slot(led, "reel", "replit", {led[0]["slot"]}, mon) == datetime(2026, 10, 14, 12, 0, tzinfo=TZ)  # only the taken slot is skipped
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "notion.md").write_text("Tracker: https://example.com/p/abc123def).\n")
        assert notion_url(d) == "https://example.com/p/abc123def" and notion_url(Path(d) / "x") is None
    assert len(cadence_slots("reel", mon.date(), mon.date() + timedelta(days=7))) == 3  # Mon/Wed/Fri
    assert next_slot("reel", set(), datetime(2026, 11, 2, 13, 0, tzinfo=TZ)) == datetime(2026, 11, 3, 12, 0, tzinfo=TZ)  # Mon pm -> Tue
    assert next_slot("reel", {datetime(2026, 11, 3, 12, 0, tzinfo=TZ).isoformat()}, datetime(2026, 11, 2, 8, 0, tzinfo=TZ)) == datetime(2026, 11, 2, 12, 0, tzinfo=TZ)  # the earliest gap first
    assert next_slot("reel", set(), datetime(2026, 10, 30, 13, 0, tzinfo=TZ)) == datetime(2026, 10, 31, 12, 0, tzinfo=TZ)  # Fri pm -> Sat
    assert len(cadence_slots("reel", date(2026, 10, 26), date(2026, 11, 2))) == 7  # every day
    pick = parse_picks('## Top picks\n1. **bigarrow** ([repo](https://x.io/a)) · Reel (weak fit) · 21/25 (use 3)\n   Reel: hook "I asked." · on\n'
                       '2. **Skip** · Watch · 12/25\n## Watch\n- x', "2026-10-14")
    assert pick == [{"id": "bigarrow", "pick": "bigarrow", "verdict": "Reel", "score": 21, "hook": "I asked.", "link": "https://x.io/a", "found": "2026-10-14"}]
    assert copy_check("I run a restaurant.\nIt's busy on Fridays.") == ([], [])
    fixes = copy_check("We leverage AI — it’s seamless.")[0]
    assert "leverage" in fixes and "seamless" in fixes and any("—" in f for f in fixes) and any("’" in f for f in fixes)
    frm, by = date(2026, 10, 23), date(2026, 11, 30)
    assert pace(210, 2000, frm, by, frm, 210)[0] == 210 and round(pace(210, 2000, frm, by, frm, 210)[1]) == 47  # 1,790 in 38 days
    assert pace(210, 2000, frm, by, date(2026, 10, 30), 300)[0] == 540  # the line a week in
    assert pace(3, 100, frm, by, by, 100) == (100, 0)  # last day, hit
    assert rel("/home/me/personal-brand-os/episodes/reel-01") == rel("/workspace/repo/episodes/reel-01") \
        == rel("/Volumes/Disk/kit/episodes/reel-01") == "episodes/reel-01"  # one folder on a laptop, in the cloud, on a server
    half = [(i / 100, 1.0 if i * 0.2 < 5 else 0.5) for i in range(1, 101)]  # a 20 s Reel that loses half its viewers at 5 s
    assert drop_off(half, 20) == (4, 50.0, 50) and drop_off([], 20) == (None, None, None)
    print("selftest ok")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] not in ("add", "linkedin", "facebook", "list", "check", "remind", "reslot", "dashboard", "reels", "growth", "trial", "selftest"):
        sys.exit(__doc__)
    if a[0] != "selftest" and not (TZ and len(CADENCE) == 3):
        sys.exit('config.json needs creator.timezone and schedule.reel / schedule.episode / schedule.linkedin '
                 '({"days": ["mon", ...], "time": "HH:MM"}): copy config.example.json to config.json and fill it in')
    if a[0] == "add":
        cmd_add(a[1], "--go" in a, a[a.index("--from") + 1] if "--from" in a else None, a[a.index("--at") + 1] if "--at" in a else None)
    elif a[0] == "linkedin":
        cmd_linkedin(a[1], "--go" in a, a[a.index("--topic") + 1] if "--topic" in a else None, a[a.index("--at") + 1] if "--at" in a else None)
    elif a[0] == "facebook":
        cmd_facebook(a[1], "--go" in a)
    elif a[0] == "list":
        cmd_list()
    elif a[0] == "check":
        cmd_check()
    elif a[0] == "remind":
        cmd_remind()
    elif a[0] == "reslot":
        cmd_reslot()
    elif a[0] == "dashboard":
        cmd_dashboard()
    elif a[0] == "reels":
        cmd_reels()
    elif a[0] == "growth":
        cmd_growth()
    elif a[0] == "trial":
        cmd_trial(a[1], "--go" in a)
    else:
        selftest()
