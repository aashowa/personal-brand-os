#!/usr/bin/env python3
"""Daily radar: new software catching on (GitHub, Reddit, Hacker News, Product Hunt, YouTube, X), collected for
your audience. This script only collects; the daily task ranks with RUBRIC.md and writes
research/radar/YYYY-MM-DD.md.

    python3 research/radar/radar.py collect        # -> ~/.agent-reach/radar/YYYY-MM-DD.json, counts per source
    python3 research/radar/radar.py seen URL ...    # remember what a digest showed, so it isn't suggested again
    python3 research/radar/radar.py selftest

Agent Reach routes: GitHub via gh, Reddit via public RSS (no login), Hacker News via hnrss, Product Hunt
via its feed, YouTube via yt-dlp, X via twitter-cli (optional: needs TWITTER_AUTH_TOKEN + TWITTER_CT0; skipped with a note until then).
Subreddits and search queries come from config.json's "radar" section (subreddits, youtube_queries, x_queries); defaults below.
"""
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import feedparser

HERE = Path(__file__).resolve().parent
OUT = Path.home() / ".agent-reach" / "radar"
SEEN = HERE / "seen.json"
LIBRARY = HERE.parents[1] / "site" / "library.json"
UA = "Mozilla/5.0 agent-reach/1.0"
CONFIG = HERE.parents[1] / "config.json"
CFG = (json.loads(CONFIG.read_text()) if CONFIG.exists() else {}).get("radar", {})
SUBS = CFG.get("subreddits", {"ai": ["ClaudeAI", "ChatGPT", "OpenAI", "artificial", "ChatGPTPro", "nocode", "automation", "SideProject", "n8n"],
                              "business": ["smallbusiness", "Entrepreneur"]})
YT_QUERIES = CFG.get("youtube_queries", ["claude code", "new ai tool", "ai agent for small business"])
X_QUERIES = CFG.get("x_queries", ["new AI tool", "claude code skill", "open source AI app"])


def fetch(url, tries=3):
    for i in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60).read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:  # Reddit answers 429 after a burst; back off and try again
            if e.code != 429 or i == tries - 1:
                raise
            time.sleep(30 * (i + 1))


def run(*cmd, env=None):
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=180, env=env)
    if out.returncode:
        raise RuntimeError((out.stderr or out.stdout).strip()[-300:])
    return out.stdout


def item(source, title, url, text="", signal="", rank=None):
    return {"source": source, "title": title.strip(), "url": url.strip(), "text": re.sub(r"\s+", " ", text or "").strip()[:400],
            "signal": signal, "rank": rank}


def parse_trending(md):
    """GitHub Trending page as read by Jina: '## [owner / repo](url)', then the description, then '<lang>[stars](...)'."""
    out = []
    for i, m in enumerate(re.finditer(r"^## \[([^\]]+)\]\((https://github\.com/[^)]+)\)\n\n(.*?)\n\n(.*?)\n", md, re.M | re.S)):
        stars = re.search(r"\[([\d,]+)\]\([^)]*/stargazers\)", m.group(4))
        nxt = md.find("\n## [", m.start(4))
        today = re.search(r"([\d,]+) stars today", md[m.start(4):nxt if nxt > 0 else None])  # within this repo's block
        out.append(item("github-trending", m.group(1).replace(" ", ""), m.group(2), m.group(3),
                        f"{stars.group(1) if stars else '?'} stars" + (f", {today.group(1)} today" if today else ""), i + 1))
    return out


def gh_trending():
    return parse_trending(fetch("https://r.jina.ai/https://github.com/trending?since=daily"))


def gh_new(days=7):
    since = (date.today() - timedelta(days=days)).isoformat()
    rows = json.loads(run("gh", "search", "repos", f"created:>{since} stars:>150", "--sort", "stars", "--limit", "30",
                          "--json", "fullName,description,stargazersCount,url"))
    return [item("github-new", r["fullName"], r["url"], r.get("description") or "", f"{r['stargazersCount']} stars in {days} days", i + 1)
            for i, r in enumerate(rows)]


def feed(source, url, limit=15):
    f = feedparser.parse(fetch(url))
    return [item(source, e.get("title", ""), e.get("link", ""), re.sub("<[^>]+>", " ", e.get("summary", "")), "", i + 1)
            for i, e in enumerate(f.entries[:limit])]


def reddit():
    out = []
    for group, subs in SUBS.items():  # one combined feed per group: Reddit answers 429 to a request per subreddit
        out += feed(f"reddit:{group}", f"https://www.reddit.com/r/{'+'.join(subs)}/top/.rss?t=day&limit=40", 40)
    return out  # RSS has no vote counts, so rank is the order Reddit gives


def youtube():
    out = []
    for q in YT_QUERIES:
        url = "https://www.youtube.com/results?sp=CAISAggD&search_query=" + urllib.parse.quote_plus(q)  # this week, newest first
        d = json.loads(run("yt-dlp", url, "--flat-playlist", "--playlist-end", "12", "-J", "--no-warnings"))
        out += [item(f"youtube:{q}", e.get("title") or "", e.get("url") or f"https://youtu.be/{e.get('id')}", e.get("channel") or "",
                     f"{e.get('view_count') or 0} views", i + 1) for i, e in enumerate(d.get("entries") or [])]
    return out


