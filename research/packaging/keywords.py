#!/usr/bin/env python3
"""Which phrases do people search on YouTube, and can a small channel rank for them? Run before writing titles.

usage: keywords.py "phrase" ["phrase" ...]   autocomplete + search check for each phrase
       keywords.py --selftest
Per phrase: YouTube autocomplete (free; a phrase that suggests itself back is a real search), then the top 10 search
results (YouTube Data API; search.list allows about 100 calls a day, so about 100 phrases): median views, how many are under 180 days
old, and how many came from channels under 100k subscribers yet out-viewed their own subscriber count and 5k views
("small wins").
Small wins are the opening: YouTube already ranks small channels for that phrase. Loop: run broad seeds, pick the
suggestions that fit the episode, run those, and put the best "target" phrase at the front of the title.
Needs YOUTUBE_API_KEY in the repo .env (read through system/youtube_upload.py).
"""
import datetime, importlib.util, json, statistics, sys, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]                # repo root


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return json.loads(urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace"))


def suggest(q):
    return get("https://suggestqueries.google.com/complete/search?" +
               urllib.parse.urlencode({"client": "firefox", "ds": "yt", "q": q, "hl": "en", "gl": "us"}))[1]


def api(key, path, **p):
    return get(f"https://www.googleapis.com/youtube/v3/{path}?" + urllib.parse.urlencode(dict(p, key=key)))["items"]


def top10(key, q):
    """[{title, views, subs, age_days}] for the top 10 search results."""
    ids = [i["id"]["videoId"] for i in api(key, "search", part="id", q=q, type="video", maxResults=10,
                                           regionCode="US", relevanceLanguage="en")]
    if not ids: return []
    vids = api(key, "videos", part="statistics,snippet", id=",".join(ids))
    subs = {c["id"]: int(c["statistics"].get("subscriberCount", 0)) for c in
            api(key, "channels", part="statistics", id=",".join({v["snippet"]["channelId"] for v in vids}))}
    now = datetime.datetime.now(datetime.timezone.utc)
    return [{"title": v["snippet"]["title"], "views": int(v["statistics"].get("viewCount", 0)),
             "subs": subs.get(v["snippet"]["channelId"], 0),
             "age_days": (now - datetime.datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))).days}
            for v in vids]


def score(rows, echoed):
    """Verdict for one phrase. ponytail: fixed thresholds from a first calibration run; retune once your own search
    terms (YouTube Analytics) show which phrases actually brought views."""
    med = statistics.median(r["views"] for r in rows) if rows else 0
    small = [r for r in rows if r["subs"] < 100_000 and r["views"] >= max(r["subs"], 5_000)]
    fresh = sum(r["age_days"] < 180 for r in rows)
    if not echoed or med < 5_000: verdict = "low demand"
    elif not small: verdict = "crowded"
    else: verdict = "target"
    best = max(small, key=lambda r: r["views"], default=None)
    return {"median": med, "small": len(small), "fresh": fresh, "verdict": verdict, "best": best}


def selftest():
    r = lambda v, s, a=30: {"title": "t", "views": v, "subs": s, "age_days": a}
    s = score([r(84_000, 3_900), r(30_000, 500_000), r(20_000, 90_000, 400)], echoed=True)
    assert (s["verdict"], s["small"], s["fresh"], s["median"]) == ("target", 1, 2, 30_000), s
    assert score([r(30_000, 500_000)], echoed=True)["verdict"] == "crowded"
    assert score([r(84_000, 3_900)], echoed=False)["verdict"] == "low demand"
    assert score([r(1_700, 1_200), r(30_000, 500_000)], echoed=True)["verdict"] == "crowded"  # tiny wins don't count
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] in ([], ["--selftest"]):
        selftest() if sys.argv[1:] else print(__doc__); sys.exit()
    spec = importlib.util.spec_from_file_location("yu", ROOT / "system/youtube_upload.py")
    yu = importlib.util.module_from_spec(spec); spec.loader.exec_module(yu)
    key = yu.env_value("YOUTUBE_API_KEY")
    print("| Phrase | Verdict | Median views (top 10) | Small wins | Fresh (<180 d) | Best small-channel result |\n|---|---|---|---|---|---|")
    sugg = {}
    for q in sys.argv[1:]:
        sugg[q] = suggest(q)
        s = score(top10(key, q), echoed=q.lower() in (x.lower() for x in sugg[q]))
        b = s["best"]
        best = f'"{b["title"]}" ({b["views"]:,} views, {b["subs"]:,} subs)' if b else ""
        print(f'| {q} | {s["verdict"]} | {s["median"]:,.0f} | {s["small"]} | {s["fresh"]} | {best} |')
    print("\nAutocomplete (candidates for the next run):")
    for q, xs in sugg.items(): print(f"- {q}: " + ", ".join(x for x in xs if x.lower() != q.lower()))
