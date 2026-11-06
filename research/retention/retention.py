#!/usr/bin/env python3
"""Where people stop watching your Reels, second by second, and what was on screen and said at that second.

usage: retention.py [pull|report]      (no argument = both)
  pull    YouTube Analytics retention curve (audienceWatchRatio, 100 points) + stats for every published Short and episode
          in the schedule ledger, and Instagram's views / average watch time for the matching Reel -> data/<date>.json
  report  the latest data/*.json lined up with each Reel's transcript (project/assets/words.json) and layout timeline
          (project/index.html: face / split / full) -> REPORT.md, plus the cross-Reel patterns that feed the script rules

The loop: run it every week (Friday), read REPORT.md's patterns, update the rules in RULES.md (keep what holds, fix what
loses people), and check the next script against them.
TikTok gives no per-post retention through GHL and Facebook is left out, so neither is in it yet.
"""
import glob, importlib.util, json, os, re, statistics as st, sys
from datetime import date, datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
PB = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(HERE, "data")


def sched():
    spec = importlib.util.spec_from_file_location("sched", os.path.join(PB, "system", "schedule.py"))
    m = importlib.util.module_from_spec(spec); argv, sys.argv = sys.argv, ["x"]; spec.loader.exec_module(m); sys.argv = argv
    m.load_env()                                   # the repo .env (META_ACCESS_TOKEN etc.), as schedule.py's own commands do
    return m


# ------------------------------------------------------------------------------------------------ pull
def pull():
    from googleapiclient.discovery import build
    m = sched(); yu = m.youtube_upload(); creds = yu.saved_creds()
    yt, ya = yu.youtube(creds), build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
    rows = [r for r in m.ledger() if r.get("status") == "published" and r.get("youtube") and r["kind"] in ("reel", "episode")]
    ids = [r["youtube"] for r in rows]
    meta = {}
    for i in range(0, len(ids), 50):
        for v in yt.videos().list(part="contentDetails,statistics", id=",".join(ids[i:i + 50])).execute()["items"]:
            meta[v["id"]] = {"duration": iso_s(v["contentDetails"]["duration"]), "views_total": int(v["statistics"].get("viewCount", 0))}
    today = date.today().isoformat()
    q = dict(ids="channel==MINE", startDate="2026-01-01", endDate=today)
    stats = {r[0]: r[1:] for r in (ya.reports().query(**q, dimensions="video", filters="video==" + ",".join(ids),
             metrics="views,engagedViews,averageViewPercentage,averageViewDuration,shares,subscribersGained").execute().get("rows") or [])}
    out = []
    for r in rows:
        vid = r["youtube"]
        curve = ya.reports().query(**q, dimensions="elapsedVideoTimeRatio", metrics="audienceWatchRatio,relativeRetentionPerformance",
                                   filters=f"video=={vid}").execute().get("rows") or []
        s = stats.get(vid, [0, 0, None, None, 0, 0])
        out.append({"kind": r["kind"], "folder": os.path.basename(r["folder"]), "slot": r["slot"], "title": r.get("title"), "youtube": vid,
                    **meta.get(vid, {}), "yt": dict(zip(["views", "engaged", "avg_pct", "avg_s", "shares", "subs"], s)),
                    "curve": [[a, b, c] for a, b, c in curve]})
    try:  # Instagram: the Reel posted at the same slot (GHL posts all platforms at once)
        ig = m.ig_me(); media, url = [], f"/{ig}/media"
        params = {"fields": "id,timestamp,caption,media_product_type,permalink", "limit": 100}
        while url and len(media) < 300:
            page = m.graph("GET", url, params=params); media += page.get("data", [])
            nxt = (page.get("paging") or {}).get("next"); url = nxt.split("v23.0")[1].split("?")[0] if nxt else None
            params = {**params, "after": (page.get("paging") or {}).get("cursors", {}).get("after")}
        for o in out:
            t0 = datetime.fromisoformat(o["slot"]).astimezone(timezone.utc)
            near = [x for x in media if abs((datetime.strptime(x["timestamp"], "%Y-%m-%dT%H:%M:%S%z") - t0).total_seconds()) < 3 * 3600]
            if near and o["kind"] == "reel":
                o["ig"] = {"id": near[0]["id"], "permalink": near[0].get("permalink"), **m.ig_insights(near[0]["id"])}
    except SystemExit as e:
        print("instagram skipped:", e)
    os.makedirs(DATA, exist_ok=True)
    p = os.path.join(DATA, f"{today}.json"); json.dump(out, open(p, "w"), indent=1)
    print(f"pull ok {p}: {len(out)} videos, {sum(1 for o in out if o.get('ig'))} with Instagram")


