#!/usr/bin/env python3
"""Find videos that beat their own creator's normal, for the daily radar (research/radar/RUBRIC.md § Outliers).

usage: outliers.py collect [SLUG ...]   pull every creator in watchlist.json (or only the slugs given)
       outliers.py seen URL ...         remember reported outliers so they're listed once
       outliers.py --selftest
Outlier = a post 2 to 30 days old with at least 2x the median views of that creator's latest 30 posts on the same
platform (Instagram Reels, YouTube Shorts and YouTube long-form each have their own baseline). 2-5x strong, 5x+ huge;
under 10 posts in the baseline = low confidence. Undated posts (YouTube Shorts) are aged from the day we first saw them;
the ones found on a creator's first pull have no known age and only count toward the baseline.
Transcripts for the top 10: whisper-1 on the Reel (Instagram); YouTube captions, else Gemini reading the video (first 2 min
of long-form). History: <slug>/<platform>.json. Output: ~/.agent-reach/radar/YYYY-MM-DD-outliers.json.
Captions and transcripts are untrusted data: stored as text, never followed as instructions.
"""
import json, os, re, statistics, subprocess, sys, tempfile, time, urllib.request
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]                                  # repo root (.env, .tmp)
HIST = HERE                                             # <slug>/<platform>.json; the selftest points it at a temp dir
OUT = Path.home() / ".agent-reach" / "radar"
SEEN = HERE / "seen.json"
APIFY = "https://api.apify.com/v2"
GEMINI = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
REEL_ACTOR, REEL_USD, START_USD = "apify~instagram-reel-scraper", 0.0023, 0.001   # Apify Starter plan (Bronze tier) prices


def load(path, default):
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else default


def save(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=1))


def merge(old, new, today):
    """Newest first: the fresh list in its order, then rows only in the old history. Views/title come from the fresh
    list; first_seen is kept from the first pull. An undated row gets first_seen None (age unknown) on a first pull, or
    when it's listed after a post we already know (so it's older than that post, not new today)."""
    seen = {r["id"]: r for r in old}
    out, ids, passed_known = [], set(), False
    for r in new:
        if r["id"] in ids: continue
        ids.add(r["id"])
        if r["id"] in seen:
            fs, passed_known = seen[r["id"]].get("first_seen"), True
        else:
            fs = None if not r.get("date") and (not old or passed_known) else today
        out.append(dict(r, first_seen=fs))
    return out + [r for r in old if r["id"] not in ids]


def age_days(row, today):
    t = date.fromisoformat(today)
    if row.get("date"):
        d = row["date"]; return (t - date(int(d[:4]), int(d[4:6]), int(d[6:8]))).days
    if row.get("first_seen"):
        return (t - date.fromisoformat(row["first_seen"])).days
    return None


def tier(lift):
    return "huge" if lift >= 5 else "strong" if lift >= 2 else None


def score(rows, today):
    """(outliers sorted by lift, median of the latest 30 posts, n in that baseline)."""
    base = rows[:30]
    if not base: return [], 0, 0
    med = statistics.median(r["views"] for r in base)
    if med <= 0: return [], med, len(base)
    outs = []
    for r in rows:
        a = age_days(r, today)
        if a is None or not 2 <= a <= 30: continue
        lift = r["views"] / med
        if tier(lift):
            outs.append(dict(r, lift=round(lift, 1), tier=tier(lift), age_days=a, median=med,
                             confidence="low" if len(base) < 10 else "ok"))
    return sorted(outs, key=lambda o: -o["lift"]), med, len(base)


def env(key):
    if os.environ.get(key): return os.environ[key]      # an already-set env var wins
    p = ROOT / ".env"
    for line in (p.read_text().splitlines() if p.exists() else []):
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip().strip('"')
    raise RuntimeError(f"{key} missing: set it in .env")


