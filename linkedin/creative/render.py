"""Render a post creative: each <section class="slide"> in <dir>/linkedin.html -> <dir>/linkedin-NN.png (1080x1350).

    python3 linkedin/creative/render.py <dir>             # linkedin.html -> linkedin-NN.png
    python3 linkedin/creative/render.py <dir> facebook    # facebook.html -> facebook-NN.png

One slide = a single-image post; several = a carousel (schedule.py sends them as one swipeable PDF).
"""
import pathlib
import sys

from playwright.sync_api import sync_playwright

d = pathlib.Path(sys.argv[1]).resolve()
name = sys.argv[2] if len(sys.argv) > 2 else "linkedin"
for old in d.glob(f"{name}-[0-9][0-9].png"):
    old.unlink()
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome")  # the installed Chrome; no Playwright browser download needed
    pg = b.new_page(viewport={"width": 1080, "height": 1350})
    pg.goto((d / f"{name}.html").as_uri())
    pg.wait_for_load_state("networkidle")
    pg.evaluate("document.fonts.ready")
    slides = pg.query_selector_all("section.slide")
    for i, s in enumerate(slides, 1):
        s.screenshot(path=str(d / f"{name}-{i:02}.png"))
    b.close()
print(f"{d.name}: {len(slides)} slide(s) -> {name}-01..{len(slides):02}.png")
