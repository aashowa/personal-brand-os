"""Render index.template.html + config.json + library.json into index.html; --deploy also ships it to your site.

  python3 site/publish.py            # render + check only
  python3 site/publish.py --deploy   # render + check + vercel deploy --prod

Edit index.template.html, never index.html (it is rebuilt every run). config.json at the repo root gives
creator.name, creator.handle, creator.site_url and the "site" section: description, og_description, photo
(a file in site/ that you supply, default photo.jpg), socials ({"YouTube": url, ...}; the first one is also the
header link) and chips ({tag: [css class, label]}, the label on each kit card; classes: chip, chip a1, chip a2).
No library.json yet: it renders library.example.json so you can look at the page, and refuses to deploy it.
Deploy needs the Vercel CLI, `vercel link` run once in site/, and GHL_API_KEY + GHL_LOCATION_ID (+ optional
LIBRARY_TAG) set in the Vercel project's environment variables for api/subscribe.js.
"""
import html
import json
import pathlib
import re
import subprocess
import sys

SITE = pathlib.Path(__file__).resolve().parent
CONFIG = SITE.parent / "config.json"
START, END = "<!-- library:start -->", "<!-- library:end -->"
LOCKED = 'href="#f" data-href="{}">Email to open ↑</a>'


def config():
    if not CONFIG.exists():
        sys.exit("config.json is missing: copy config.example.json to config.json at the repo root and fill in creator + site")
    cfg = json.loads(CONFIG.read_text())
    c, s = cfg.get("creator") or {}, cfg.get("site") or {}
    for sec, d, k in (("creator", c, "name"), ("creator", c, "handle"), ("creator", c, "site_url"), ("site", s, "description")):
        if not d.get(k):
            sys.exit(f"config.json needs {sec}.{k}")
    return c, s


C, S = config()
CHIP = S.get("chips") or {"general": ["chip", "Free file"]}


def code_html(text):
    out = []
    for i, line in enumerate(text.split("\n")):
        e = html.escape(line)
        if line.startswith("#") or (i == 0 and line.endswith("/")):
            e = f'<span class="k">{e}</span>'
        elif line.startswith("…"):
            e = f'<span class="c">{e}</span>'
        elif line.startswith("> "):
            e = f'<span class="c">&gt;</span>{e[4:]}'
        elif " # " in line:
            a, b = e.split(" # ", 1)
            e = f'{a} <span class="c"># {b}</span>'
        out.append(e)
    return '<div class="code">' + "\n".join(out) + "</div>"


def kit_html(k, i):
    cls, label = CHIP.get(k["tag"]) or sys.exit(f"library tag {k['tag']!r} is not in site.chips in config.json")
    tape = f'<span class="tape" style="--i:{i};--r:{(-3, 3, -2, 4)[i % 4]}deg" aria-hidden="true">Email to open</span><span class="locked-hint"></span>'
    text = (f'<span class="{cls}">{html.escape(label)}</span>\n<h3>{html.escape(k["title"])}</h3>\n<p>{html.escape(k["blurb"])}</p>'
            + (f'\n<p class="meta">{html.escape(k["meta"])}</p>' if k.get("meta") else ""))
    link = f'<a class="go" {LOCKED.format(html.escape(k["link"]))}'
    code = code_html(k["code"]) if k.get("code") else ""
    if k.get("wide"):
        body = f"<div>\n{text}\n{link}\n</div>\n{code}"
    else:
        body = f"{text}\n{code}\n{link}"
    return f'<article class="file{" wide" if k.get("wide") else ""}" data-tab="{html.escape(k["tab"])}">\n{tape}\n{body}\n</article>'


def tools_html(tools, i):
    rows = "\n".join(
        f'<li><div><b>{html.escape(t["name"])}</b><small>{html.escape(t["blurb"])}</small></div>'
        f'<a class="go" {LOCKED.format(html.escape(t["link"]))}</li>' for t in tools)
    return (f'<article class="file full" data-tab="from-the-reels/">\n'
            f'<span class="tape" style="--i:{i};--r:-2deg" aria-hidden="true">Email to open</span><span class="locked-hint"></span>\n'
            f'<span class="chip">Tools I showed you</span>\n<h3>Free repos from my Reels</h3>\n<ol class="tools">\n{rows}\n</ol>\n</article>')


def fill(page):
    """The template's {{placeholders}} from config.json."""
    socials = S.get("socials") or {}
    photo = S.get("photo", "photo.jpg")
    if not (SITE / photo).exists():
        print(f"note: site/{photo} is missing; add your photo there (or set site.photo in config.json)")
    vals = {k: html.escape(v) for k, v in {
        "name": C["name"], "handle": C["handle"].lstrip("@"), "site_url": C["site_url"].rstrip("/"), "photo": photo,
        "description": S["description"], "og_description": S.get("og_description") or S["description"],
        "header_link": next(iter(socials.values()), C["site_url"])}.items()}
    vals["socials"] = "\n".join(f'    <a href="{html.escape(u)}">{html.escape(n)} ↗</a>' for n, u in socials.items())
    page = re.sub(r"\{\{(\w+)\}\}", lambda m: vals[m.group(1)], page)
    return page


def main():
    lib_file = SITE / "library.json"
    if not lib_file.exists():
        if "--deploy" in sys.argv:
            sys.exit("site/library.json is missing: copy library.example.json to library.json and put your files in it")
        lib_file = SITE / "library.example.json"
        print("no site/library.json yet: rendering library.example.json (copy it to library.json and put your files in it)")
    lib = json.loads(lib_file.read_text())
    cards = [kit_html(k, i) for i, k in enumerate(lib["kits"])]
    if lib["tools"]:
        cards.append(tools_html(lib["tools"], len(cards)))
    page = fill((SITE / "index.template.html").read_text())
    a, b = page.index(START) + len(START), page.index(END)
    page = page[:a] + "\n" + "\n\n".join(cards) + "\n" + page[b:]
    (SITE / "index.html").write_text(page)

    # check: every library link made it onto the page, locked behind the email box
    links = [k["link"] for k in lib["kits"]] + [t["link"] for t in lib["tools"]]
    missing = [u for u in links if f'data-href="{html.escape(u)}"' not in page]
    assert not missing, f"links missing from page: {missing}"
    assert page.count('href="#f" data-href=') == len(links)
    print(f"rendered {len(lib['kits'])} kits + {len(lib['tools'])} tools into index.html")

    if "--deploy" in sys.argv:
        r = subprocess.run(["vercel", "deploy", "--prod", "--yes"], cwd=SITE, capture_output=True, text=True)
        url = re.findall(r"https://[\w.-]+\.vercel\.app", r.stdout + r.stderr)
        print("deployed" if r.returncode == 0 else f"deploy FAILED ({r.returncode})", url[-1] if url else "")
        sys.exit(r.returncode)


if __name__ == "__main__":
    main()