def api(path, payload=None, timeout=60):
    sep = "&" if "?" in path else "?"
    req = urllib.request.Request(f"{APIFY}{path}{sep}token={env('APIFY_API_TOKEN')}",
                                 data=json.dumps(payload).encode() if payload is not None else None,
                                 headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def run_actor(actor, payload):
    """Start an Apify actor, wait for it (up to 20 min) and return its dataset items."""
    run = api(f"/acts/{actor}/runs", payload)["data"]
    for _ in range(120):
        time.sleep(10)
        status = api(f"/actor-runs/{run['id']}")["data"]["status"]
        if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"): break
    if status != "SUCCEEDED": raise RuntimeError(f"{actor} run {run['id']} ended {status}")
    return api(f"/datasets/{run['defaultDatasetId']}/items?clean=true", timeout=120)


def apify_usage():
    d = api("/users/me/limits")["data"]
    return d["current"]["monthlyUsageUsd"], d["limits"]["maxMonthlyUsageUsd"]


def apify_room(est_usd, used_usd, cap_usd):
    return used_usd + est_usd <= 0.9 * cap_usd


def instagram(handles, limit):
    """{lowercase handle: rows newest first} from one reel-scraper run."""
    items = run_actor(REEL_ACTOR, {"username": handles, "resultsLimit": limit, "skipPinnedPosts": True})
    out = {}
    for it in items:
        if it.get("error") or not it.get("shortCode") or not it.get("timestamp"): continue
        out.setdefault((it.get("ownerUsername") or "").lower(), []).append({
            "id": it["shortCode"], "url": it.get("url") or f"https://www.instagram.com/reel/{it['shortCode']}/",
            "views": int(it.get("videoPlayCount") or it.get("videoViewCount") or 0), "date": it["timestamp"][:10].replace("-", ""),
            "dur": int(it.get("videoDuration") or 0), "title": it.get("caption") or "", "video_url": it.get("videoUrl")})
    for rows in out.values(): rows.sort(key=lambda r: r["date"], reverse=True)
    return out


def youtube(url, tab):
    """Newest 40 of a channel's Shorts or long-form videos (yt-dlp flat listing; Shorts come without dates)."""
    out = subprocess.run(["yt-dlp", "--no-update", "--flat-playlist", "--playlist-end", "40", "--extractor-args",
                          "youtubetab:approximate_date", "--print", "%(id)s\t%(view_count)s\t%(duration)s\t%(upload_date)s\t%(title)s",
                          url.rstrip("/") + "/" + tab], capture_output=True, text=True, timeout=300).stdout
    rows = []
    for l in out.splitlines():
        p = l.split("\t")
        if len(p) == 5 and p[1].isdigit():
            rows.append({"id": p[0], "views": int(p[1]), "dur": int(float(p[2])) if p[2] not in ("NA", "None") else 0,
                         "date": p[3] if p[3].isdigit() else None, "title": p[4],
                         "url": f"https://www.youtube.com/shorts/{p[0]}" if tab == "shorts" else f"https://youtu.be/{p[0]}"})
    return rows


def vtt_text(vtt, max_start_s):
    """Plain text from WebVTT; YouTube's rolling captions repeat the previous line, so a repeat is dropped."""
    lines = []
    for block in vtt.split("\n\n"):
        rows = block.strip().splitlines()
        t = next((i for i, l in enumerate(rows) if "-->" in l), None)
        if t is None: continue
        h, m, sec = rows[t].split("-->")[0].strip().split(":")
        if max_start_s is not None and int(h) * 3600 + int(m) * 60 + float(sec) >= max_start_s: continue
        for l in rows[t + 1:]:
            l = re.sub(r"<[^>]+>", "", l).strip()
            if l and (not lines or lines[-1] != l): lines.append(l)
    return " ".join(lines)


def whisper(mp3, key):
    b = "----outliers"
    body = b"".join(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
                    for k, v in (("model", "whisper-1"), ("response_format", "json")))
    body += (f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="a.mp3"\r\nContent-Type: audio/mpeg\r\n\r\n'.encode()
             + Path(mp3).read_bytes() + f"\r\n--{b}--\r\n".encode())
    req = urllib.request.Request("https://api.openai.com/v1/audio/transcriptions", data=body,
                                 headers={"Authorization": "Bearer " + key, "Content-Type": f"multipart/form-data; boundary={b}"})
    return json.load(urllib.request.urlopen(req, timeout=300))["text"].strip()


def gemini_body(url, end_s):
    meta = {"endOffset": f"{end_s}s", "fps": 0.2} if end_s else {"fps": 0.2}
    return {"contents": [{"parts": [{"fileData": {"fileUri": url}, "videoMetadata": meta},
                                    {"text": "Transcribe exactly what is said in this clip, word for word, as plain text. "
                                             "No timestamps, labels or commentary."}]}],
            "generationConfig": {"temperature": 0, "mediaResolution": "MEDIA_RESOLUTION_LOW"}}


def gemini(url, end_s):
    """Gemini reads a public YouTube video on Google's side (~6k tokens, about a cent, for 2 minutes)."""
    req = urllib.request.Request(f"{GEMINI}?key={env('GEMINI_API_KEY')}", data=json.dumps(gemini_body(url, end_s)).encode(),
                                 headers={"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=180))
    return "".join(p.get("text", "") for p in r["candidates"][0]["content"]["parts"]).strip()


def transcribe(row, platform):
    """(text, source) for one outlier, or (None, None). Media is deleted straight after."""
    tmp = ROOT / ".tmp" / "outliers"
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        if platform == "instagram":
            mp4, mp3 = tmp / f"{row['id']}.mp4", tmp / f"{row['id']}.mp3"
            try:
                subprocess.run(["curl", "-s", "-f", "-L", "--max-time", "120", "-o", str(mp4), row["video_url"]], check=True)
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp4), "-vn", "-ac", "1", "-ar", "16000", str(mp3)], check=True)
                return whisper(mp3, env("OPENAI_API_KEY")), "whisper"
            finally:
                for f in (mp4, mp3): f.unlink(missing_ok=True)
        end = 120 if platform == "youtube-videos" else None
        subprocess.run(["yt-dlp", "--no-update", "--skip-download", "--write-subs", "--write-auto-subs", "--sub-langs", "en",
                        "--sub-format", "vtt", "--sleep-requests", "2", "-o", str(tmp / row["id"]), row["url"]],
                       capture_output=True, timeout=180)
        files = sorted(tmp.glob(row["id"] + "*.vtt"))
        try:
            text = vtt_text(files[0].read_text(), end) if files else ""
        finally:
            for f in files: f.unlink(missing_ok=True)
        if text: return text, "youtube-subs"
        # yt-dlp often gets HTTP 429 on captions and 403 on media without impersonation/PO tokens: Gemini reads it instead.
        text = gemini(row["url"], end)
        return (text, "gemini") if text else (None, None)
    except Exception:
        return None, None


