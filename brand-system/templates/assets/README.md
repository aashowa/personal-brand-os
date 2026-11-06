# Template assets

Not shipped: these are yours. The templates expect:

| File | Used by | What |
|---|---|---|
| `photo.jpg` | `thumbnail.html`, `ig-cover.html` | A photo of you, ideally a frame from the actual video. Portrait, at least 1080 px wide. |
| `x-article-art.png` (optional) | `x-article-cover.html` | 1500x600 art with the left 40% kept empty for the words. Without it the cover is plain paper. |

Render with `node brand-system/templates/render.mjs [thumbnail banner ig-cover x-article-cover]` (default: all); PNGs land in `brand-system/templates/out/`.