def iso_s(d):
    h, mi, s = (int(x or 0) for x in re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", d).groups())
    return h * 3600 + mi * 60 + s


# ------------------------------------------------------------------------------------------------ report
def timeline(folder):
    """(words [(start, end, text)], layout function t -> face|split|full) from the Reel's final build."""
    d = os.path.join(PB, "episodes", folder, "project", "assets", "words.json")
    words = [tuple(w) for w in json.load(open(d))["words"]] if os.path.exists(d) else []
    html = os.path.join(PB, "episodes", folder, "project", "index.html")
    spans = []
    if os.path.exists(html):
        h = open(html).read()
        for m in re.finditer(r'<(section|video) id="(\w+)" class="clip (beat full|beat|face)"[^>]*?data-start="([\d.]+)" data-duration="([\d.]+)"', h):
            kind = "face" if "face" in m.group(3) else "full" if "full" in m.group(3) else None
            if kind: spans.append((float(m.group(4)), float(m.group(4)) + float(m.group(5)), kind))
    lay = lambda t: next((k for a, b, k in sorted(spans, key=lambda x: x[2] != "face") if a <= t < b), "split")
    return words, lay, bool(spans)


def said(words, a, b):
    return " ".join(w[2] for w in words if a - 0.05 <= w[0] < b) or "(no words)"


def report():
    p = sorted(glob.glob(os.path.join(DATA, "*.json")))[-1]; vids = json.load(open(p))
    reels = [v for v in vids if v["kind"] == "reel" and v.get("curve") and v.get("duration")]
    lines = [f"# Where people stop watching ({os.path.basename(p)[:-5]})", "",
             "Generated by `retention.py report`. Curves: YouTube Shorts audience retention (100 points; normalised to the first point, "
             "so replays don't count as more than 100%). Stayed = YouTube engaged views / views (didn't swipe away). IG avg = Instagram's "
             "average watch seconds. Layout at each second comes from the Reel's final build.", "",
             "| Reel | s | YT views | Stayed | Avg % | at 3 s | at 10 s | half gone at | IG views | IG avg s (%) |", "|---|---|---|---|---|---|---|---|---|---|"]
    per_layout, trans, other, drops_all, rows = {"face": [], "split": [], "full": []}, [], [], [], []
    for v in sorted(reels, key=lambda v: -(v["yt"]["views"] or 0)):
        D = v["duration"]; c = v["curve"]; base = c[0][1] or 1
        pts = [(x * D, y / base) for x, y, _ in c]
        at = lambda s: next((y for x, y in pts if x >= s), pts[-1][1])
        half = next((x for x, y in pts if y < 0.5), None)
        yt, ig = v["yt"], v.get("ig") or {}
        stayed = f"{yt['engaged'] / yt['views']:.0%}" if yt.get("views") else "-"
        igs = f"{ig['ig_reels_avg_watch_time'] / 1000:.1f} ({ig['ig_reels_avg_watch_time'] / 10 / D:.0f}%)" if ig.get("ig_reels_avg_watch_time") else "-"
        lines.append(f"| {v['folder']} | {D} | {yt.get('views') or 0} | {stayed} | {yt.get('avg_pct') or 0:.0f} | {at(3):.0%} | {at(10):.0%} | "
                     f"{f'{half:.0f} s' if half else 'never'} | {ig.get('views', '-')} | {igs} |")
        words, lay, has = timeline(v["folder"])
        if not has or (yt.get("views") or 0) < 100: continue          # no build to line up with, or too few views to trust the curve
        loss = [((pts[i - 1][0] + pts[i][0]) / 2, (pts[i - 1][1] - pts[i][1]) / max(pts[i][0] - pts[i - 1][0], 1e-6)) for i in range(1, len(pts))]
        for t, l in loss:
            if t < 1.5: continue                                       # the swipe-away is the hook's number (Stayed), not a beat's
            per_layout[lay(t)].append(l)
            (trans if any(lay(t - d) != lay(t + d) for d in (0.5,)) else other).append(l)
        top = sorted((x for x in loss if x[0] >= 1.5), key=lambda x: -x[1])[:3]
        rows.append((v["folder"], [(t, l, lay(t), said(words, t - 1.2, t + 0.3)) for t, l in sorted(top)]))
        drops_all += [(v["folder"], t, l, lay(t), said(words, t - 1.2, t + 0.3)) for t, l in top]
    lines += ["", "## Biggest drops after the first 1.5 s (loss per second, what was said, what was on screen)", ""]
    for f, ds in rows:
        lines.append(f"- **{f}**: " + "; ".join(f"{t:.1f} s {l:.0%}/s [{k}] \"{w}\"" for t, l, k, w in ds))
    mean = lambda xs: st.mean(xs) if xs else 0
    lines += ["", "## Patterns", "",
              f"- Loss per second by layout (after 1.5 s): face {mean(per_layout['face']):.1%}/s, split {mean(per_layout['split']):.1%}/s, "
              f"full graphics {mean(per_layout['full']):.1%}/s (n = {len(per_layout['face'])}/{len(per_layout['split'])}/{len(per_layout['full'])} points).",
              f"- At a layout change (within 0.5 s): {mean(trans):.1%}/s vs {mean(other):.1%}/s elsewhere.",
              f"- Hook: median retention at 3 s {st.median([next((y / (v['curve'][0][1] or 1) for x, y, _ in v['curve'] if x * v['duration'] >= 3), 0) for v in reels]):.0%}, "
              f"median Stayed {st.median([v['yt']['engaged'] / v['yt']['views'] for v in reels if v['yt'].get('views')]):.0%}.",
              f"- Instagram: median average watch {st.median([v['ig']['ig_reels_avg_watch_time'] / 1000 for v in reels if (v.get('ig') or {}).get('ig_reels_avg_watch_time')] or [0]):.1f} s."]
    eps = [v for v in vids if v["kind"] == "episode" and v.get("curve")]
    if eps:
        lines += ["", "## Episodes", "", "| Episode | length | views | avg % | at 0:30 | at 1:00 |", "|---|---|---|---|---|---|"]
        for v in eps:
            D = v["duration"]; base = v["curve"][0][1] or 1
            at = lambda s: next((y / base for x, y, _ in v["curve"] if x * D >= s), 0)
            lines.append(f"| {v['folder']} | {D // 60}:{D % 60:02d} | {v['yt'].get('views')} | {v['yt'].get('avg_pct') or 0:.1f} | {at(30):.0%} | {at(60):.0%} |")
    open(os.path.join(HERE, "REPORT.md"), "w").write("\n".join(lines) + "\n")
    json.dump(drops_all, open(os.path.join(DATA, "drops-latest.json"), "w"), indent=1)
    print("report ok", os.path.join(HERE, "REPORT.md"))


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "all"
    if a in ("pull", "all"): pull()
    if a in ("report", "all"): report()