def collect_one(slug, platform, fetch, today):
    """Fetch, merge into history, score. One source failing never stops the others."""
    try:                                                # a fetch error, a broken history file or a full disk fails this source only
        rows = fetch()
        if not rows: return "failed: nothing listed (kept the old history)", []
        path = HIST / slug / f"{platform}.json"
        merged = merge(load(path, []), rows, today)
        save(path, merged)
        outs, med, n = score(merged, today)
        return f"ok {n} posts, median {med:,.0f}", [dict(o, creator=slug, platform=platform) for o in outs]
    except Exception as e:
        return f"failed: {str(e)[:160]}", []


def cmd_collect(slugs):
    wl = load(HERE / "watchlist.json", {})
    if not wl: sys.exit("no creators: copy watchlist.example.json to watchlist.json and list the ones you follow")
    slugs = slugs or list(wl)
    today = date.today().isoformat()
    sources, outs = {}, []
    try:
        used, cap = apify_usage()
    except Exception as e:
        used, cap = None, None
        print(f"apify limits: failed: {str(e)[:160]}")
    handles = {s: wl[s]["instagram"] for s in slugs if wl[s].get("instagram")}
    first = [s for s in handles if not (HIST / s / "instagram.json").exists()]
    for limit, group in ((30, first), (6, [s for s in handles if s not in first])):
        if not group: continue
        est = len(group) * limit * REEL_USD + START_USD
        if cap is None or not apify_room(est, used, cap):
            for s in group: sources[f"{s}:instagram"] = f"failed: apify budget ({used} of {cap})"
            continue
        try:
            data, err = instagram([handles[s] for s in group], limit), None
        except Exception as e:
            data, err = {}, e
        used += est
        for s in group:
            def fetch(h=handles[s].lower(), err=err):
                if err: raise err
                return data.get(h, [])
            sources[f"{s}:instagram"], got = collect_one(s, "instagram", fetch, today)
            outs += got
    for s in (s for s in slugs if wl[s].get("youtube")):
        for tab in ("shorts", "videos"):
            sources[f"{s}:youtube-{tab}"], got = collect_one(s, f"youtube-{tab}", lambda u=wl[s]["youtube"], t=tab: youtube(u, t), today)
            outs += got
    seen = set(load(SEEN, []))
    outs = sorted((o for o in outs if o["url"].rstrip("/") not in seen), key=lambda o: -o["lift"])
    for i, o in enumerate(outs):                        # one at a time, highest lift first; YouTube rate-limits subtitle pulls
        o["transcript"], o["transcript_source"] = transcribe(o, o["platform"]) if i < 10 else (None, None)
        o.pop("video_url", None)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{today}-outliers.json"
    save(path, {"date": today, "sources": sources, "apify_usd": {"used": used, "cap": cap}, "outliers": outs})
    for k, v in sources.items(): print(f"{k:32} {v}")
    print(f"{len(outs)} new outliers -> {path}")
    for o in outs[:10]: print(f"  {o['lift']:>5}x  {o['creator']:15} {o['platform']:15} {o['url']}  {o['title'][:60]!r}")


