#!/usr/bin/env python3
"""Keep up with how the channels you learn from package their videos (titles, thumbnails, descriptions).

usage: pull.py [SLUG ...]      refresh every channel in creators.json (or only the slugs given)
       pull.py --selftest
Per channel (folder SLUG/): every long-form upload into videos.json (first_seen keeps the date we first saw it, views
update); thumbnails for new uploads and the top 24 of the last 12 months; the description of each new outlier; contact
sheets sheets/<date>-top.jpg (top 12, last 12 months) and sheets/<date>-new.jpg (uploads since the last pull, with views).
Outlier = a regular video (< 60 min) from the last 12 months with at least 2x the channel's median views.
Prints the new uploads and new outliers: read them against PLAYBOOK.md and add what's new there.
Needs yt-dlp + ffmpeg. No login; views are YouTube's rounded counts.
"""
import datetime, json, os, statistics, subprocess, sys, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))


def api_key():
    key, d = os.environ.get("YOUTUBE_API_KEY"), HERE
    while not key and d != os.path.dirname(d):
        env = os.path.join(d, ".env")
        if os.path.exists(env):
            key = next((l.split("=", 1)[1].strip().strip("\"'") for l in open(env) if l.startswith("YOUTUBE_API_KEY=")), None)
        d = os.path.dirname(d)
    return key


def description(vid):
    """yt-dlp first, then the YouTube Data API: the bot check blocks single-video pages from cloud IPs."""
    txt = subprocess.run(["yt-dlp", "--no-update", "--skip-download", "--sleep-requests", "2", "--print", "description",
                          f"https://www.youtube.com/watch?v={vid}"], capture_output=True, text=True).stdout
    key = api_key()
    if txt.strip() or not key: return txt
    req = urllib.request.Request("https://www.googleapis.com/youtube/v3/videos?" + urllib.parse.urlencode({"part": "snippet", "id": vid}),
                                 headers={"X-Goog-Api-Key": key})
    try:
        items = json.load(urllib.request.urlopen(req, timeout=30)).get("items", [])
    except OSError:
        return ""
    return items[0]["snippet"]["description"] if items else ""


def flat(url):
    out = subprocess.run(["yt-dlp", "--no-update", "--flat-playlist", "--extractor-args", "youtubetab:approximate_date",
                          "--print", "%(id)s\t%(view_count)s\t%(duration)s\t%(upload_date)s\t%(title)s", url.rstrip("/") + "/videos"],
                         capture_output=True, text=True).stdout
    rows = []
    for l in out.splitlines():
        p = l.split("\t")
        if len(p) == 5 and p[1].isdigit():
            rows.append({"id": p[0], "views": int(p[1]), "dur": int(float(p[2])) if p[2] not in ("NA", "None") else 0,
                         "date": p[3], "title": p[4]})
    return rows


def merge(old, new, today):
    """New list wins for views/title; first_seen is kept from the first pull."""
    seen = {r["id"]: r for r in old}
    return [dict(r, first_seen=seen.get(r["id"], {}).get("first_seen", today)) for r in new]


def outliers(rows, today, factor=2.0):
    cut = (datetime.date.fromisoformat(today) - datetime.timedelta(days=365)).strftime("%Y%m%d")
    reg = [r for r in rows if r["date"] >= cut and 0 < r["dur"] < 3600]
    if not reg: return [], 0
    med = statistics.median(r["views"] for r in reg)
    return sorted([r for r in reg if r["views"] >= factor * med], key=lambda r: -r["views"]), med


def thumb(d, vid):
    out = os.path.join(d, "thumbs", vid + ".jpg")
    if os.path.exists(out): return out
    for q in ("maxresdefault", "hqdefault"):
        if subprocess.run(["curl", "-s", "-f", "-A", "Mozilla/5.0", "-o", out, f"https://i.ytimg.com/vi/{vid}/{q}.jpg"]).returncode == 0 \
                and os.path.getsize(out) > 5000: return out
    return None