def x_env():
    """X login for twitter-cli (optional): TWITTER_AUTH_TOKEN + TWITTER_CT0 from the environment, else the repo .env.
    Unattended runs can't read Chrome's cookies, so the tool needs these two."""
    import os
    keys = {k: os.environ[k] for k in ("TWITTER_AUTH_TOKEN", "TWITTER_CT0") if os.environ.get(k)}
    env_file = HERE.parents[1] / ".env"
    for line in (env_file.read_text().splitlines() if env_file.exists() else []):
        k, _, v = line.partition("=")
        if k.strip() in ("TWITTER_AUTH_TOKEN", "TWITTER_CT0"):
            keys.setdefault(k.strip(), v.strip().strip("'\""))
    if len(keys) < 2:
        raise RuntimeError("not connected: set TWITTER_AUTH_TOKEN and TWITTER_CT0 in .env (optional; X is skipped without them)")
    return os.environ | keys


def tweets(source, raw):
    rows = json.loads(raw)
    rows = rows.get("data", rows) if isinstance(rows, dict) else rows
    out = []
    for i, t in enumerate(rows or []):
        url = t.get("url") or f"https://x.com/i/status/{t.get('id')}"
        likes = t.get("likes") or t.get("favorite_count") or (t.get("metrics") or {}).get("likes") or 0
        out.append(item(source, (t.get("text") or "")[:120], url, t.get("text") or "", f"{likes} likes", i + 1))
    return out


def x():
    env, out = x_env(), []
    try:
        for q in X_QUERIES:
            out += tweets(f"x:{q}", run("twitter", "search", q, "-n", "15", "--json", env=env))
    except RuntimeError:  # X keeps moving its search endpoint (404 on some twitter-cli versions); the home feed is stable
        out = tweets("x:feed", run("twitter", "feed", "-n", "40", "--json", env=env))
    return out


SOURCES = {"github-trending": gh_trending, "github-new": gh_new, "reddit": reddit,
           "hackernews": lambda: feed("hackernews", "https://hnrss.org/best", 30) + feed("hackernews-show", "https://hnrss.org/show?points=50", 15),
           "producthunt": lambda: feed("producthunt", "https://www.producthunt.com/feed", 30),
           "youtube": youtube, "x": x}


def load(p, default):
    return json.loads(p.read_text()) if p.exists() else default


def covered():
    """Links already given away on your free-files site (site/library.json, optional), so the radar doesn't suggest them again."""
    lib = load(LIBRARY, {})
    return {(t.get("url") or t.get("link") or "").rstrip("/").lower() for k in ("tools", "kits") for t in lib.get(k, [])} - {""}


def mark(items, seen, done):
    for it in items:
        u = it["url"].rstrip("/").lower()
        it["seen_before"] = u in seen
        it["already_covered"] = u in done
    return items


def cmd_collect():
    seen, done, items, notes = set(load(SEEN, [])), covered(), [], {}
    for name, fn in SOURCES.items():
        try:
            got = fn()
            items += got
            notes[name] = len(got)
        except Exception as e:  # one source down shouldn't stop the day
            notes[name] = f"failed: {str(e)[:160]}"
    uniq = list({it["url"].rstrip("/").lower(): it for it in items if it["url"]}.values())
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{date.today().isoformat()}.json"
    path.write_text(json.dumps({"date": date.today().isoformat(), "sources": notes, "items": mark(uniq, seen, done)}, indent=1))
    for k, v in notes.items():
        print(f"{k:16} {v}")
    print(f"{len(uniq)} unique items, {sum(i['seen_before'] for i in uniq)} seen before, {sum(i['already_covered'] for i in uniq)} already covered -> {path}")


def cmd_seen(urls):
    seen = load(SEEN, [])
    seen += [u.rstrip("/").lower() for u in urls if u.rstrip("/").lower() not in seen]
    SEEN.write_text(json.dumps(seen, indent=1))
    print(f"{len(seen)} urls remembered")


def selftest():
    md = ("## [morluto / rea](https://github.com/morluto/rea)\n\nReverse engineer anything with agents.\n\n"
          "TypeScript[152,219](https://github.com/morluto/rea/stargazers)[35,109](https://github.com/morluto/rea/forks) Built by x 1,204 stars today\n")
    t = parse_trending(md)
    assert t == [item("github-trending", "morluto/rea", "https://github.com/morluto/rea", "Reverse engineer anything with agents.",
                      "152,219 stars, 1,204 today", 1)], t
    m = mark([item("x", "a", "https://github.com/morluto/rea/"), item("x", "b", "https://b.com")], {"https://b.com"}, {"https://github.com/morluto/rea"})
    assert m[0]["already_covered"] and not m[0]["seen_before"] and m[1]["seen_before"] and not m[1]["already_covered"]
    print("selftest ok")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["collect"]:
        cmd_collect()
    elif a[:1] == ["seen"]:
        cmd_seen(a[1:])
    elif a[:1] == ["selftest"]:
        selftest()
    else:
        sys.exit(__doc__)