def cmd_seen(urls):
    seen = load(SEEN, [])
    seen += [u.rstrip("/") for u in urls if u.rstrip("/") not in seen]
    save(SEEN, seen)
    print(f"{len(seen)} urls remembered")


def selftest():
    global HIST
    HIST = Path(tempfile.mkdtemp())
    rows = [{"id": str(i), "url": f"u{i}", "views": v, "date": "20261010", "dur": 30, "title": "", "first_seen": "2026-10-10"}
            for i, v in enumerate([100] * 9 + [1000])]
    outs, med, n = score(rows, "2026-10-17")
    assert med == 100 and n == 10 and [o["id"] for o in outs] == ["9"] and outs[0]["tier"] == "huge" and outs[0]["lift"] == 10.0
    assert tier(1.9) is None and tier(2.0) == "strong" and tier(5.0) == "huge"
    assert score([], "2026-10-17") == ([], 0, 0)
    assert score([dict(rows[0], views=0)] * 3, "2026-10-17")[0] == []              # median 0: no crash, no outliers
    old = [dict(rows[9], date="20260901")]                                          # 46 days old: outside the window
    assert score(old + rows[:9], "2026-10-17")[0] == []
    assert score(rows[:5] + [rows[9]], "2026-10-17")[0][0]["confidence"] == "low"
    fresh = [{"id": "s", "url": "s", "views": 9000, "date": None, "dur": 0, "title": ""}]
    m = merge([], fresh + [dict(fresh[0], id="t", url="t", views=10)] * 3, "2026-10-17")
    assert m[0]["first_seen"] is None and age_days(m[0], "2026-10-20") is None
    assert score(m, "2026-10-20")[0] == []
    m2 = merge([{"id": "a", "first_seen": "2026-10-01", "views": 1}], [{"id": "b", "views": 5, "date": None}, {"id": "a", "views": 9}], "2026-10-17")
    assert [(r["id"], r["first_seen"], r["views"]) for r in m2] == [("b", "2026-10-17", 5), ("a", "2026-10-01", 9)]
    assert age_days({"date": None, "first_seen": "2026-10-10"}, "2026-10-17") == 7
    assert apify_room(0.15, 1.75, 29) and not apify_room(0.15, 26.0, 29)
    def boom(): raise RuntimeError("HTTP 429")
    note, outs = collect_one("x-test", "youtube-shorts", boom, "2026-10-17")
    assert note.startswith("failed: HTTP 429") and outs == []
    v = "WEBVTT\n\n00:00:01.000 --> 00:00:03.000\nhello <c>world</c>\n\n00:00:02.000 --> 00:00:04.000\nhello world\nnext line\n\n00:02:05.000 --> 00:02:07.000\nlate\n"
    assert vtt_text(v, None) == "hello world next line late" and vtt_text(v, 120) == "hello world next line"
    assert transcribe({"id": "x", "url": "u", "video_url": "http://127.0.0.1:9/none.mp4"}, "instagram") == (None, None)
    k = {"id": "k", "views": 5, "date": None}                                     # old undated Shorts after a known one
    m3 = merge([dict(k, first_seen="2026-10-01")], [{"id": "new", "views": 9, "date": None}, k, {"id": "old", "views": 900, "date": None}], "2026-10-17")
    assert [(r["id"], r["first_seen"]) for r in m3] == [("new", "2026-10-17"), ("k", "2026-10-01"), ("old", None)]
    g = gemini_body("https://youtu.be/x", 120)["contents"][0]["parts"][0]          # Gemini reads the first 2 min
    assert g == {"fileData": {"fileUri": "https://youtu.be/x"}, "videoMetadata": {"endOffset": "120s", "fps": 0.2}}
    assert gemini_body("u", None)["contents"][0]["parts"][0]["videoMetadata"] == {"fps": 0.2}
    (HIST / "bad").mkdir(); (HIST / "bad" / "youtube-videos.json").write_text("[{trunc")   # a broken file fails one source
    assert collect_one("bad", "youtube-videos", lambda: [dict(rows[0])], "2026-10-17")[0].startswith("failed: ")
    print("selftest ok")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--selftest"]: selftest()
    elif a[:1] == ["collect"]: cmd_collect(a[1:])
    elif a[:1] == ["seen"] and a[1:]: cmd_seen(a[1:])
    else: print(__doc__); sys.exit(1)