def sheet(d, rows, out, cols=4):
    rows = [r for r in rows if os.path.exists(os.path.join(d, "thumbs", r["id"] + ".jpg"))][:16]
    if not rows: return
    args, filt = [], []
    for i, r in enumerate(rows):
        args += ["-i", os.path.join(d, "thumbs", r["id"] + ".jpg")]
        filt.append(f"[{i}]scale=640:360,drawtext=text='{r['views'] // 1000}k':x=6:y=6:fontsize=30:fontcolor=yellow:box=1:boxcolor=black[s{i}]")
    lay = "|".join(f"{(i % cols) * 640}_{(i // cols) * 360}" for i in range(len(rows)))
    filt.append("".join(f"[s{i}]" for i in range(len(rows))) + f"xstack=inputs={len(rows)}:layout={lay}:fill=black[o]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", ";".join(filt), "-map", "[o]", "-q:v", "3", out], check=True)


def pull(slug, url, today):
    d = os.path.join(HERE, slug); [os.makedirs(os.path.join(d, x), exist_ok=True) for x in ("thumbs", "sheets", "descriptions")]
    vp = os.path.join(d, "videos.json"); old = json.load(open(vp)) if os.path.exists(vp) else []
    new = flat(url)
    if not new: print(f"{slug}: nothing listed (yt-dlp blocked or channel moved); kept the old list"); return
    rows = merge(old, new, today); json.dump(rows, open(vp, "w"), indent=0)
    fresh = [r for r in rows if r["id"] not in {o["id"] for o in old}] if old else []
    outs, med = outliers(rows, today)
    top = outs[:24] or sorted(rows, key=lambda r: -r["views"])[:24]
    with ThreadPoolExecutor(8) as ex: list(ex.map(lambda r: thumb(d, r["id"]), top + fresh))
    new_out = [r for r in outs if not os.path.exists(os.path.join(d, "descriptions", r["id"] + ".txt"))][:5]
    for r in new_out:                               # one at a time: YouTube rate-limits description pulls (HTTP 429)
        txt = description(r["id"])
        if txt.strip(): open(os.path.join(d, "descriptions", r["id"] + ".txt"), "w").write(r["title"] + "\n----\n" + txt)
        else: print(f"  no description for {r['id']}: yt-dlp and the YouTube API both came back empty", file=sys.stderr)
    sheet(d, sorted(outs or rows, key=lambda r: -r["views"])[:12], os.path.join(d, "sheets", f"{today}-top.jpg"))
    if fresh: sheet(d, fresh, os.path.join(d, "sheets", f"{today}-new.jpg"))
    print(f"\n{slug}: {len(rows)} uploads, median (12 mo, < 60 min) {med:,.0f}, {len(outs)} outliers (>= 2x)")
    for r in fresh: print(f"  NEW      {r['views']:>9,}  {r['date']}  {r['title']}")
    for r in new_out: print(f"  OUTLIER  {r['views']:>9,}  {r['date']}  {r['title']}")


def selftest():
    rows = [{"id": str(i), "views": v, "dur": 600, "date": "20261001", "title": ""} for i, v in enumerate([10, 20, 30, 100])]
    o, med = outliers(rows, "2026-10-11"); assert med == 25 and [r["id"] for r in o] == ["3"], (o, med)
    m = merge([{"id": "a", "first_seen": "2026-10-01"}], [{"id": "a", "views": 5}, {"id": "b", "views": 1}], "2026-10-11")
    assert [r["first_seen"] for r in m] == ["2026-10-01", "2026-10-11"], m
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]: selftest(); sys.exit()
    cp = os.path.join(HERE, "creators.json")
    if not os.path.exists(cp): sys.exit("no creators.json: copy creators.example.json to creators.json and list your channels")
    creators = json.load(open(cp))
    today = datetime.date.today().isoformat()
    for slug in sys.argv[1:] or list(creators):
        pull(slug, creators[slug]["url"], today)
